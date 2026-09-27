from __future__ import annotations

import hashlib
import os
import time
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from .. import store
from ..models import AccessibilityProfile

router = APIRouter(prefix="/api/v1/onboarding", tags=["accessible-onboarding"])

STAGES = [
    "accessibility", "registration", "contact_verification", "identity_verification",
    "security_setup", "consent", "ready_to_activate", "activated",
]
DEMO_OTP = "246810"
SESSION_TTL_SECONDS = 60 * 60

GUIDANCE = {
    "en-NG": {
        "accessibility": "Choose how you want registration to work before you enter any personal information.",
        "registration": "Enter your basic details. For this public demo, use only the synthetic details already provided.",
        "contact_verification": "Verify your contact details with the demo one-time code.",
        "identity_verification": "Choose an identity verification path. This demo never stores the full identity number.",
        "security_setup": "Set up secure authentication. Voice is an interface option, not an authentication credential.",
        "consent": "Review the important terms in clear language and decide what you consent to.",
        "ready_to_activate": "Everything required is complete. Review and open the demo account.",
        "activated": "Your accessible banking profile has been carried into the active account.",
    },
    "pcm-NG": {
        "accessibility": "Choose how you want make registration work for you before you put any personal information.",
        "registration": "Put your basic details. For this public demo, use only the sample details wey dey already.",
        "contact_verification": "Use the demo one-time code verify your contact.",
        "identity_verification": "Choose how you want verify identity. This demo no dey keep the full identity number.",
        "security_setup": "Set secure authentication. Voice na how you fit use the app; e no be your password.",
        "consent": "Read the important terms for simple language and choose wetin you agree to.",
        "ready_to_activate": "Everything don complete. Review am and open the demo account.",
        "activated": "Your accessibility settings don follow you enter the active account.",
    },
    "yo-NG": {
        "accessibility": "Yan bí o ṣe fẹ́ kí ìforúkọsílẹ̀ ṣiṣẹ́ fún ọ kí o tó fi ìwífún ara ẹni kankan sílẹ̀.",
        "registration": "Tẹ ìwífún ipilẹ rẹ sílẹ̀. Fún àpẹẹrẹ gbangba yìí, lo ìwífún àpẹẹrẹ tó ti wà níbẹ̀ nìkan.",
        "contact_verification": "Jẹ́rìí ìbánisọ̀rọ̀ rẹ pẹ̀lú kóòdù àpẹẹrẹ ẹ̀ẹ̀kan ṣoṣo.",
        "identity_verification": "Yan ọ̀nà ìjẹ́rìí ìdánimọ̀. Àpẹẹrẹ yìí kò fi gbogbo nọ́mbà ìdánimọ̀ pamọ́.",
        "security_setup": "Ṣètò ìdánimọ̀ tó lágbára. Ohùn jẹ́ ọ̀nà ìbánisọ̀rọ̀, kì í ṣe ọ̀rọ̀ aṣínà.",
        "consent": "Ka àwọn ọ̀rọ̀ pàtàkì ní èdè tó rọrùn, kí o sì yan ohun tí o fara mọ́.",
        "ready_to_activate": "Gbogbo ohun tó yẹ ti parí. Ṣàyẹ̀wò rẹ kí o sì ṣí àkọọ́lẹ̀ àpẹẹrẹ.",
        "activated": "Àwọn ìfẹ́ ìrọ̀rùn rẹ ti tẹ̀lé ọ sínú àkọọ́lẹ̀ tó ṣiṣẹ́.",
    },
    "ha-NG": {
        "accessibility": "Zaɓi yadda kake son rajista ta yi aiki a gare ka kafin ka shigar da bayanan sirri.",
        "registration": "Shigar da bayananka na asali. A wannan demo na jama'a, yi amfani da bayanan gwaji da aka riga aka cika kawai.",
        "contact_verification": "Tabbatar da bayanan tuntuɓarka da lambar gwaji ta lokaci ɗaya.",
        "identity_verification": "Zaɓi hanyar tabbatar da shaida. Wannan demo ba ya adana cikakkiyar lambar shaida.",
        "security_setup": "Saita ingantaccen tabbatarwa. Murya hanya ce ta amfani da app, ba kalmar sirri ba.",
        "consent": "Karanta muhimman sharuɗɗa cikin sauƙin harshe sannan ka zaɓi abin da ka amince da shi.",
        "ready_to_activate": "An kammala duk abin da ake buƙata. Duba sannan ka buɗe asusun demo.",
        "activated": "Saitunan samun dama sun bi ka zuwa asusun da aka kunna.",
    },
    "ig-NG": {
        "accessibility": "Họrọ ka ịchọrọ ka ndebanye aha si arụ ọrụ tupu i tinye ozi onwe gị.",
        "registration": "Tinye ozi gị bụ isi. Maka demo ọha a, jiri naanị ozi atụ e dejupụtara.",
        "contact_verification": "Jiri koodu demo otu oge kwado ozi kọntaktị gị.",
        "identity_verification": "Họrọ ụzọ nkwenye njirimara. Demo a anaghị echekwa nọmba njirimara zuru ezu.",
        "security_setup": "Hazie nkwenye nchekwa. Olu bụ ụzọ iji ngwa, ọ bụghị paswọọdụ gị.",
        "consent": "Gụọ okwu ndị dị mkpa n'asụsụ dị mfe ma họrọ ihe ị kwenyere na ya.",
        "ready_to_activate": "Ihe niile achọrọ ezuola. Nyochaa ya wee mepee akaụntụ demo.",
        "activated": "Ntọala nnweta gị esorola gị banye na akaụntụ arụnyere.",
    },
}

