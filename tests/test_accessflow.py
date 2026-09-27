import asyncio, os, sys
from decimal import Decimal
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app import store
from app.models import IntentRequest, BankingIntent
from app.services.natlas import MockNAtlasProvider
from app.services.banking import create_preview, execute_preview, BankingError

client=TestClient(app)

@pytest.fixture(autouse=True)
def reset(): store.reset_demo(); yield

def parse(text,hint=None): return asyncio.run(MockNAtlasProvider().parse(IntentRequest(text=text,language_hint=hint)))

def test_health():
    r=client.get('/health'); assert r.status_code==200 and r.json()['status']=='ok'

def test_languages_are_complete():
    codes={x['code'] for x in client.get('/api/v1/languages').json()}; assert codes=={'en-NG','yo-NG','ha-NG','ig-NG','pcm-NG'}

def test_pidgin_transfer_parses():
    i=parse('Abeg send 5k give Chinedu'); assert i.action=='transfer_money' and i.language=='pcm-NG' and i.amount==Decimal('5000') and i.beneficiary_query=='chinedu'

def test_yoruba_code_switch_transfer_parses():
    i=parse('Mo fẹ transfer 10k si Adewale'); assert i.language=='yo-NG' and i.code_switched and i.amount==Decimal('10000')

def test_hausa_transfer_parses():
    i=parse('Aika 5k zuwa Amina'); assert i.language=='ha-NG' and i.action=='transfer_money'

def test_igbo_transfer_parses():
    i=parse('Zipu 5k nye Amina'); assert i.language=='ig-NG' and i.action=='transfer_money'

def test_missing_amount_requires_clarification():
    i=parse('Send money to Chinedu'); assert i.clarification and i.confidence<.85

def test_missing_beneficiary_requires_clarification():
    i=parse('Send 5k'); assert i.clarification and i.confidence<.85

def test_unknown_never_becomes_transaction():
    i=parse('Tell me a joke'); assert i.action=='unknown'

def test_preview_masks_account():
    p=create_preview(parse('Send 5k to Chinedu')); assert p.masked_account.endswith('1920') and '004829' not in p.masked_account

def test_low_confidence_transfer_is_blocked():
    i=BankingIntent(intent_id='x',action='transfer_money',language='en-NG',amount=1000,beneficiary_query='chinedu',confidence=.5)
    with pytest.raises(BankingError): create_preview(i)

def test_over_limit_transfer_blocked():
    i=parse('Send 300k to Chinedu')
    with pytest.raises(BankingError): create_preview(i)

def test_insufficient_balance_blocked():
    i=parse('Send 100k to Chinedu')
    with pytest.raises(BankingError): create_preview(i)

def test_confirmation_required():
    p=create_preview(parse('Send 5k to Chinedu'))
    with pytest.raises(BankingError): execute_preview(p.preview_id,False,'1234')

def test_authentication_required():
    p=create_preview(parse('Send 5k to Chinedu'))
    with pytest.raises(BankingError): execute_preview(p.preview_id,True,'0000')

def test_transfer_changes_balance_once():
    p=create_preview(parse('Send 5k to Chinedu')); before=store.ACCOUNT['balance']; out=execute_preview(p.preview_id,True,'1234','same-key'); assert store.ACCOUNT['balance']==before-Decimal('5000'); out2=execute_preview(p.preview_id,True,'1234','same-key'); assert out2['transaction']['transaction_id']==out['transaction']['transaction_id']; assert store.ACCOUNT['balance']==before-Decimal('5000')

def test_preview_cannot_execute_twice_without_idempotency():
    p=create_preview(parse('Send 5k to Chinedu')); execute_preview(p.preview_id,True,'1234')
    with pytest.raises(BankingError): execute_preview(p.preview_id,True,'1234')

def test_assistant_balance_returns_bank_state():
    r=client.post('/api/v1/assistant',json={'text':'Check my balance','language_hint':'en-NG','interaction_mode':'text'}); assert r.status_code==200; assert float(r.json()['data']['balance'])==82400

def test_assistant_transfer_returns_preview_not_execution():
    r=client.post('/api/v1/assistant',json={'text':'Abeg send 5k give Chinedu','language_hint':'pcm-NG','interaction_mode':'text'}); j=r.json(); assert j['type']=='transfer_preview'; assert float(store.ACCOUNT['balance'])==82400

def test_card_freeze_requires_pin():
    r=client.post('/api/v1/card/freeze',json={'confirmed':True,'pin':'0000'}); assert r.status_code==400; assert store.CARD['frozen'] is False

def test_card_freeze_success():
    r=client.post('/api/v1/card/freeze',json={'confirmed':True,'pin':'1234'}); assert r.status_code==200 and r.json()['frozen'] is True

def test_support_case_created():
    r=client.post('/api/v1/assistant',json={'text':'I need customer support','language_hint':'en-NG','interaction_mode':'text'}); assert r.status_code==200 and len(store.SUPPORT_CASES)==1

def test_fraud_case_created():
    r=client.post('/api/v1/assistant',json={'text':'This transaction looks suspicious fraud','language_hint':'en-NG','interaction_mode':'text'}); assert r.status_code==200 and len(store.FRAUD_REPORTS)==1

def test_profile_records_preferences_not_diagnosis():
    payload={'primary_language':'yo-NG','allow_code_switching':True,'voice_guidance':True,'captions':False,'screen_reader':True,'large_text':False,'high_contrast':False,'large_targets':True,'switch_control':False,'extended_timeout':True,'easy_banking':True,'reduced_motion':True}
    r=client.put('/api/v1/profile',json=payload); assert r.status_code==200; assert 'disability' not in r.json()

def test_analytics_aggregate_language_and_mode():
    client.post('/api/v1/assistant',json={'text':'Abeg check my balance','language_hint':'pcm-NG','interaction_mode':'voice'}); d=client.get('/api/v1/analytics/summary').json(); assert d['languages']['pcm-NG']>=1 and d['interaction_modes']['voice']>=1
