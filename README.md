# AccessFlow AI

**One integration layer for accessible, multilingual digital banking.**

AccessFlow is a competition-grade SDK/platform and demonstration bank for Zecathon 6.0's Inclusive Digital Banking challenge. It is designed to integrate into an existing bank application rather than replace the bank's mobile/web stack.

## What the demo proves

- English, Yorùbá, Hausa, Igbo and Nigerian Pidgin interaction model
- accessible registration before login: language/preferences → registration → contact verification → flexible KYC → security → consent → activation
- customer-controlled accessibility profiles rather than inferred disability labels
- voice/text banking and code-switch-aware intent routing
- safe transfers: intent → bank resolution → immutable preview → explicit confirmation → authentication → execution
- account reads, transaction status, card security, fraud reporting and accessible support
- bank-side Accessibility Intelligence dashboard
- embeddable TypeScript SDK contract
- N-ATLAS provider abstraction with a deterministic public-demo fallback

## Safety boundary

N-ATLAS is **not** the ledger and cannot move money. The language layer can only produce a structured intent. Core banking state is always fetched from the bank adapter, and state-changing operations require deterministic validation, explicit customer confirmation and the bank's authentication mechanism.

## Live demo

- Accessible registration: https://accessflow-ai-demo.onrender.com/register
- Customer: https://accessflow-ai-demo.onrender.com
- Accessibility Intelligence: https://accessflow-ai-demo.onrender.com/admin
- OpenAPI: https://accessflow-ai-demo.onrender.com/docs
- Health: https://accessflow-ai-demo.onrender.com/health
- Demo PIN: `1234`

## Local development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

## N-ATLAS

The public demo defaults to `NATLAS_MODE=mock` so it is deterministic and does not pretend to have model credentials that are not present. To use an OpenAI-compatible N-ATLAS deployment:

```env
NATLAS_MODE=remote
NATLAS_BASE_URL=https://your-model-endpoint
NATLAS_API_KEY=...
NATLAS_MODEL=NCAIR1/N-ATLaS
```

The rest of AccessFlow does not change when the model endpoint changes.

## Repository structure

```text
backend/app/           FastAPI application and demo UI
backend/app/services/  language provider, orchestrator, banking safety, localization
sdk/                   embeddable TypeScript integration SDK
evals/                 multilingual banking evaluation seed set
tests/                 safety and end-to-end API tests
docs/                  architecture, security, implementation and demo guidance
render.yaml            Render blueprint
```

## Verification

```bash
PYTHONPATH=backend pytest -q
```

Current suite: **36 tests** covering multilingual intent handling, transaction safety, registration stage enforcement, contact verification, accessible KYC privacy, public-demo data guards, security setup, consent, account activation, profile continuity, card security, fraud/support flows and analytics.

The public onboarding demo is also intentionally synthetic: users are warned not to enter real BVN/NIN/passport or personal information, and the demo backend retains only the last four characters of the mock identity number.

## Production path

The demo store is intentionally self-contained. A bank pilot replaces the demo adapter with the bank's customer/account/beneficiary/payment/authentication APIs, and replaces the demo model provider with the approved N-ATLAS deployment. The SDK and orchestration contract remain stable.
