from __future__ import annotations
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field

LanguageCode = Literal["en-NG", "yo-NG", "ha-NG", "ig-NG", "pcm-NG"]
Action = Literal["get_balance","recent_transactions","transfer_money","check_transfer_status","freeze_card","report_suspicious_transaction","contact_support","unknown"]

class AccessibilityProfile(BaseModel):
    primary_language: LanguageCode = "en-NG"
    allow_code_switching: bool = True
    voice_guidance: bool = False
    captions: bool = False
    screen_reader: bool = False
    large_text: bool = False
    high_contrast: bool = False
    large_targets: bool = False
    switch_control: bool = False
    extended_timeout: bool = False
    easy_banking: bool = False
    reduced_motion: bool = False

class IntentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=700)
    language_hint: Optional[LanguageCode] = None

class BankingIntent(BaseModel):
    intent_id: str
    action: Action
    language: LanguageCode
    code_switched: bool = False
    amount: Optional[Decimal] = None
    currency: Literal["NGN"] = "NGN"
    beneficiary_query: Optional[str] = None
    transaction_query: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    clarification: Optional[str] = None
    raw_text: Optional[str] = None

class AssistantRequest(IntentRequest):
    interaction_mode: str = "text"

class AssistantResponse(BaseModel):
    type: Literal["message","transfer_preview","confirmation","error"]
    intent: BankingIntent
    message: str
    data: dict = Field(default_factory=dict)

class TransferPreviewRequest(BaseModel):
    intent_id: str

class TransferPreview(BaseModel):
    preview_id: str
    intent_id: str
    beneficiary_id: str
    beneficiary_name: str
    bank_name: str
    masked_account: str
    amount: Decimal
    fee: Decimal = Decimal("0")
    total_debit: Decimal
    expires_in_seconds: int = 120
    status: Literal["awaiting_confirmation"] = "awaiting_confirmation"
    confirmation_text: str

class TransferConfirmRequest(BaseModel):
    confirmed: bool
    pin: str = Field(min_length=4, max_length=12)
    idempotency_key: Optional[str] = Field(default=None, max_length=120)

class StateChangeConfirmRequest(BaseModel):
    confirmed: bool
    pin: str = Field(min_length=4, max_length=12)

class AnalyticsEvent(BaseModel):
    event: str = Field(min_length=1, max_length=80)
    journey: Optional[str] = Field(default=None, max_length=80)
    language: Optional[LanguageCode] = None
    interaction_mode: Optional[str] = Field(default=None, max_length=40)
    metadata: dict = Field(default_factory=dict)
