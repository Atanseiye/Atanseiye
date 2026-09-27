from __future__ import annotations
from collections import Counter,defaultdict
from fastapi import APIRouter,HTTPException
from .. import store
from ..models import AccessibilityProfile,AssistantRequest,TransferPreviewRequest,TransferConfirmRequest,StateChangeConfirmRequest,AnalyticsEvent
from ..services.natlas import get_provider
from ..services.banking import BankingError,create_preview,execute_preview,freeze_card
from ..services.orchestrator import handle_intent

router=APIRouter(prefix="/api/v1")
LANGS=[{"code":"en-NG","name":"English","native":"English"},{"code":"yo-NG","name":"Yorùbá","native":"Yorùbá"},{"code":"ha-NG","name":"Hausa","native":"Hausa"},{"code":"ig-NG","name":"Igbo","native":"Igbo"},{"code":"pcm-NG","name":"Pidgin","native":"Naija Pidgin"}]
PERSONAS=[
{"id":"ade","name":"Ade","description":"Blind, Yoruba-first customer using voice guidance and screen-reader optimized navigation.","profile":{"primary_language":"yo-NG","allow_code_switching":True,"voice_guidance":True,"captions":False,"screen_reader":True,"large_text":False,"high_contrast":False,"large_targets":True,"switch_control":False,"extended_timeout":True,"easy_banking":True,"reduced_motion":True},"example_request":"Mo fẹ transfer 10k si Adewale"},
{"id":"ifeoma","name":"Ifeoma","description":"Deaf, Pidgin-first customer using captions, visual alerts and Easy Banking.","profile":{"primary_language":"pcm-NG","allow_code_switching":True,"voice_guidance":False,"captions":True,"screen_reader":False,"large_text":False,"high_contrast":False,"large_targets":True,"switch_control":False,"extended_timeout":True,"easy_banking":True,"reduced_motion":True},"example_request":"Why my transaction still dey pending?"},
{"id":"musa","name":"Musa","description":"Motor-impaired, Hausa-first customer using large controls, voice banking and extended timeouts.","profile":{"primary_language":"ha-NG","allow_code_switching":True,"voice_guidance":True,"captions":False,"screen_reader":False,"large_text":True,"high_contrast":False,"large_targets":True,"switch_control":True,"extended_timeout":True,"easy_banking":True,"reduced_motion":True},"example_request":"Aika 5k zuwa Amina"}]
def event(name,**kwargs):store.EVENTS.append({"event":name,**kwargs})

@router.get("/languages")
def languages():return LANGS
@router.get("/personas")
def personas():return PERSONAS
@router.post("/demo/reset")
def reset_demo():store.reset_demo();return {"ok":True}
@router.get("/profile",response_model=AccessibilityProfile)
def get_profile():return store.PROFILE
@router.put("/profile",response_model=AccessibilityProfile)
def put_profile(profile):
    store.PROFILE=profile;event("profile_updated",language=profile.primary_language,interaction_mode="voice" if profile.voice_guidance else "standard",metadata={"easy_banking":profile.easy_banking,"captions":profile.captions,"screen_reader":profile.screen_reader,"large_targets":profile.large_targets});return profile
@router.get("/account")
def account():return {**store.ACCOUNT,"number":"******"+store.ACCOUNT["number"][-4:]}
@router.get("/transactions")
def transactions():return store.TRANSACTIONS[:10]
@router.get("/card")
def card():return store.CARD

@router.post("/intent/parse")
async def parse_intent(request:AssistantRequest):
    try:
        intent=await get_provider().parse(request);store.INTENTS[intent.intent_id]=intent.model_dump(mode="json");event("intent_parsed",language=intent.language,interaction_mode=request.interaction_mode,metadata={"action":intent.action,"confidence":intent.confidence,"code_switched":intent.code_switched});return intent
    except Exception as e:raise HTTPException(502,f"Language service error: {e}")

@router.post("/assistant")
async def assistant(request:AssistantRequest):
    try:
        intent=await get_provider().parse(request);store.INTENTS[intent.intent_id]=intent.model_dump(mode="json");event("intent_parsed",language=intent.language,interaction_mode=request.interaction_mode,journey=intent.action,metadata={"confidence":intent.confidence,"code_switched":intent.code_switched});response=handle_intent(intent);event("assistant_response",language=intent.language,interaction_mode=request.interaction_mode,journey=intent.action,metadata={"type":response.type});return response
    except BankingError as e:raise HTTPException(400,str(e))
    except Exception as e:raise HTTPException(502,f"Language service error: {e}")

@router.post("/transfers/preview")
def preview_transfer(request:TransferPreviewRequest):
    raw=store.INTENTS.get(request.intent_id)
    if not raw:raise HTTPException(404,"Intent not found")
    from ..models import BankingIntent
    try:
        p=create_preview(BankingIntent(**raw));event("transfer_previewed",journey="transfer",language=raw.get("language"));return p
    except BankingError as e:raise HTTPException(400,str(e))

@router.post("/transfers/{preview_id}/confirm")
def confirm_transfer(preview_id:str,request:TransferConfirmRequest):
    try:
        result=execute_preview(preview_id,request.confirmed,request.pin,request.idempotency_key);event("transfer_completed",journey="transfer",language=store.PROFILE.primary_language);return result
    except BankingError as e:event("transfer_failed",journey="transfer",language=store.PROFILE.primary_language,metadata={"reason":str(e)});raise HTTPException(400,str(e))

@router.post("/card/freeze")
def confirm_card_freeze(request:StateChangeConfirmRequest):
    if not request.confirmed:raise HTTPException(400,"Explicit confirmation is required")
    try:
        c=freeze_card(request.pin);event("card_frozen",journey="card_security",language=store.PROFILE.primary_language);return c
    except BankingError as e:event("card_freeze_failed",journey="card_security",metadata={"reason":str(e)});raise HTTPException(400,str(e))

@router.post("/events")
def record_event(e:AnalyticsEvent):store.EVENTS.append(e.model_dump());return {"ok":True}
@router.get("/analytics/summary")
def analytics_summary():
    languages=Counter(e.get("language") for e in store.EVENTS if e.get("language"));events=Counter(e.get("event") for e in store.EVENTS);modes=Counter(e.get("interaction_mode") for e in store.EVENTS if e.get("interaction_mode"));journeys=defaultdict(lambda:{"events":0,"completed":0,"failed":0})
    for e in store.EVENTS:
        j=e.get("journey")
        if j:
            journeys[j]["events"]+=1
            if str(e.get("event","")).endswith("completed"):journeys[j]["completed"]+=1
            if "failed" in str(e.get("event","")):journeys[j]["failed"]+=1
    return {"total_events":len(store.EVENTS),"languages":dict(languages),"events":dict(events),"interaction_modes":dict(modes),"journeys":dict(journeys),"transfer_completion_count":events.get("transfer_completed",0),"transfer_failure_count":events.get("transfer_failed",0),"support_cases":len(store.SUPPORT_CASES),"fraud_reports":len(store.FRAUD_REPORTS),"card_frozen":store.CARD["frozen"]}
