from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
import os,time,uuid
from .. import store
from ..models import BankingIntent,TransferPreview
from .localization import msg,money

class BankingError(Exception): pass
def masked(account): return "*"*max(0,len(account)-4)+account[-4:]
def resolve_beneficiary(query):
    if not query: raise BankingError("A beneficiary is required")
    q=query.lower().strip(); matches=[b for b in store.BENEFICIARIES if q in b["name"].lower()]
    if len(matches)==0: raise BankingError("Beneficiary was not found")
    if len(matches)>1: raise BankingError("Beneficiary could not be resolved uniquely")
    return matches[0]
def create_preview(intent):
    if intent.action!="transfer_money": raise BankingError("Intent is not a transfer")
    if intent.confidence<.85 or intent.clarification: raise BankingError("Intent is not confident enough; clarification is required")
    if intent.amount is None or intent.amount<=0: raise BankingError("A valid transfer amount is required")
    if intent.amount>Decimal(os.environ.get("DEMO_MAX_TRANSFER","250000")): raise BankingError("Transfer exceeds the demo safety limit")
    ben=resolve_beneficiary(intent.beneficiary_query); fee=Decimal("0"); total=intent.amount+fee
    if total>store.ACCOUNT["balance"]: raise BankingError("Insufficient balance")
    pid=f"PRE-{uuid.uuid4().hex[:10].upper()}"; text=msg(intent.language,"transfer_confirm",amount=money(intent.amount),name=ben["name"],bank=ben["bank"],ending=ben["account"][-4:])
    p=TransferPreview(preview_id=pid,intent_id=intent.intent_id,beneficiary_id=ben["id"],beneficiary_name=ben["name"],bank_name=ben["bank"],masked_account=masked(ben["account"]),amount=intent.amount,fee=fee,total_debit=total,confirmation_text=text)
    raw=p.model_dump(mode="json"); raw["created_monotonic"]=time.monotonic(); raw["executed"]=False
    with store.LOCK: store.PREVIEWS[pid]=raw
    return p
def execute_preview(preview_id,confirmed,pin,idempotency_key=None):
    with store.LOCK:
        if idempotency_key and idempotency_key in store.IDEMPOTENCY: return store.IDEMPOTENCY[idempotency_key]
        if preview_id not in store.PREVIEWS: raise BankingError("Transfer preview not found")
        p=store.PREVIEWS[preview_id]
        if p["executed"]: raise BankingError("This transfer has already been executed")
        if time.monotonic()-p["created_monotonic"]>120: raise BankingError("Transfer preview expired")
        if not confirmed: raise BankingError("Explicit confirmation is required")
        if pin!=os.environ.get("DEMO_PIN","1234"): raise BankingError("Authentication failed")
        amount=Decimal(str(p["total_debit"]))
        if amount>store.ACCOUNT["balance"]: raise BankingError("Insufficient balance")
        store.ACCOUNT["balance"]-=amount; p["executed"]=True; txid=f"TX-{uuid.uuid4().hex[:10].upper()}"
        record={"transaction_id":txid,"type":"debit","amount":Decimal(str(p["amount"])),"description":f"Transfer to {p['beneficiary_name']}","status":"successful","created_at":datetime.now(timezone.utc).isoformat()}
        store.TRANSACTIONS.insert(0,record); result={"transaction":record,"new_balance":store.ACCOUNT["balance"]}
        if idempotency_key: store.IDEMPOTENCY[idempotency_key]=result
        return result
def find_transaction(query=None):
    q=(query or "").strip().lower()
    if q:
        for tx in store.TRANSACTIONS:
            if q in tx["transaction_id"].lower() or q in tx["description"].lower(): return tx
    return store.TRANSACTIONS[0] if store.TRANSACTIONS else None
def freeze_card(pin):
    if pin!=os.environ.get("DEMO_PIN","1234"): raise BankingError("Authentication failed")
    store.CARD["frozen"]=True; return dict(store.CARD)
def report_fraud(query=None):
    tx=find_transaction(query); case={"case_id":f"FRD-{uuid.uuid4().hex[:8].upper()}","transaction_id":tx["transaction_id"] if tx else None,"status":"under_review","created_at":datetime.now(timezone.utc).isoformat()}; store.FRAUD_REPORTS.insert(0,case); return case
def open_support_case(summary):
    case={"case_id":f"SUP-{uuid.uuid4().hex[:8].upper()}","summary":summary,"status":"open","created_at":datetime.now(timezone.utc).isoformat()}; store.SUPPORT_CASES.insert(0,case); return case
