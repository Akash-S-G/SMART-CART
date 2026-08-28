# SmartCart AI — Smart Grocery Cart

AI-powered grocery e-commerce with YOLO vision scanner, RAG recipe copilot (flan-t5-small), and full commerce flow. **1005 products** seeded locally, 24 tables, host PostgreSQL.

## Quick Start (Local — Host psql 5432)

```bash
# 1) Postgres — host psql (recommended, local only as requested)
psql -h /var/run/postgresql -U akash -c "SELECT 1"          # host running on 5432
PGPASSWORD=777 psql -h 127.0.0.1 -U smartcart_user -d smartcart -c "SELECT count(*) FROM products;" # 1005

# Docker alternative (if host psql unavailable)
docker run -d --name smartcart-postgres -e POSTGRES_USER=smartcart_user -e POSTGRES_PASSWORD=777 -e POSTGRES_DB=smartcart -p 5433:5432 postgres:16-alpine
# then use DATABASE_URL=postgresql+psycopg://smartcart_user:777@localhost:5433/smartcart

# 2) Backend
cd backend
cp .env.example .env   # edit DATABASE_URL to 5432 (host) or 5433 (docker)
uv sync                # or pip install -r requirements
uv run uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/healthz  # {"status":"ok"}
curl http://localhost:8000/readyz   # {"status":"ready"}
uv run pytest tests/test_api.py -q  # 5 passed

# 3) Frontend
cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm install
npm run dev            # http://localhost:5173
npm run build && npm run lint
npx playwright test --reporter=list  # 8/8 ✓
```

**Admin seed:** `admin@smartcart.ai / SmartCart@123`

## Environment

- `backend/.env.example` — local `5432` default, JWT, CORS, Cloudinary, Google OAuth, AI_SERVICE_URL, Supabase (paused, backup in `.env.supabase.bak`)
- `frontend/.env.example` — `VITE_API_URL`, `VITE_WS_URL` (http/ws for local, https/wss for deploy)

See `backend/.env` (gitignored) for working local `DATABASE_URL=postgresql+psycopg://smartcart_user:777@localhost:5432/smartcart`.

## Architecture

- **Backend:** FastAPI + SQLAlchemy, 24 tables (products, inventory, carts, orders, payments, reviews, etc.), JWT, rate-limit 1000/60s (`/static` excluded), YOLO lazy + Modal fallback `https://akash-yt3001--smartcart-ai-vision-fastapi-app.modal.run`
- **Frontend:** React 18 + Vite + TanStack Query + shadcn, code-split (150k gzip), `PAGE_SIZE 24` infinite scroll, `black/*` → tokens, dark mode, a11y
- **AI:** `/ai/detect` YOLO + `/ai/recipe` flan-t5-small 80M RAG, scanner accuracy tuned `CONF 0.35`, `MAX_DET 12`

## Features

- **Catalog:** categories, search, pagination, sort, filters, autocomplete `GET /products/autocomplete?q=milk`, barcode `GET /generate-barcode`
- **Commerce:** cart, wishlist, coupons (WELCOME50, SMART100, FREESHIP), checkout, orders, payments verify, slip PDF `GET /orders/{id}/slip`, cancel, tracking timeline, recently viewed, compare
- **User:** auth (register/login/refresh, Google OAuth), address book `POST/GET /addresses`, profile
- **Admin:** inventory management — `GET /inventory`, `GET /valuation`, `GET /low-stock`, `GET /{id}/transactions`, `PATCH /{id}` thresholds, `POST /{id}/adjust` with transaction log (`restock/adjustment/damaged/expired/return/sale`), bulk CSV, image upload, barcode, analytics `GET /analytics/dashboard`, customers, logs, WebSocket `/ws`
- **Inventory:** reorder_level, max_capacity, location per SKU, valuation, low/out alerts (`InventoryDashboardView`)

## Testing & Lint

```bash
cd backend && uv run pytest tests/test_api.py -q
cd frontend && npx playwright test --reporter=list
curl http://localhost:8000/products/autocomplete?q=butter  # ["Amul Butter"]
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/addresses
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/inventory/valuation
```

## Git Flow

`feat/*` branches, merge only after test (`pytest` + `playwright 8/8` + `curl`). Current: `feat/git-docs` → `main`. See `TASK.md` for tracker, changelog, and run notes. Host DB `127.0.0.1:5432` `smartcart_user:777/smartcart` (24 tables, 1005 products).

## Deploy

- Backend: Render/HF (set `DATABASE_URL` to Supabase pooler `6543` if needed)
- Frontend: Vercel (`VITE_API_URL`, `VITE_WS_URL`)
- CORS: `BACKEND_CORS_ORIGINS` includes `https://smart-cart-snowy.vercel.app` + localhost

