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
