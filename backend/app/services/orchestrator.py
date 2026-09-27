from .. import store
from ..models import AssistantResponse
from .banking import create_preview,find_transaction,report_fraud,open_support_case
from .localization import msg,money
def handle_intent(intent):
    lang=intent.language
    if intent.clarification:return AssistantResponse(type="message",intent=intent,message=intent.clarification)
    if intent.action=="get_balance":return AssistantResponse(type="message",intent=intent,message=msg(lang,"balance",amount=money(store.ACCOUNT["balance"])),data={"balance":store.ACCOUNT["balance"],"currency":"NGN"})
    if intent.action=="recent_transactions":
        tx=store.TRANSACTIONS[:5];return AssistantResponse(type="message",intent=intent,message=msg(lang,"transactions",count=len(tx)),data={"transactions":tx})
    if intent.action=="transfer_money":
        p=create_preview(intent);return AssistantResponse(type="transfer_preview",intent=intent,message=p.confirmation_text,data=p.model_dump(mode="json"))
    if intent.action=="check_transfer_status":
        tx=find_transaction(intent.transaction_query); key="successful" if tx and tx["status"]=="successful" else "pending";return AssistantResponse(type="message",intent=intent,message=msg(lang,key),data={"transaction":tx})
    if intent.action=="freeze_card":return AssistantResponse(type="confirmation",intent=intent,message="Freezing your card blocks new card payments. Confirm and authenticate to continue.",data={"action":"freeze_card","card":store.CARD})
    if intent.action=="report_suspicious_transaction":
        case=report_fraud(intent.transaction_query);return AssistantResponse(type="message",intent=intent,message=msg(lang,"fraud_reported"),data={"case":case})
    if intent.action=="contact_support":
        case=open_support_case(intent.raw_text or "Accessible support request");return AssistantResponse(type="message",intent=intent,message=msg(lang,"support",ref=case["case_id"]),data={"case":case})
    return AssistantResponse(type="message",intent=intent,message=msg(lang,"unknown"))
