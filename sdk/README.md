# @accessflow/web

A thin bank-integration SDK for AccessFlow. The SDK intentionally does **not** replace the bank's authentication, customer record, ledger or core banking system.

```ts
import { AccessFlow } from '@accessflow/web';

const accessFlow = new AccessFlow({
  baseUrl: 'https://accessflow.example.com',
  token: bankSessionToken,
});

const profile = await accessFlow.getProfile();
const response = await accessFlow.assist({
  text: 'Abeg send 5k give Chinedu',
  language_hint: profile.primary_language,
  interaction_mode: 'text'
});
```

State-changing financial operations remain subject to the bank's deterministic validation, explicit confirmation and authentication.


## Pre-login onboarding

Accessibility begins before authentication. A bank can start registration with customer-controlled interaction preferences:

```ts
const session = await accessFlow.startOnboarding({
  primary_language: 'yo-NG',
  voice_guidance: true,
  screen_reader: true,
  large_targets: true,
  easy_banking: true,
});

// Server-enforced stages then cover registration, contact verification,
// accessible identity verification, bank-controlled security, consent and activation.
```

The SDK does not replace the bank's KYC/identity provider or authentication system; those remain authoritative adapters in production.
