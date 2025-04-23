# Enable Guardrails

To enable Guardrails, you need to go to the frontend folder:
```bash
$ cd frontend
```

then go into the .env file and set the following environment variable:

```
ENABLE_GUARDRAILS_TOGGLE=true
```
If there is not already a `.env` file, there should be a `.env.example` file. Copy the `.env.example` file to .env and then edit the file to change the value of `ENABLE_GUARDRAILS_TOGGLE` to true.

Then, rebuild the frontend container and the guardrails will be togglable in the UI.

**Extra Notes:** When guardrails are disabled, the persona feature will be enabled. This is because personas allow for bypassing the guardrails in a way not intended. Turn off guardrails to play with personas!
