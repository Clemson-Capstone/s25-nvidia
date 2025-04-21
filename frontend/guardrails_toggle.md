# Enabling the Guardrails Toggle

The guardrails toggle is disabled by default in this application. Follow these steps to enable it:

1. Open the `.env` file in the root directory of the frontend project.
2. Change the `ENABLE_GUARDRAILS_TOGGLE` environment variable from `false` to `true`:
   ```
   ENABLE_GUARDRAILS_TOGGLE=true
   ```
3. Save the file and restart the development server:
   ```bash
   npm run dev
   ```
   
   Or if you're using Docker, rebuild and restart the container:
   ```bash
   docker build -t frontend .
   docker run -p 3000:3000 frontend
   ```

## Why are guardrails disabled?

Guardrails are an important safety feature that help ensure the LLM behaves responsibly. The toggle is disabled by default to prevent accidental disabling of these safety measures.

## Understanding Guardrails

When enabled, guardrails provide several protections:

- Prevent harmful, unethical, or inappropriate responses
- Filter out toxic or offensive content
- Ensure responses align with the intended use of the application as a teaching assistant

Only enable the toggle if you need to test the application's behavior with guardrails disabled for development or testing purposes.