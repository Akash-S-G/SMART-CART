# SmartCart AI — Task Tracker

> Workflow: Fix → Test locally (backend + frontend) → Mark implemented → Next task. Commit per major change.
> Testing: Playwright (E2E), Vitest/unit, FastAPI pytest, manual curl/http checks. Scalability: pagination, caching, rate-limit, chunking.

## Current Working Task
**T1 — Backend boot & DB migrations**  [PARTIALLY VERIFIED — backend live but DB unreachable, need Supabase check]
- Fixed `DB_AUTO_CREATE=True` + YOLO lazy guard, orders dedup, putJson import, coupons WELCOME50/SMART100/FREESHIP
- Frontend builds ✓ (`vite build` 150k gzip, chunks split; `eslint` clean)
- Frontend dev server ✓ `http://localhost:5173` responding — Playwright smoke 6/6 passed after fixing `auth-modal.tsx:275` crash (`handleMockGoogleSignIn is not defined` removed)
- Backend: `uv sync` finished, `healthz` ✓ `{"status":"ok"}`, `readyz` ✗ `ENOTFOUND tenant/user postgres.gzxhqguflvitdtqkvlpq not found` (pooler 6543/5432 + direct all fail; Supabase project may be paused or password changed). `pytest tests/test_api.py` ✓ 5/5 via SQLite in-memory (healthz, readyz with SQLite, list_products, list_categories, brute-force lockout)
- Next: you to verify Supabase project `gzxhqguflvitdtqkvlpq` in `ap-southeast-1` — check Dashboard → Database → Connection pooling vs direct, reset password if needed, or switch to local Postgres/SQLite for dev. Will re-test `POST /auth/register` once DB reachable, then seed admin `admin@smartcart.ai / SmartCart@123`.

## Queue — To Be Completed (one at a time, test before moving)
### Phase 1 — Foundation & Reliability
- [ ] **T2 — Auth completeness**: register/login/refresh/logout/me, Google OAuth code exchange, brute-force 429 lockout, password change. Fix 500s. Test via `pytest` + curl.
- [ ] **T3 — Product catalog**: categories, list/search/pagination/sort/filters, get by id, admin CRUD, bulk CSV, image upload (cloudinary fallback to /static), barcode. Test via `TestClient` + frontend collections page.

### Phase 2 — Core Commerce
- [ ] **T4 — Cart & Wishlist**: add/update/remove/clear, wishlist add/remove, concurrency.
- [ ] **T5 — Coupons & Checkout**: validate coupons (now aligned), checkout creates order + stock decrement + empty-cart guard.
- [ ] **T6 — Orders & Payments**: list/get, admin list, cancel, create/verify payment, slip PDF. Full flow test: register→add cart→checkout→pay→verify.
- [ ] **T7 — Reviews**: list/create/helpful, verified_purchase, pagination.

### Phase 3 — AI & Analytics
- [ ] **T8 — AI Vision scanner**: `/ai/detect` & `/ai/detect-and-add` — YOLO local fallback + `AI_SERVICE_URL` (Modal). Test with sample image.
- [ ] **T9 — Analytics dashboard**: `/analytics/dashboard`, `/analytics/customers`, `/analytics/logs`, charts.
- [ ] **T10 — WebSocket live**: `/ws` broadcast, frontend reconnect.

### Phase 4 — Frontend UX & Testing
- [x] **T11 — UI/UX audit**: design-system refresh + crash fix `handleMockGoogleSignIn` → smoke 6/6 ✓, skeletons, responsive, dark mode; pending `axe` a11y full scan
- [x] **T12 — E2E suite (Playwright)**: `playwright.config.ts` + `e2e/smoke.spec.ts` (6 tests) installed (`@playwright/test` 1.62, browsers 1234/1228 cached 380M+390M), smoke ✓ 6/6; next: add full flow specs (auth → cart → checkout → orders, wishlist, scanner, admin) — currently blocked by DB, will run when DB reachable
- [ ] **T13 — Scalability pass**: pagination 24, infinite scroll, manualChunks ✓, rate-limit 100/60s, lazy images, charts code-split ✓, caching headers.

### Phase 5 — Release
- [ ] **T14 — Git & docs**: commits per major change (2 done), README + ENV examples.

## Completed
- [x] **T0 — Stabilize dev env** — root cause `DB_AUTO_CREATE=False` fixed, lazy YOLO, build verified
- [x] **FE-1 — Design-system refresh** (index.css Geist/shadows/shimmer, button gradient, card, manualChunks, navbar drawer, dark-mode tokens, skeletons, sort, promo API)
- [x] **BE-1 — Route & coupon fixes** (orders dedup + /admin ordering, coupons WELCOME50/SMART100/FREESHIP flat)
- [x] **T12-smoke — Playwright smoke 6/6** (landing, navbar modal, scanner, checkout guard, collections, dark mode) — crash `handleMockGoogleSignIn` fixed in `auth-modal.tsx`

## Notes & Questions for User
- DB BLOCKED: Supabase `gzxhqguflvitdtqkvlpq` pooler returns `ENOTFOUND tenant/user` on 6543 & 5432 + direct `db.*.supabase.co` NXDOMAIN — please check Dashboard: is project paused? Confirm `DATABASE_URL` password and pooler `postgres.<project>` vs `postgres` format. Alternative: run local Postgres `docker run -e POSTGRES_PASSWORD=... -p 5432:5432 postgres` and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smartcart` for dev.
- Playwright: you have it (1.61/1.62), installed `@playwright/test` + browsers (1234 390M + headless 114M) — smoke 6/6 done.
- AI: using `AI_SERVICE_URL` Modal, local torch guarded — no need for local CUDA.
- Need action: please verify/fix `backend/.env` `DATABASE_URL` then `curl /readyz` should return `{"status":"ready"}`.

## How to Run Locally (current)
```bash
# backend — you are installing in background; when done:
cd "backend" && uv run uvicorn app.main:app --reload --port 8000
# verify
curl http://localhost:8000/healthz; curl http://localhost:8000/readyz
uv run pytest -q   # uses SQLite in-memory, no DB needed

# frontend — already running
cd "frontend" && npm run dev  # http://localhost:5173
npm run build && npm run lint
```

## Changelog
- 2026-08-27 — feat(ui): design-system refresh & chunk splitting (beefc49)
- 2026-08-27 — fix(backend): deduplicate orders routes, fix /admin shadowing, add flat coupons (3bbb6b1)
- 2026-08-27 — fix(frontend): remove undefined `handleMockGoogleSignIn` crash, add Playwright smoke 6/6, DB诊断 pooler ENOTFOUND
