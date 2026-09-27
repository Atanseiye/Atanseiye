# AccessFlow architecture

```text
Bank mobile/web app
        │
        │ @accessflow/web / REST
        ▼
AccessFlow Experience API
 ├── Accessibility Profile
 ├── Language / N-ATLAS Gateway
 ├── Intent Orchestrator
 ├── Confirmation & Risk Boundary
 └── Accessibility Telemetry
        │
        ▼
Bank Adapter Interface
 ├── Customer / account read APIs
 ├── Beneficiary resolution
 ├── Existing authentication / step-up auth
 ├── Payment execution
 └── Card / fraud / support APIs
```

## Trust boundaries

1. The language model may interpret a request but cannot authoritatively state bank data.
2. Bank state is retrieved from bank APIs/adapters.
3. Transfer previews are server-created and expire.
4. State-changing actions require explicit confirmation and authentication.
5. Idempotency protects retry paths from duplicate debits.
6. Accessibility analytics should aggregate interaction preferences and journey outcomes, not diagnoses.

## Model provider boundary

`NAtlasProvider.parse()` returns a strict `BankingIntent`. `MockNAtlasProvider` makes the public demo deterministic. `OpenAICompatNAtlasProvider` is the production-shaped integration point for a hosted N-ATLAS endpoint.


## Accessible customer lifecycle

AccessFlow starts before authentication:

```text
Anonymous visitor
   ↓
Choose language + accessibility preferences
   ↓
Registration details
   ↓
Accessible contact verification
   ↓
Flexible KYC path
   ├── guided camera with audio/captions
   ├── document + review
   └── accessible assisted review
   ↓
Bank-controlled PIN / passkey / biometric setup
   ↓
Plain-language consent
   ↓
Explicit account activation
   ↓
Accessibility profile carried into authenticated banking
```

The server enforces each transition. The UI cannot simply skip KYC, authentication setup or consent.
