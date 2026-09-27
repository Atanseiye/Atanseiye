# Security model

AccessFlow is an interaction/orchestration layer, not a core banking system.

## Required invariants

- An LLM cannot execute financial operations directly.
- A transfer with missing/ambiguous beneficiary or amount cannot proceed.
- Confidence below the configured threshold cannot create an executable preview.
- Server-side balance, beneficiary, limit and policy checks are authoritative.
- The customer must see a transaction preview before money moves.
- State-changing operations require explicit confirmation and authentication.
- Transfer previews expire and may execute only once.
- Idempotency keys prevent duplicate execution on safe retries.
- Raw credentials/PINs are never sent to the language model.
- Frontend-provided balances, names and transaction state are never trusted.

## Production additions

OIDC/session binding, FIDO2/passkeys or bank step-up auth, encrypted audit storage, bank-grade rate limiting, fraud/risk hooks, WAF, mTLS/private networking, secrets management, immutable audit trails, penetration testing, data-retention policy, NDPR controls, and bank-specific approval workflows.


## Registration and KYC safeguards

- Accessibility preferences can be selected before authentication; they are not authentication factors.
- The public demo explicitly requires synthetic data and is not an identity provider.
- The public onboarding response never returns the full submitted demo identity number; only the final four characters are retained in session state.
- Contact verification must succeed before identity verification.
- Security setup must succeed before consent and activation.
- Weak demo PINs are rejected; production banks should use their own passkey/FIDO/device authentication policies.
- Consent is explicit and includes separate acknowledgement for accessibility-preference processing.
- Production KYC evidence must flow to the bank/approved identity provider, not through the N-ATLAS language model.
