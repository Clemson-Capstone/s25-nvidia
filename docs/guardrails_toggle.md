# Enable Guardrails

To enable Guardrails, you need to go to the .env file and set the following environment variable:

```
ENABLE_GUARDRAILS_TOGGLE=true
```

Then, rebuild the frontend container and the guardrails will be togglable in the UI.

**Extra Notes:** When guardrails are disabled, the persona feature will be enabled. This is because personas allow for bypassing the guardrails in a way not intended. Turn off guardrails to play with personas!
