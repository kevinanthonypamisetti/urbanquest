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

The service exposes `GET /`, `GET /health`, and `POST /chat`. Set `MAPS_PROVIDER=google`
and `GOOGLE_MAPS_API_KEY` to resolve itinerary place queries and routes through Google
Places/Routes. If the key is absent (or the provider is not selected), it explicitly
falls back to the deterministic demo provider.

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

## Authentication

The frontend exposes `/login` and `/signup` with Google OAuth and email/mobile
OTP entry points. The FastAPI service exposes `/auth/request-code`, `/auth/verify`,
`/auth/me`, `/auth/logout`, and `/auth/google`. Configure `DATABASE_URL`,
`GOOGLE_OAUTH_URL`, and an OTP delivery provider before production deployment.
The PostgreSQL baseline schema is in [`urbanquest-ai/schema.sql`](./urbanquest-ai/schema.sql).
During local development, `DEVELOPMENT_OTP=123456` is accepted by the verification
endpoint. Production sessions use an HttpOnly, SameSite=Lax cookie and never store
passwords or plaintext OTPs.

For Google sign-in, set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`GOOGLE_REDIRECT_URI` (for example `https://your-render-service.onrender.com/auth/google/callback`),
and `FRONTEND_URL` on Render. Add the same callback URL to the Google Cloud OAuth
client's authorized redirect URIs.

For production email OTP delivery, set `RESEND_API_KEY` and `AUTH_FROM_EMAIL` on
the Render service, and set `VITE_AUTH_API_URL` in Vercel to the Render URL plus
`/auth`. The sender domain must be verified in Resend; the default sender is only
for development/testing.

## Supabase frontend setup

Create a Supabase project, then run [`supabase/schema.sql`](./supabase/schema.sql)
in the SQL editor. Add the project URL and public anon key to Vercel:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-public-anon-key
```

The planner is protected by Supabase Auth. Users must sign up or sign in before
using the planner, and the chat agent uses the existing `/chat` API with the
current trip context.

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
