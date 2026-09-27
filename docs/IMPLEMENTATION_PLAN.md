# Implementation roadmap

## Competition build

1. Complete five-language text journeys and code-switch evaluation.
2. Wire the official/approved N-ATLAS endpoint when credentials are available.
3. Add N-ATLAS ASR or approved speech adapter; keep typed fallback.
4. Validate TalkBack, VoiceOver/NVDA and keyboard-only journeys.
5. Expand the evaluation corpus to at least 500 utterances (100 per language), plus code-switched and adversarial cases.
6. Record the three hero persona demonstrations.
7. Measure intent accuracy, entity extraction, clarification rate and unsafe-action rate.

## Pilot integration

1. Implement `BankAdapter` against Zenith sandbox APIs.
2. Bind AccessFlow profile to bank customer identity and consent.
3. Use bank-native authentication/step-up flows.
4. Add Postgres/Redis, encrypted audit events and observability.
5. Perform accessibility usability tests with target users.
6. Complete security/threat modeling and compliance review.

## Production

Ship AccessFlow as web/mobile SDKs plus managed orchestration APIs. The bank keeps its customer, auth, ledger, payments and fraud systems.
