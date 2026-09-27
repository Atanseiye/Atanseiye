import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app import store

client=TestClient(app)

@pytest.fixture(autouse=True)
def reset_demo():
    store.reset_demo()
    yield

PROFILE={"primary_language":"pcm-NG","allow_code_switching":True,"voice_guidance":True,"captions":True,"screen_reader":False,"large_text":False,"high_contrast":False,"large_targets":True,"switch_control":False,"extended_timeout":True,"easy_banking":True,"reduced_motion":True}
REG={"first_name":"Kemi","last_name":"Demo","email":"kemi.demo@example.com","phone":"+2348000000000","date_of_birth":"1994-06-12","synthetic_data_acknowledged":True}

def start():
    r=client.post("/api/v1/onboarding/sessions",json={"profile":{}})
    assert r.status_code==200
    return r.json()["session_id"]

def accessibility(sid):
    return client.put(f"/api/v1/onboarding/{sid}/accessibility",json=PROFILE)

def reach_identity(sid):
    assert accessibility(sid).status_code==200
    assert client.post(f"/api/v1/onboarding/{sid}/registration",json=REG).status_code==200
    assert client.post(f"/api/v1/onboarding/{sid}/contact/verify",json={"code":"246810"}).status_code==200

def reach_consent(sid):
    reach_identity(sid)
    assert client.post(f"/api/v1/onboarding/{sid}/identity",json={"method":"passport","identifier":"DEMO654321","verification_mode":"guided_camera","accessibility_guidance":True}).status_code==200
    assert client.post(f"/api/v1/onboarding/{sid}/security",json={"pin":"5826","confirm_pin":"5826","prefer_passkey_or_biometrics":True,"allow_device_biometrics":True}).status_code==200

def test_accessibility_is_first_stage():
    sid=start()
    assert client.get(f"/api/v1/onboarding/{sid}").json()["stage"]=="accessibility"

def test_registration_cannot_skip_accessibility():
    sid=start()
    assert client.post(f"/api/v1/onboarding/{sid}/registration",json=REG).status_code==409

def test_accessibility_preferences_persist_during_onboarding():
    sid=start()
    data=accessibility(sid).json()
    assert data["profile"]["primary_language"]=="pcm-NG"
    assert data["profile"]["captions"] is True

def test_public_demo_requires_synthetic_acknowledgement():
    sid=start(); accessibility(sid)
    body={**REG,"synthetic_data_acknowledged":False}
    assert client.post(f"/api/v1/onboarding/{sid}/registration",json=body).status_code==400

def test_wrong_verification_code_does_not_advance():
    sid=start(); accessibility(sid)
    client.post(f"/api/v1/onboarding/{sid}/registration",json=REG)
    assert client.post(f"/api/v1/onboarding/{sid}/contact/verify",json={"code":"000000"}).status_code==400

def test_identity_response_masks_identifier():
    sid=start(); reach_identity(sid)
    data=client.post(f"/api/v1/onboarding/{sid}/identity",json={"method":"passport","identifier":"DEMO654321","verification_mode":"document_plus_review","accessibility_guidance":True}).json()
    assert data["identity"]["identifier_last4"]=="4321"
    assert "DEMO654321" not in str(data)

def test_weak_pin_is_rejected():
    sid=start(); reach_identity(sid)
    client.post(f"/api/v1/onboarding/{sid}/identity",json={"method":"passport","identifier":"DEMO654321","verification_mode":"guided_camera","accessibility_guidance":True})
    assert client.post(f"/api/v1/onboarding/{sid}/security",json={"pin":"1234","confirm_pin":"1234","prefer_passkey_or_biometrics":True,"allow_device_biometrics":True}).status_code==400

def test_incomplete_consent_is_rejected():
    sid=start(); reach_consent(sid)
    body={"terms_accepted":True,"privacy_notice_accepted":True,"accessibility_preferences_accepted":False,"plain_language_summary_read":True}
    assert client.post(f"/api/v1/onboarding/{sid}/consent",json=body).status_code==400

def test_full_activation_carries_profile_into_banking():
    sid=start(); reach_consent(sid)
    body={"terms_accepted":True,"privacy_notice_accepted":True,"accessibility_preferences_accepted":True,"plain_language_summary_read":True}
    assert client.post(f"/api/v1/onboarding/{sid}/consent",json=body).status_code==200
    out=client.post(f"/api/v1/onboarding/{sid}/activate",json={"confirmed":True})
    assert out.status_code==200
    assert out.json()["stage"]=="activated"
    assert client.get("/api/v1/profile").json()["primary_language"]=="pcm-NG"

def test_onboarding_is_visible_in_accessibility_analytics():
    sid=start(); reach_consent(sid)
    body={"terms_accepted":True,"privacy_notice_accepted":True,"accessibility_preferences_accepted":True,"plain_language_summary_read":True}
    client.post(f"/api/v1/onboarding/{sid}/consent",json=body)
    client.post(f"/api/v1/onboarding/{sid}/activate",json={"confirmed":True})
    analytics=client.get("/api/v1/analytics/summary").json()
    assert analytics["onboarding_completion_count"]==1
    assert analytics["onboarding_funnel"]["Account activated"]==1
