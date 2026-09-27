# National-level demo script

## Opening — 20 seconds

"Digital banking can be technically available and still be inaccessible. AccessFlow is an integration layer that lets a bank adapt the same banking journey to a customer's language and preferred way of interacting — without replacing core banking."

## Persona 1 — Ade: blind + Yoruba-first

1. Load Ade's profile.
2. Show that voice guidance, screen-reader optimization, large controls and extra time activate.
3. Use: `Mo fẹ transfer 10k si Adewale`.
4. Emphasize code-switch handling.
5. Show beneficiary/bank/account/amount confirmation.
6. Explain that no money has moved yet.
7. Confirm with PIN and show successful debit.

## Persona 2 — Ifeoma: deaf + Pidgin-first

1. Load Ifeoma's profile: captions, text-first, Easy Banking.
2. Ask: `Why my transaction still dey pending?`
3. Show concise Pidgin status with no audio dependency.
4. Open support through text.

## Persona 3 — Musa: motor-impaired + Hausa-first

1. Load Musa's profile: voice, large controls, keyboard/switch support, extended timeouts.
2. Ask: `Aika 5k zuwa Amina`.
3. Complete the same secured transfer path without requiring precise touch.

## Bank view

Switch to `/admin` and show language usage, interaction mode, journey signals, support/fraud events. Explain that the production version helps product teams identify accessibility friction without storing disability diagnoses as analytics labels.

## Close

"AccessFlow does not ask a bank to rebuild banking. It gives the bank one integration layer for accessibility, Nigerian-language interaction, safe orchestration and measurable inclusion."


## Registration demo — before the three usage personas

1. Open `/register` while signed out.
2. Emphasize that language and accessibility controls are available **before any personal details are requested**.
3. Choose a Nigerian language and enable voice guidance / captions / large controls / Easy Banking.
4. Use the synthetic prefilled registration data.
5. Demonstrate the OTP in both visible and spoken form.
6. On KYC, show three equivalent paths instead of a mandatory visual-only selfie flow.
7. Explain that the demo backend retains only the last four characters of the synthetic identity number.
8. Configure PIN/passkey preference and explicitly state that voice control is not voice authentication.
9. Review the plain-language consent summary.
10. Activate the account and show that the accessibility profile is already present on the banking dashboard.
11. Switch to `/admin` and show the onboarding funnel alongside post-login accessibility metrics.
