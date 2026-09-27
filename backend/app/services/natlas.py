from __future__ import annotations
import json,os,re,uuid
from decimal import Decimal
import httpx
from ..models import BankingIntent,IntentRequest

SYSTEM_PROMPT="""You are the language-understanding layer for AccessFlow, an accessible Nigerian banking interface.
You NEVER execute financial actions and NEVER invent bank state. Convert the user's request into strict JSON only.
Allowed actions: get_balance, recent_transactions, transfer_money, check_transfer_status, freeze_card, report_suspicious_transaction, contact_support, unknown.
Return action, language, code_switched, amount, beneficiary_query, transaction_query, confidence, clarification.
language must be one of en-NG, yo-NG, ha-NG, ig-NG, pcm-NG. Never skip confirmation or authentication."""
class NAtlasProvider:
    async def parse(self,request): raise NotImplementedError
class OpenAICompatNAtlasProvider(NAtlasProvider):
    def __init__(self):
        self.base_url=os.environ.get("NATLAS_BASE_URL","").rstrip("/"); self.api_key=os.environ.get("NATLAS_API_KEY",""); self.model=os.environ.get("NATLAS_MODEL","NCAIR1/N-ATLaS")
    async def parse(self,request):
        if not self.base_url: raise RuntimeError("NATLAS_BASE_URL is not configured")
        headers={"Content-Type":"application/json"}
        if self.api_key: headers["Authorization"]=f"Bearer {self.api_key}"
        payload={"model":self.model,"temperature":0,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":request.text}]}
        async with httpx.AsyncClient(timeout=45) as client:
            r=await client.post(f"{self.base_url}/v1/chat/completions",json=payload,headers=headers); r.raise_for_status(); data=r.json()
        obj=json.loads(data["choices"][0]["message"]["content"]); obj["intent_id"]=f"INT-{uuid.uuid4().hex[:10].upper()}"; obj["raw_text"]=request.text
        return BankingIntent(**obj)
class MockNAtlasProvider(NAtlasProvider):
    markers={"pcm-NG":["abeg","dey","wetin","give","no enter","never enter"],"yo-NG":["mo fẹ","mo fe","owó","owo","ránṣẹ","ranse","jọ̀wọ́"],"ha-NG":["aika","kuɗi","kudi","asusun","don Allah"],"ig-NG":["zipu","ego","akaụntụ","akauntu","biko"]}
    def detect(self,text,hint):
        t=text.lower(); scores={k:sum(m in t for m in v) for k,v in self.markers.items()}; best=max(scores,key=scores.get); lang=best if scores[best] else (hint or "en-NG"); english=any(x in t for x in ["send","transfer","balance","card","transaction","help"]); return lang,lang!="en-NG" and english
    def amount(self,text):
        t=text.lower().replace(",",""); m=re.search(r"(?:₦|ngn\s*)?(\d+(?:\.\d+)?)\s*(k|thousand|m|million)?",t)
        if not m:return None
        v=Decimal(m.group(1)); s=(m.group(2) or "").lower()
        if s in {"k","thousand"}:v*=1000
        elif s in {"m","million"}:v*=1000000
        return v
    async def parse(self,request):
        text=request.text.strip();t=text.lower();lang,code=self.detect(text,request.language_hint);base={"intent_id":f"INT-{uuid.uuid4().hex[:10].upper()}","language":lang,"code_switched":code,"raw_text":text}
        if any(x in t for x in ["balance","how much","owo mi","owó mi","kudi na","ego m"]): return BankingIntent(action="get_balance",confidence=.98,**base)
        if any(x in t for x in ["recent","transactions","statement","mu'amala","azụmahịa"]): return BankingIntent(action="recent_transactions",confidence=.96,**base)
        if any(x in t for x in ["freeze card","block card","card mi","katin","kaadị"]): return BankingIntent(action="freeze_card",confidence=.95,**base)
        if any(x in t for x in ["fraud","suspicious","scam","zamba","aghụghọ"]): return BankingIntent(action="report_suspicious_transaction",confidence=.94,**base)
        if any(x in t for x in ["status","pending","no enter","never enter","did it go"]): return BankingIntent(action="check_transfer_status",confidence=.92,**base)
        if any(x in t for x in ["support","help me","customer care","talk to person","agent"]): return BankingIntent(action="contact_support",confidence=.94,**base)
        if any(x in t for x in ["send","transfer","give","aika","ránṣẹ","ranse","zipu"]):
            amount=self.amount(text); known=["chinedu","okafor","adewale","johnson","amina","bello"]; found=next((n for n in known if n in t),None); clarification=None; conf=.97
            if amount is None: clarification="What amount would you like to send?"; conf=.70
            elif found is None: clarification="Who would you like to send the money to?"; conf=.72
            return BankingIntent(action="transfer_money",amount=amount,beneficiary_query=found,confidence=conf,clarification=clarification,**base)
        return BankingIntent(action="unknown",confidence=.35,clarification="I did not understand that clearly. Please try again.",**base)
def get_provider(): return OpenAICompatNAtlasProvider() if os.environ.get("NATLAS_MODE","mock").lower() in {"remote","openai","openai-compatible"} else MockNAtlasProvider()
