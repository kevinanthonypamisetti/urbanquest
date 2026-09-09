# UrbanQuest

The main product is a React/Vite frontend. The first Python orchestration service
is in [`urbanquest-ai/`](./urbanquest-ai/).

## Run the AI service

```bash
cd urbanquest-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The service exposes `GET /health` and `POST /chat`. The demo maps provider is
deliberately deterministic so the service can run without external API keys.

## Deployment walkthrough

The repository includes [`render.yaml`](./render.yaml) for the Python API.

1. Push this repository to GitHub.
2. In Vercel, import the repository and deploy the Vite frontend.
3. Set `VITE_AI_API_URL` in Vercel to the Render URL plus `/chat`.
4. In Render, create the service from `render.yaml`.
5. Set Render's `CORS_ORIGINS` to the exact Vercel URL, then redeploy both services.
6. Verify the Render `/health` endpoint and submit a concierge request from the Vercel site.

The current deployment uses the deterministic demo maps provider. Real map
providers should be added only after their server-side API keys are configured.

## Run the frontend

```bash
npm install
npm run dev
```

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
