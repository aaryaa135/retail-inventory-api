<p align="center">
  <h1 align="center">🛒 Retail Inventory Management API</h1>
  <p align="center"><b>Production-grade REST API — FastAPI + PostgreSQL + SQLAlchemy 2.0 + Pydantic v2 + Alembic + TDD</b></p>
  <p align="center"><i>SKU-unique catalog • Stock-aware orders • Low-stock alerts • 52 tests • Dockerized • Interview-ready</i></p>
</p>

<p align="center">
  <a href="https://github.com/aaryaa135/retail-inventory-api/actions"><img src="https://img.shields.io/github/actions/workflow/status/aaryaa135/retail-inventory-api/ci.yml?branch=main&label=CI&logo=github" alt="CI"/></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-DD2C00?logo=sqlalchemy" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="Postgres"/>
  <img src="https://img.shields.io/badge/tests-52%20passing-brightgreen?logo=pytest" alt="Tests"/>
  <img src="https://img.shields.io/badge/coverage-95%25-brightgreen" alt="Coverage"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License"/>
  <img src="https://img.shields.io/badge/code_style-black-000000" alt="Black"/>
</p>

<p align="center">
  <b>Docker:</b> <code>http://localhost:8001/docs</code> &nbsp;|&nbsp; <b>Local:</b> <code>http://localhost:8000/docs</code> &nbsp;|&nbsp; <b>Health:</b> <code>/health</code>
</p>

---

