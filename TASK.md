# SmartCart AI — Task Tracker

> Workflow: Fix → Test locally (backend + frontend) → Mark implemented → Next task. Commit per major change.
> Testing: Playwright (E2E), Vitest/unit, FastAPI pytest, manual curl/http checks. Scalability: pagination, caching, rate-limit, chunking.

## Current Working Task
**T0 — Stabilize local dev environment & fix critical backend boot bug**  [IN_PROGRESS]
- Backend: DB tables missing (`relation "users" does not exist`) because `DB_AUTO_CREATE=False` + `ENVIRONMENT=development` skips `init_db()`. Need enable auto-create for dev OR add alembic upgrade path.
- Frontend already runs on :5173, but backend :8000 is down due to broken .venv (uv sync incomplete, torch/cuda 1GB downloads).
- Action: fix config, re-sync with longer timeout or `uv sync --no-install-torch`? ensure `backend/.venv` works. Verify `GET /health`, `POST /auth/register`.
- Tests: `curl` health, register, login; `pytest backend/tests`; `npm run build` (done) ; `npm run lint`.

## Queue — To Be Completed (ordered, one at a time)
### Phase 1 — Foundation & Reliability
- [ ] **T1 — Backend boot & DB migrations**: Fix `DB_AUTO_CREATE` default, test lifespan, ensure seed admin `admin@smartcart.ai / SmartCart@123` works. Add `alembic upgrade head` fallback.
- [ ] **T2 — Auth completeness**: Verify register/login/refresh/logout/me, Google OAuth code exchange, brute-force lockout, password change. Fix any 500s. Test with http files + pytest.
- [ ] **T3 — Product catalog API**: categories, list/search/pagination/sort/filters, get by id, admin CRUD, bulk upload, image upload (cloudinary), barcode. Ensure `PUT /products/{id}` missing import `putJson` fixed in frontend `api.ts`.

### Phase 2 — Core Commerce
- [ ] **T4 — Cart & Wishlist**: add/update/remove/clear, wishlist add/remove, concurrency tests.
- [ ] **T5 — Coupons & Checkout**: validate coupons, checkout creates order, empty-cart guard, stock decrement. Fix `checkout.tsx` optimistic promo chip bug (done partially, need test).
- [ ] **T6 — Orders & Payments**: list/get, admin list, cancel, create/verify payment, slip PDF generation. Test full flow register→add cart→checkout→pay→verify.
- [ ] **T7 — Reviews**: list/create/helpful, verified_purchase flag, pagination.

### Phase 3 — AI & Analytics
- [ ] **T8 — AI Vision scanner**: `/ai/detect` & `/ai/detect-and-add` — YOLO + modal fallback. Ensure `AI_SERVICE_URL` works, test with sample image.
- [ ] **T9 — Analytics dashboard**: `/analytics/dashboard`, `/analytics/customers`, `/analytics/logs` — verify aggregation queries, charts.
- [ ] **T10 — WebSocket live**: `/ws` broadcast, frontend reconnect.

### Phase 4 — Frontend UX & Testing
- [ ] **T11 — UI/UX audit fixes**: Already did design-system refresh (index.css, button/card, navbar, AppShell). Need verify responsive, dark mode, a11y (axe), skeletons.
- [ ] **T12 — E2E suite (Playwright)**: Install & write specs: auth, browse → product → cart → checkout → order; scanner upload; admin; wishlist. Run `npx playwright test`.
- [ ] **T13 — Scalability pass**: pagination (PAGE_SIZE 24), infinite scroll, manualChunks (done), rate-limit (100/60s), caching headers, lazy image loading, charts code-split.

### Phase 5 — Release
- [ ] **T14 — Git & docs**: Commit per major change (not per trivial edit), update README, ENV examples, seed script.

## Completed
- [x] Frontend design-system refresh (index.css tokens, button gradient, card, vite manualChunks, navbar mobile drawer, modal a11y, dark-mode `black/*` fixes, landing skeletons, collections sort, checkout promo API, copilot dialog) — build passes, chunks split 540k→150k gzip main.

## Notes & Questions for User
- Q: Do you want torch/CUDA fully installed locally or use `AI_SERVICE_URL` (Modal) to avoid 2GB download? Default will keep Modal.
- Q: Playwright browsers download ~500MB — proceed with `npx playwright install`?
- Q: Supabase DB is remote (`aws-0-ap-southeast-1.pooler.supabase.com`) — ok to run `init_db()` against it? Will create tables if missing.
- Need: `CLOUDINARY_*`, `GOOGLE_CLIENT_ID` present — keep as is.

## How to Run Locally
```bash
# backend
cd "backend" && uv sync              # first time ~5min due to torch
uv run uvicorn app.main:app --reload --port 8000

# frontend
cd "frontend" && npm install && npm run dev  # http://localhost:5173

# tests
uv run pytest -q
npm run build && npm run lint
npx playwright test --reporter=list
```

## Changelog (major commits)
- 2026-08-27 — feat(ui): design-system refresh & chunk splitting