class SessionStart(BaseModel):
    profile: AccessibilityProfile = Field(default_factory=AccessibilityProfile)

class RegistrationDetails(BaseModel):
    first_name: str = Field(min_length=2, max_length=60)
    last_name: str = Field(min_length=2, max_length=60)
    email: str = Field(min_length=5, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(min_length=10, max_length=24)
    date_of_birth: date
    synthetic_data_acknowledged: bool

    @field_validator("date_of_birth")
    @classmethod
    def adult_demo(cls, value: date):
        today = date.today()
        years = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if years < 18:
            raise ValueError("Demo onboarding requires an adult customer")
        return value

class ContactVerification(BaseModel):
    code: str = Field(min_length=6, max_length=6)

class IdentityVerification(BaseModel):
    method: Literal["nin", "bvn", "passport"]
    identifier: str = Field(min_length=6, max_length=24)
    verification_mode: Literal["guided_camera", "document_plus_review", "accessible_assisted_review"] = "guided_camera"
    accessibility_guidance: bool = True

class SecuritySetup(BaseModel):
    pin: str = Field(pattern=r"^\d{4,6}$")
    confirm_pin: str = Field(pattern=r"^\d{4,6}$")
    prefer_passkey_or_biometrics: bool = True
    allow_device_biometrics: bool = True

class ConsentRequest(BaseModel):
    terms_accepted: bool
    privacy_notice_accepted: bool
    accessibility_preferences_accepted: bool
    plain_language_summary_read: bool

class ActivationRequest(BaseModel):
    confirmed: bool

def _event(name: str, session: dict, **metadata):
    store.EVENTS.append({
        "event": name,
        "journey": "onboarding",
        "language": session["profile"]["primary_language"],
        "interaction_mode": "voice" if session["profile"].get("voice_guidance") else "standard",
        "metadata": metadata,
    })

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _session(session_id: str) -> dict:
    session = store.ONBOARDING_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Onboarding session not found")
    if time.monotonic() - session["created_monotonic"] > SESSION_TTL_SECONDS:
        raise HTTPException(410, "Onboarding session expired")
    return session

def _require(session: dict, expected: str):
    if session["stage"] != expected:
        raise HTTPException(409, f"This step cannot run while onboarding is at '{session['stage']}'")

def _public(session: dict):
    lang = session["profile"]["primary_language"]
    return {
        "session_id": session["session_id"],
        "stage": session["stage"],
        "progress": STAGES.index(session["stage"]) / (len(STAGES) - 1),
        "profile": session["profile"],
        "registration": session.get("registration"),
        "contact_verified": session.get("contact_verified", False),
        "identity": session.get("identity"),
        "security": session.get("security_public"),
        "consent": session.get("consent"),
        "account": session.get("account"),
        "guidance": GUIDANCE.get(lang, GUIDANCE["en-NG"])[session["stage"]],
    }

@router.post("/sessions")
def create_session(request: SessionStart):
    sid = f"ONB-{uuid.uuid4().hex[:12].upper()}"
    session = {
        "session_id": sid, "stage": "accessibility",
        "profile": request.profile.model_dump(mode="json"),
        "created_monotonic": time.monotonic(), "contact_verified": False,
    }
    store.ONBOARDING_SESSIONS[sid] = session
    _event("onboarding_started", session)
    return _public(session)

@router.get("/{session_id}")
def get_session(session_id: str):
    return _public(_session(session_id))

@router.put("/{session_id}/accessibility")
def save_accessibility(session_id: str, profile: AccessibilityProfile):
    session = _session(session_id); _require(session, "accessibility")
    session["profile"] = profile.model_dump(mode="json")
    session["stage"] = "registration"
    _event("onboarding_accessibility_configured", session,
           voice_guidance=profile.voice_guidance, captions=profile.captions,
           screen_reader=profile.screen_reader, large_targets=profile.large_targets,
           easy_banking=profile.easy_banking)
    return _public(session)

@router.post("/{session_id}/registration")
def registration(session_id: str, details: RegistrationDetails):
    session = _session(session_id); _require(session, "registration")
    if not details.synthetic_data_acknowledged:
        raise HTTPException(400, "Acknowledge that the public demo must use synthetic data")
    if not details.email.lower().endswith("@example.com"):
        raise HTTPException(400, "Use the prefilled example.com email in this public demo")
    if details.phone != "+2348000000000":
        raise HTTPException(400, "Use the prefilled synthetic phone number in this public demo")
    local, domain = details.email.split("@", 1)
    session["registration"] = {
        "first_name": details.first_name, "last_name": details.last_name,
        "email_masked": f"{local[:1]}***@{domain}",
        "phone_masked": f"******{details.phone[-4:]}",
        "date_of_birth": details.date_of_birth.isoformat(),
    }
    session["stage"] = "contact_verification"
    session["otp_hash"] = _hash(DEMO_OTP)
    _event("onboarding_registration_completed", session)
    return {**_public(session), "demo_code": DEMO_OTP if os.getenv("ACCESSFLOW_PUBLIC_DEMO", "1") == "1" else None}

@router.post("/{session_id}/contact/verify")
def verify_contact(session_id: str, request: ContactVerification):
    session = _session(session_id); _require(session, "contact_verification")
    if _hash(request.code) != session.get("otp_hash"):
        _event("onboarding_contact_verification_failed", session)
        raise HTTPException(400, "Verification code is incorrect")
    session["contact_verified"] = True
    session.pop("otp_hash", None)
    session["stage"] = "identity_verification"
    _event("onboarding_contact_verified", session)
    return _public(session)

@router.post("/{session_id}/identity")
def verify_identity(session_id: str, request: IdentityVerification):
    session = _session(session_id); _require(session, "identity_verification")
    session["identity"] = {
        "method": request.method,
        "identifier_last4": request.identifier[-4:],
        "verification_mode": request.verification_mode,
        "status": "verified_demo",
        "accessibility_guidance": request.accessibility_guidance,
    }
    session["stage"] = "security_setup"
    _event("onboarding_identity_verified", session, method=request.method, verification_mode=request.verification_mode)
    return _public(session)

@router.post("/{session_id}/security")
def setup_security(session_id: str, request: SecuritySetup):
    session = _session(session_id); _require(session, "security_setup")
    if request.pin != request.confirm_pin:
        raise HTTPException(400, "PIN entries do not match")
    if request.pin in {"0000", "1111", "1234", "2222", "4321"}:
        raise HTTPException(400, "Choose a less predictable PIN for onboarding")
    session["pin_hash"] = _hash(request.pin)
    session["security_public"] = {
        "pin_configured": True,
        "prefer_passkey_or_biometrics": request.prefer_passkey_or_biometrics,
        "allow_device_biometrics": request.allow_device_biometrics,
        "voice_is_authentication": False,
    }
    session["stage"] = "consent"
    _event("onboarding_security_configured", session, passkey_preferred=request.prefer_passkey_or_biometrics)
    return _public(session)

@router.post("/{session_id}/consent")
def save_consent(session_id: str, request: ConsentRequest):
    session = _session(session_id); _require(session, "consent")
    if not all([request.terms_accepted, request.privacy_notice_accepted,
                request.accessibility_preferences_accepted, request.plain_language_summary_read]):
        raise HTTPException(400, "All required onboarding consent items must be reviewed and accepted")
    session["consent"] = request.model_dump(mode="json")
    session["stage"] = "ready_to_activate"
    _event("onboarding_consent_completed", session)
    return _public(session)

@router.post("/{session_id}/activate")
def activate(session_id: str, request: ActivationRequest):
    session = _session(session_id); _require(session, "ready_to_activate")
    if not request.confirmed:
        raise HTTPException(400, "Explicit activation confirmation is required")
    customer_id = f"CUS-{uuid.uuid4().hex[:8].upper()}"
    account_id = f"ACC-{uuid.uuid4().hex[:8].upper()}"
    account = {
        "customer_id": customer_id, "account_id": account_id,
        "account_name": "AccessFlow Demo Current Account",
        "masked_account": "******6789", "currency": "NGN", "status": "active_demo",
    }
    session["account"] = account
    session["stage"] = "activated"
    store.PROFILE = AccessibilityProfile(**session["profile"])
    store.ACTIVATED_DEMO_CUSTOMERS[customer_id] = {
        "customer_id": customer_id, "profile": session["profile"],
        "registration": session["registration"], "identity": session["identity"], "account": account,
    }
    _event("onboarding_completed", session, customer_id=customer_id)
    return {**_public(session), "next_url": "/?onboarded=1"}
