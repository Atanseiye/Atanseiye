from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone
from threading import RLock
from .models import AccessibilityProfile

LOCK=RLock(); PROFILE=AccessibilityProfile()
ACCOUNT={"id":"ACC-1001","name":"Demo Current Account","number":"0123456789","balance":Decimal("82400.00"),"currency":"NGN"}
BENEFICIARIES=[
 {"id":"BEN-1","name":"Chinedu Okafor","bank":"Access Bank","account":"0048291920"},
 {"id":"BEN-2","name":"Adewale Johnson","bank":"GTBank","account":"0187344917"},
 {"id":"BEN-3","name":"Amina Bello","bank":"Zenith Bank","account":"1018832044"}]
INTENTS={}; PREVIEWS={}; EVENTS=[]; IDEMPOTENCY={}; SUPPORT_CASES=[]; FRAUD_REPORTS=[]
CARD={"id":"CARD-1","masked":"5399 **** **** 2411","frozen":False}

def _seed_transactions():
    now=datetime.now(timezone.utc).isoformat()
    return [
      {"transaction_id":"TX-SEED-1","type":"debit","amount":Decimal("3500"),"description":"Electricity purchase","status":"successful","created_at":now},
      {"transaction_id":"TX-SEED-2","type":"credit","amount":Decimal("25000"),"description":"Transfer received","status":"successful","created_at":now},
      {"transaction_id":"TX-SEED-3","type":"debit","amount":Decimal("12000"),"description":"Transfer to Amina Bello","status":"successful","created_at":now},
      {"transaction_id":"TX-SEED-4","type":"debit","amount":Decimal("7200"),"description":"Internet subscription","status":"pending","created_at":now}]
TRANSACTIONS=_seed_transactions()

def reset_demo():
    global PROFILE
    with LOCK:
        PROFILE=AccessibilityProfile(); ACCOUNT["balance"]=Decimal("82400.00"); CARD["frozen"]=False
        INTENTS.clear(); PREVIEWS.clear(); EVENTS.clear(); IDEMPOTENCY.clear(); SUPPORT_CASES.clear(); FRAUD_REPORTS.clear()
        TRANSACTIONS[:]=_seed_transactions()
