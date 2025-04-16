# Frontend

Next.js frontend component for the Virtual Teaching Assistant application.

## Prerequisites

Before running this application, ensure you have:

- [Node.js](https://nodejs.org/) (v18 or higher)
- [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)
- Docker (if running with Docker)
- Access to backend services:
  - RAG server (default: http://localhost:8081)
  - Ingestion server (default: http://localhost:8082)
  - Canvas API proxy server (default: http://localhost:8012)

## Getting Started

### Running Locally

1. cd into this frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm i --legacy-peer-deps
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Modify variables as needed (see [Environment Variables](#environment-variables) section)

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

### Building for Production

To create a production build:

```bash
npm run build
npm start
```

## Running with Docker

This application includes a multi-stage Dockerfile to optimize build and runtime performance.

1. Configure your environment variables in `.env` file (see [Environment Variables](#environment-variables) section).

2. Build the Docker image:
   ```bash
   docker build -t frontend .
   ```

3. Run the container with environment variables:
   ```bash
   docker run -p 3000:3000 --env-file .env frontend
   ```
   
   Alternatively, specify environment variables directly:
   ```bash
   docker run -p 3000:3000 -e ENABLE_GUARDRAILS_TOGGLE=true frontend
   ```

4. Access the application at [http://localhost:3000](http://localhost:3000).

## Backend Dependencies

The frontend expects the following backend services to be running:

- RAG Server at http://localhost:8081
- Ingestion Server at http://localhost:8082
- Canvas API Proxy at http://localhost:8012

## Environment Variables

Configure these variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_GUARDRAILS_TOGGLE` | Enable/disable the guardrails toggle in the UI | `false` |

When `ENABLE_GUARDRAILS_TOGGLE` is set to `false`, the toggle will be replaced with a message directing users to the `guardrails_toggle.md` file for instructions on enabling it.

To enable the guardrails toggle:
1. Open the `.env` file
2. Set `ENABLE_GUARDRAILS_TOGGLE=true`
3. Restart the server

## Available Scripts

- `npm run dev`: Run the development server with turbopack
- `npm run build`: Build the application for production
- `npm start`: Start the production server
- `npm run lint`: Run ESLint for code quality