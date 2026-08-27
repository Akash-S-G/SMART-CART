# SmartCart AI — Task Tracker

> Workflow: Fix → Test locally (backend + frontend) → Mark implemented → Next task. Commit per major change.
> Testing: Playwright (E2E), Vitest/unit, FastAPI pytest, manual curl/http checks. Scalability: pagination, caching, rate-limit, chunking.

## Current Working Task
**T14 — Git & docs**  [IN_PROGRESS — local psql active, all 8 E2E pass]
- Switched to **local psql** `127.0.0.1:5432` `smartcart_user:777/smartcart` (host Postgres 16, 652 products, 16 cats) — removed Docker 5433 per your request. Fixed rate-limit 429 (`black/*` static now excluded, 100→1000), backfilled 20 missing `product_prices`+`inventory` (was `Product price not found`).

## Completed — Phase 1-4 (tested locally)
### Foundation & Reliability
- [x] **T1 — Backend boot & DB migrations**: `DB_AUTO_CREATE=True`, YOLO lazy guard, `orders.py` dedup + `/admin` ordering, `DATABASE_URL` `postgresql://smartcart_user:777@localhost:5432/smartcart` (host psql 16, was Docker 5433 per 652 products), `healthz` ✓, `readyz` ✓, `create_all` + admin seed `admin@smartcart.ai / SmartCart@123` ✓
- [x] **T2 — Auth**: `POST /auth/register` ✓, `POST /auth/login` ✓, `GET /auth/me` ✓, `POST /auth/refresh` ✓, brute-force 429 lockout ✓ (pytest 5/5), Google OAuth code exchange (real redirect, mock removed)
- [x] **T3 — Product catalog**: categories ✓, list/search/pagination/sort/filters ✓, get by id ✓, admin CRUD `POST/PUT/DELETE /products` ✓, bulk CSV ✓, image upload (Cloudinary fallback to `/static/uploads`) ✓, barcode `GET /generate-barcode` ✓, `putJson` import fixed

### Core Commerce
- [x] **T4 — Cart & Wishlist**: `GET /cart` ✓, `POST /cart/items` ✓, `PATCH /cart/items/{id}` ✓, `DELETE /cart/items/{id}` ✓, `GET/POST/DELETE /wishlist` ✓ (curl + UI)
- [x] **T5 — Coupons & Checkout**: `POST /coupons/validate` WELCOME50 50%→500, SMART100 flat 100, FREESHIP flat 40 ✓, `POST /orders/checkout` creates order, stock decrement, empty-cart guard ✓
- [x] **T6 — Orders & Payments**: `GET /orders` ✓, `GET /orders/{id}` ✓, `GET /orders/admin` ✓ (fixed shadowing), `PATCH /orders/{id}/cancel` ✓, `POST /payments` + `POST /payments/verify` → status `paid` ✓, `GET /orders/{id}/slip` PDF ✓ — full flow `register→add cart→checkout→pay→verify` via curl ✓
- [x] **T7 — Reviews**: `GET /products/{id}/reviews` ✓, `POST /products/{id}/reviews` ✓, `POST /products/{id}/reviews/{rid}/helpful` ✓

### AI & Analytics
- [x] **T8 — AI Vision scanner**: `/ai/detect` YOLO lazy + `AI_SERVICE_URL` Modal `https://akash-yt3001--smartcart-ai-vision-fastapi-app.modal.run` fallback ✓ (tested via UI, `detectImageApi` works; local YOLO disabled when no torch)
- [x] **T9 — Analytics dashboard**: `GET /analytics/dashboard` ✓ `{"total_orders":1,"total_revenue":1179,...}`, `GET /analytics/customers` ✓, `GET /analytics/logs` ✓, Recharts code-split (431k chunk)
- [x] **T10 — WebSocket live**: `/ws` `ConnectionManager` broadcast ✓ (manual wscat test)

### Frontend UX & Testing
- [x] **T11 — UI/UX audit**: index.css Geist/shadows/shimmer/reduced-motion, button gradient, navbar mobile drawer + scroll-lock/Esc/overlay, `black/*` → tokens, landing skeletons, collections sort responsive, checkout promo API — **crash `handleMockGoogleSignIn` fixed**, dark mode verified
- [x] **T12 — E2E suite**: `playwright.config.ts` + `e2e/smoke.spec.ts` 6/6 ✓ + `e2e/full-flow.spec.ts` 2/2 ✓ (register→browse→product→cart→checkout→payment→orders + wishlist/reviews) — total **8/8 ✓** (1.62.1, Chromium 1234)
- [x] **T13 — Scalability pass**: pagination `PAGE_SIZE 24` + infinite scroll, `vite manualChunks` (main 540k→150k gzip), **rate-limit 1000/60s + `/static` excluded** (was 100, hit 429 on image-heavy collections), `loading="lazy"`, `healthz/readyz`

## Queue — Remaining
- [ ] **T14 — Git & docs**: finalize README, `.env.example` for local (`DATABASE_URL=postgresql://smartcart_user:777@localhost:5433/smartcart`), seed instruction `./seed_products.sh --limit 20` or admin API seeding (done via curl for 8 products)

## Notes
- Local DB: **host psql** `127.0.0.1:5432` `smartcart_user:777/smartcart` (24 tables, 652 products) — backfilled 20 missing `product_prices`/`inventory` (was `Product price not found` on cart). Supabase backup `backend/.env.supabase.bak`.
- Playwright 8/8, pytest 5/5, build 150k gzip — all green after rate-limit fix.
- AI: Modal URL, no local CUDA.
- Google OAuth: fixed `GOOGLE_CLIENT_SECRET` missing attr (was 500 on `/auth/google-login`); now `code` exchange + fallback email works — verify `http://localhost:5173` in Console redirect URIs.

## How to Run Locally (now)
```bash
# postgres (local psql — host)
psql -h /var/run/postgresql -U akash -c "SELECT 1" # host running on 5432
# if needed: PGPASSWORD=777 psql -h 127.0.0.1 -U smartcart_user -d smartcart -c "SELECT count(*) FROM products;" # 652
# Docker alternative: docker run -d --name smartcart-postgres -e POSTGRES_USER=smartcart_user -e POSTGRES_PASSWORD=777 -e POSTGRES_DB=smartcart -p 5433:5432 postgres:16-alpine

# backend
cd backend && uv run uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/healthz # {"status":"ok"}
curl http://localhost:8000/readyz # {"status":"ready"}
uv run pytest tests/test_api.py -q # 5 passed
# seed more products if needed:
# ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email":"admin@smartcart.ai","password":"SmartCart@123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
# curl -s -X POST http://localhost:8000/products -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{"name":"Test","sku":"SKU-TEST","category_id":"...","price":99,"initial_stock":10}'

# frontend
cd frontend && npm run dev # http://localhost:5173
npm run build && npm run lint
npx playwright test --reporter=list # 8 passed
```

## Changelog
- 2026-08-27 — feat(ui): design-system refresh & chunk splitting (beefc49)
- 2026-08-27 — fix(backend): deduplicate orders routes, fix /admin shadowing, add flat coupons (3bbb6b1)
- 2026-08-27 — fix(frontend): remove undefined `handleMockGoogleSignIn` crash, add Playwright smoke 6/6 (fe4f11e)
- 2026-08-27 — feat(local): Docker 5433 → host psql 5432, full E2E 8/8, all backend flows via curl
- 2026-08-27 — fix(auth): GOOGLE_CLIENT_SECRET attr + rate-limit 1000 + /static exclude + backfill 20 prices/inventory (d75c7da)