## 📑 Table of Contents
- [Why This Repo Stands Out](#-why-this-repo-stands-out)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [API Endpoints](#-api-endpoints)
- [Quick Start](#-quick-start)
- [Environment](#-environment)
- [Usage Examples](#-usage-examples)
- [Testing (52 Tests)](#-testing-52-tests)
- [Migrations](#-migrations)
- [Project Structure](#-project-structure)
- [Production Hardening Checklist](#-production-hardening-checklist)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🌟 Why This Repo Stands Out

| What Interviewers Look For | How This Repo Nails It |
|---|---|
| **No `create_all` in prod** | `app/main.py:14` uses `lifespan` + `AUTO_CREATE_TABLES` + retry + `alembic/versions/001_initial.py:1` |
| **Money = `Numeric`, not `Float`** | `app/models.py:29,51,64` `Numeric(10,2)` — no rounding bugs |
| **Race-condition handling** | `app/routers/orders.py:19` `with_for_update()` + duplicate `product_id` `400` |
| **FK delete = `409` not `500`** | `app/routers/categories.py:47` / `products.py:66` guard + `ondelete` `RESTRICT/SET NULL/CASCADE` |
| **Pydantic v2 clean** | `model_dump()` + `ConfigDict` + `json_schema_extra` (0 warnings, `52 passed`) |
| **52 tests, not 40** | `categories 11 + products 17 + inventory 13 + orders 11` with `TestClient` override `app/tests/conftest.py:23` |
| **Docker + CI** | `docker-compose.yml:21` `8001:8000` (avoids `authforge-api` collision) + `.github/workflows/ci.yml:1` `ruff/black/pytest --cov` |

> **One-line pitch:** *“FastAPI + Postgres with stock-invariant preserved on `422`, sorted low-stock alerts, and row-level locking — TDD’d, linted, migrated, and dockerized.”*

---

## 🏗 Architecture

### System Diagram
```mermaid
graph TD
  Client -->|HTTP| API[FastAPI 0.115<br/>app/main.py:32<br/>CORS + lifespan]
  API --> R1[Categories<br/>/api/v1/categories]
  API --> R2[Products<br/>/api/v1/products<br/>?search & paginated]
  API --> R3[Inventory<br/>/api/v1/inventory<br/>low-stock]
  API --> R4[Orders<br/>/api/v1/orders<br/>with_for_update]
  R1 & R2 & R3 & R4 --> DB[(PostgreSQL 16 / SQLite)]
  DB --> Alembic[Alembic 1.13<br/>001_initial]
```

### ER Diagram
```mermaid
erDiagram
  Category ||--o{ Product : has
  Product ||--|| Inventory : tracked_by
  Product ||--o{ OrderItem : ordered_in
  Order ||--o{ OrderItem : contains
  Category { int id PK; string name UK; string description; datetime created_at }
  Product { int id PK; string sku UK; string name; Numeric price; int category_id FK }
  Inventory { int id PK; int product_id FK UK; int quantity; int low_stock_threshold }
  Order { int id PK; enum status; Numeric total_amount; datetime created_at }
  OrderItem { int id PK; int order_id FK; int product_id FK; int quantity; Numeric unit_price }
```

* **DB URL:** `app/database.py:9` `DATABASE_URL` → `postgresql://retail:retail@db:5432/retail` (Docker) / `sqlite:///./retail_inventory.db` (fallback)
* **Engine:** `check_same_thread=False` only for SQLite `app/database.py:14`, pool `NullPool` for Alembic `alembic/env.py:22`

---

## 🧱 Tech Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| **API** | FastAPI + Uvicorn | `0.115.0 / 0.30.6` | Auto OpenAPI, `TestClient` via `httpx 0.27.2` |
| **ORM** | SQLAlchemy | `2.0.35` | `declarative_base` from `sqlalchemy.orm`, `Numeric`, `with_for_update` |
| **Validation** | Pydantic | `2.9.2` | `ConfigDict`, `Field(gt/ge)`, `json_schema_extra` |
| **DB** | PostgreSQL 16 / SQLite | `psycopg2-binary 2.9.9` | Prod + dev/test parity |
| **Migrations** | Alembic | `1.13.3` | `001_initial` + `stamp head` |
| **Tests** | pytest + pytest-asyncio | `8.3.3 / 0.24.0` | `TestClient` + `app.dependency_overrides[get_db]` |
| **Quality** | Ruff + Black | `pyproject.toml:1` | CI: `ruff check` + `black --check` |
| **Infra** | Docker + Compose | `python:3.11-slim` | `8001:8000` avoids host `8000` conflict |

---

## ✨ Features

| Domain | What Works | File Highlight |
|---|---|---|
| **Products** | CRUD, SKU unique `409`, `?search` (ilike name\|sku), `?category_id`, `?skip/limit` 1-100, delete blocked if orders exist | `app/routers/products.py:12,24,66` |
| **Categories** | CRUD, name unique `409`, delete blocked if products exist | `app/routers/categories.py:14,47` |
| **Inventory** | 1:1 product, `409` duplicate, `is_low_stock = qty <= threshold` computed | `app/routers/inventory.py:21,54` |
| **Low-Stock Alerts** | `GET /low-stock?threshold_override=50`, sorted asc, `shortage = threshold - qty` | `app/routers/inventory.py:25-45` |
| **Orders** | Dedup `400`, `404` product, `400` no inventory, `422` insufficient stock, stock deducted atomically, `total_amount` snapshot, cancel restores | `app/routers/orders.py:13-22,84` |
| **Health** | `GET /` + `GET /health` | `app/main.py:38-44` |

---

## 🔌 API Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| `GET` | `/` | Root | `200` | — |
| `GET` | `/health` | Health | `200 {"status":"healthy"}` | — |
| `POST` | `/api/v1/categories/` | Create category | `201` | `409` dup, `422` empty name |
| `GET` | `/api/v1/categories/` | List categories | `200` | — |
| `GET` | `/api/v1/categories/{id}` | Get category | `200` | `404` |
| `PUT` | `/api/v1/categories/{id}` | Update | `200` | `404` |
| `DELETE` | `/api/v1/categories/{id}` | Delete (blocked if products) | `204` | `404`, `409` |
| `POST` | `/api/v1/products/` | Create product | `201` | `409` SKU, `404` category, `422` price |
| `GET` | `/api/v1/products/?search=&category_id=&skip=&limit=` | List + filter | `200` | — |
| `GET` | `/api/v1/products/{id}` | Get product | `200` | `404` |
| `PUT` | `/api/v1/products/{id}` | Update | `200` | `404` |
| `DELETE` | `/api/v1/products/{id}` | Delete (blocked if orders) | `204` | `404`, `409` |
| `POST` | `/api/v1/inventory/` | Create inventory | `201` | `404` product, `409` dup, `422` negative qty |
| `GET` | `/api/v1/inventory/` | List all | `200` | — |
| `GET` | `/api/v1/inventory/low-stock?threshold_override=` | Alerts sorted | `200` | — |
| `GET` | `/api/v1/inventory/{product_id}` | Get by product | `200` | `404` |
| `PUT` | `/api/v1/inventory/{product_id}` | Update qty/threshold | `200` | `404` |
| `POST` | `/api/v1/orders/` | Create order (stock check) | `201` | `400` dup/no-inventory, `404` product, `422` stock |
| `GET` | `/api/v1/orders/` | List orders | `200` | — |
| `GET` | `/api/v1/orders/{id}` | Get order | `200` | `404` |
| `PATCH` | `/api/v1/orders/{id}/cancel` | Cancel + restore stock | `200` | `404`, `400` already cancelled |

OpenAPI: `/openapi.json` · Swagger: `/docs` · ReDoc: `/redoc`

---

## 🚀 Quick Start

### Option A — Docker (recommended, cross-platform) ⭐

```bash
cp .env.example .env          # or create .env with DATABASE_URL
docker compose up --build     # API http://localhost:8001/docs , Postgres 5432
docker compose exec api alembic current  # → 001 (head) already stamped
# For fresh DB: docker compose down -v && docker compose up -d && docker compose exec api alembic upgrade head
```

### Option B — Local venv

```powershell
# Windows
setup.bat                     # venv + pip install -r requirements.txt + pytest (52 tests)
# or manually:
python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000/docs
```

```bash
# Linux / Mac
make setup    # venv + install + test
make test     # pytest -v (52 tests)
make run      # uvicorn --reload 8000
make docker-up  # compose 8001
```

> **Port note:** Docker uses `8001:8000` `docker-compose.yml:21` because `8000` is taken by `authforge-api` on this host. Local `uvicorn` still uses `8000`.

---

## 🔧 Environment

`.env.example:1`:
```
DATABASE_URL=postgresql://retail:retail@localhost:5432/retail
# Docker:   postgresql://retail:retail@db:5432/retail  (docker-compose.yml:22)
# Fallback: sqlite:///./retail_inventory.db
```
`app/database.py:14` sets `check_same_thread=False` only for SQLite. `app/main.py:14` respects `AUTO_CREATE_TABLES=true` (dev) / `false` (prod → use Alembic).

---

## 💻 Usage Examples

<details>
<summary><b>curl (8001 for Docker, 8000 for local)</b></summary>

```bash
# 1. Category
curl -X POST http://localhost:8001/api/v1/categories/ \
  -H "Content-Type: application/json" -d '{"name":"Electronics","description":"Tech"}'
# → {"id":1,"name":"Electronics",...}

# 2. Product
curl -X POST http://localhost:8001/api/v1/products/ \
  -H "Content-Type: application/json" -d '{"name":"Sony TV","sku":"ST-001","price":199,"category_id":1}'

# 3. Inventory
curl -X POST http://localhost:8001/api/v1/inventory/ \
  -H "Content-Type: application/json" -d '{"product_id":1,"quantity":50,"low_stock_threshold":10}'

# 4. Order (deducts stock, 422 if insufficient)
curl -X POST http://localhost:8001/api/v1/orders/ \
  -H "Content-Type: application/json" -d '{"items":[{"product_id":1,"quantity":2}]}'
# → {"status":"confirmed","total_amount":398.0,...}

# 5. Low-stock (with override)
curl "http://localhost:8001/api/v1/inventory/low-stock?threshold_override=50"

# 6. Cancel (restores stock)
curl -X PATCH http://localhost:8001/api/v1/orders/1/cancel

# 7. Delete guards (409 not 500)
curl -X DELETE http://localhost:8001/api/v1/categories/1
# → {"detail":"Cannot delete category with existing products"}
```

</details>

<details>
<summary><b>Python (httpx)</b></summary>

```python
import httpx
base = "http://localhost:8001"
cat = httpx.post(f"{base}/api/v1/categories/", json={"name":"Books"}).json()
prod = httpx.post(f"{base}/api/v1/products/", json={"name":"P1","sku":"P1-001","price":10.5,"category_id":cat["id"]}).json()
inv = httpx.post(f"{base}/api/v1/inventory/", json={"product_id":prod["id"],"quantity":5}).json()
order = httpx.post(f"{base}/api/v1/orders/", json={"items":[{"product_id":prod["id"],"quantity":2}]}).json()
print(order["total_amount"])  # 21.0
```

</details>

<details>
<summary><b>PowerShell</b></summary>

```powershell
Invoke-RestMethod http://localhost:8001/health
$cat = Invoke-RestMethod -Uri http://localhost:8001/api/v1/categories/ -Method Post -ContentType "application/json" -Body '{"name":"Toys"}'
```

</details>

---

## 🧪 Testing (52 Tests)

```
pytest.ini:2 → testpaths = app/tests
conftest.py:6 → sys.path fix for Windows
app/tests/conftest.py:8 → sqlite file test_retail.db + app.dependency_overrides[get_db] = override_get_db
```

| Suite | File | Tests | What’s Covered |
|---|---|---|---|
| Categories | `test_categories.py:1` | **11** | create 409/422, list/get 404, update, delete 204/409/404 |
| Products | `test_products.py:1` | **17** | create 409/404/422, get 404, list/search/filter/pagination, update, delete |
| Inventory | `test_inventory.py:1` | **13** | create 404/409/422, update threshold, `is_low_stock` edge, low-stock alerts sorted/shortage/override |
| Orders | `test_orders.py:1` | **11** | deduct 201, 422 insufficient (stock not deducted), 404, total calc, cancel restore/400 double/404, list/get |

```bash
pytest app/tests/ -v                          # 52 passed, 0 warnings (was 6, now fixed)
pytest app/tests/ -v --cov=app --cov-report=term-missing
pytest app/tests/test_categories.py -v
pytest app/tests/test_orders.py -k cancel -v
# In Docker:
docker compose exec api pytest app/tests/ -v
```

**CI:** `.github/workflows/ci.yml:1` → `ubuntu-latest` + `setup-python 3.11` + `pip install ruff black` + `ruff check app/` + `black --check app/` + `pytest --cov`

---

## 🗃 Migrations

```bash
alembic current              # 001 (head) — already stamped in Docker
alembic upgrade head         # fresh DB: creates all tables (001_initial)
alembic downgrade -1
alembic revision --autogenerate -m "add column"
# Existing DB that was create_all'd: alembic stamp head (already done)
```

* `alembic/env.py:12` reads `DATABASE_URL` + imports `app.models` for autogenerate.
* `app/main.py:14` `lifespan` has retry on `could not translate host name "db"` (10×2s) — dev fallback. For prod set `AUTO_CREATE_TABLES=false`.

---

## 📂 Project Structure

```
retail-inventory-api/
├── app/
│   ├── main.py              # FastAPI + lifespan (retry) + CORSMiddleware  app/main.py:32
│   ├── database.py          # engine / SessionLocal / Base (sqlalchemy.orm) app/database.py:3
│   ├── models.py            # 5 models + OrderStatus, Numeric(10,2), ondelete  app/models.py:29,51
│   ├── schemas.py           # Pydantic v2 ConfigDict, Field(gt/ge)            app/schemas.py:18,41
│   ├── routers/
│   │   ├── categories.py    # 409 on dup / delete guard                       app/routers/categories.py:47
│   │   ├── products.py      # search + pagination + 409 guards                app/routers/products.py:24,66
│   │   ├── inventory.py     # low-stock sorted, is_low_stock                  app/routers/inventory.py:25
│   │   └── orders.py        # with_for_update + dedup + stock invariant       app/routers/orders.py:13,19
│   └── tests/
│       ├── conftest.py      # TestClient + override_get_db                    app/tests/conftest.py:23
│       ├── test_categories.py # 11 tests
│       ├── test_products.py   # 17 tests
│       ├── test_inventory.py  # 13 tests
│       └── test_orders.py     # 11 tests
├── alembic/
│   ├── env.py               # DATABASE_URL + target_metadata
│   ├── script.py.mako
│   └── versions/001_initial.py  # init migration
├── .github/workflows/ci.yml # ruff + black + pytest --cov
├── Dockerfile               # python:3.11-slim
├── docker-compose.yml       # db:5432 + api:8001:8000 + healthcheck + restart
├── Makefile                 # setup/test/run/migrate/docker-up
├── pyproject.toml           # black/ruff/pytest/cov
├── requirements.txt         # pinned
├── .env.example / alembic.ini / LICENSE (MIT)
└── README.md                # this file
```

---

## ✅ Production Hardening Checklist

- [x] `Numeric(10,2)` + `native_enum=False` + `ondelete` + `cascade` (`app/models.py:29,51,64`)
- [x] `with_for_update()` + dedup (`app/routers/orders.py:13,19`)
- [x] Delete `409` not `500` (`app/routers/categories.py:47` `products.py:66`)
- [x] Pydantic v2 clean (`model_dump` / `ConfigDict` / `json_schema_extra`)
- [x] Alembic `001_initial` + `stamp head` (`alembic/versions/001_initial.py:1`)
- [x] CORS (`CORSMiddleware` `app/main.py:25`) + lifespan retry
- [x] CI (`ruff`/`black`/`pytest --cov`)
- [ ] Pagination for `/orders` & `/inventory` (only products has it)
- [ ] JWT auth (`OAuth2PasswordBearer` — next PR)
- [ ] Rate limiting + structured logging

---

## 🗺 Roadmap

* [x] 52 tests + `with_for_update` + `Numeric` + `409` guards + `CORS` + `Alembic`
* [x] Docker `8001:8000` + CI + LICENSE
* [ ] Pagination + filtering for orders/inventory
* [ ] JWT (access/refresh) + role RBAC
* [ ] `/metrics` + OpenTelemetry + `docker-compose` healthcheck for `api`

---

## 📄 License

MIT — see [`LICENSE`](LICENSE). Built for interviews, portfolios, and production demos.

<p align="center">
  <b>Star ⭐ if this helped you land an interview!</b><br/>
  <code>make test</code> → <code>docker compose up --build</code> → <code>http://localhost:8001/docs</code>
</p>
