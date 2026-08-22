# Retail Inventory API ΓÇö Complete Code Explanation (Whole Project)

> **52 tests | FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic 2.9 + Alembic 1.13 + PostgreSQL 16 / SQLite | Docker 8001:8000 | TDD**

This is the single-file bible for the whole codebase. Every file, every line that matters, and how data flows. Accurate to commit `52c1855` (HTML landing at `/`) + `6cbecd7` + `d90e704`.

---

## Table of Contents
1. [Quick Mental Model](#1-quick-mental-model)
2. [Project Tree + What Each File Does](#2-project-tree--what-each-file-does)
3. [Core File by File (with line numbers)](#3-core-file-by-file-with-line-numbers)
4. [Data Model / ER](#4-data-model--er)
5. [API Surface (21 endpoints)](#5-api-surface-21-endpoints)
6. [Business Logic Deep Dive (orders, inventory)](#6-business-logic-deep-dive-orders-inventory)
7. [Testing (52 tests)](#7-testing-52-tests)
8. [Migrations / DB Wiring](#8-migrations--db-wiring)
9. [Docker / Infra / Config](#9-docker--infra--config)
10. [How to Run & Verify]](#10-how-to-run--verify)
11. [Interview Talking Points](#11-interview-talking-points)

---

## 1. Quick Mental Model

```
Client ΓåÆ FastAPI (app/main.py:32, lifespan+ CORS) ΓåÆ Routers ΓåÆ SQLAlchemy ORM (app/models.py) ΓåÆ Postgres (or sqlite)
                                          Γåÿ Pydantic Schemas (app/schemas.py) for validation
                                          Γåÿ pytest + TestClient (app/tests/conftest.py:23) overrides get_db
```

**One sentence:** Category has Products, Product has 1 Inventory, Order has many OrderItems, Order creation deducts Inventory atomically with `with_for_update()`.

---

## 2. Project Tree + What Each File Does

```
retail-inventory-api/
Γö£ΓöÇΓöÇ app/
Γöé   Γö£ΓöÇΓöÇ __init__.py          # empty, makes `app` a package
Γöé   Γö£ΓöÇΓöÇ main.py              # FastAPI app, lifespan retry, CORS, routers, HTML landing at / + /health
Γöé   Γö£ΓöÇΓöÇ database.py          # engine, SessionLocal, Base, get_db(), DATABASE_URL + sqlite check_same_thread
Γöé   Γö£ΓöÇΓöÇ models.py            # 5 tables + OrderStatus enum, Numeric(10,2), ondelete, cascade
Γöé   Γö£ΓöÇΓöÇ schemas.py           # Pydantic v2 DTOs, Field validation, ConfigDict
Γöé   Γö£ΓöÇΓöÇ routers/
Γöé   Γöé   Γö£ΓöÇΓöÇ __init__.py
Γöé   Γöé   Γö£ΓöÇΓöÇ categories.py    # CRUD, 409 dup, 409 delete guard
Γöé   Γöé   Γö£ΓöÇΓöÇ products.py      # CRUD + ?search/?category_id/?skip/limit + 409 guards
Γöé   Γöé   Γö£ΓöÇΓöÇ inventory.py     # 1:1 product, is_low_stock, /low-stock sorted
Γöé   Γöé   ΓööΓöÇΓöÇ orders.py        # POST with_for_update + dedup 400, 422 stock, cancel restore
Γöé   ΓööΓöÇΓöÇ tests/
Γöé       Γö£ΓöÇΓöÇ __init__.py
Γöé       Γö£ΓöÇΓöÇ conftest.py      # TestClient + override_get_db, fixtures sample_categoryΓåÆproductΓåÆinventory
Γöé       Γö£ΓöÇΓöÇ test_categories.py # 11 tests
Γöé       Γö£ΓöÇΓöÇ test_products.py   # 17 tests
Γöé       Γö£ΓöÇΓöÇ test_inventory.py  # 13 tests
Γöé       ΓööΓöÇΓöÇ test_orders.py     # 11 tests
Γö£ΓöÇΓöÇ alembic/
Γöé   Γö£ΓöÇΓöÇ env.py               # reads DATABASE_URL, imports models for autogenerate
Γöé   Γö£ΓöÇΓöÇ script.py.mako
Γöé   ΓööΓöÇΓöÇ versions/001_initial.py # creates all 5 tables
Γö£ΓöÇΓöÇ conftest.py              # sys.path fix for Windows "No module named app"
Γö£ΓöÇΓöÇ pytest.ini               # testpaths = app/tests, pythonpath = .
Γö£ΓöÇΓöÇ requirements.txt         # pinned: fastapi 0.115, sqlalchemy 2.0.35, pydantic 2.9.2, alembic 1.13.3, etc.
Γö£ΓöÇΓöÇ pyproject.toml           # black/ruff/pytest/cov config
Γö£ΓöÇΓöÇ Dockerfile               # python:3.11-slim, pip install, CMD sh -c uvicorn ... ${PORT:-8000}
Γö£ΓöÇΓöÇ docker-compose.yml       # db:5432 postgres:16-alpine healthcheck + api:8001:8000 restart unless-stopped
Γö£ΓöÇΓöÇ Makefile                 # setup/test/run/migrate/docker-up (cross-platform)
Γö£ΓöÇΓöÇ .env.example             # DATABASE_URL template
Γö£ΓöÇΓöÇ .dockerignore
Γö£ΓöÇΓöÇ alembic.ini
Γö£ΓöÇΓöÇ render.yaml              # Render blueprint (now sqlite fallback, no bank)
Γö£ΓöÇΓöÇ .github/workflows/ci.yml # ruff + black --check + pytest --cov
Γö£ΓöÇΓöÇ LICENSE (MIT) + README.md (mermaid) + docs/CODE_EXPLANATION.md (this file)
ΓööΓöÇΓöÇ .gitignore / setup.bat / start_server.bat / run_tests.bat
```

---

## 3. Core File by File (with line numbers)

### `conftest.py:1-6` ΓÇö Windows path fix
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```
Without this `pytest app/tests/` fails on Windows with `No module named 'app'` because tests import `app.main`.

### `pytest.ini:1-3`
```
[pytest]
testpaths = app/tests
pythonpath = .
```
Tells pytest where to collect and adds project root to `PYTHONPATH`.

### `requirements.txt:1-10` ΓÇö pinned prod = reproducible
```
fastapi==0.115.0
uvicorn[standard]==0.30.6  # httptools+uvloop+watchfiles for --reload
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
pytest==8.3.3
httpx==0.27.2              # TestClient needs it
pydantic==2.9.2
python-dotenv==1.0.1
alembic==1.13.3
pytest-asyncio==0.24.0     # not used yet but ready
```

### `app/database.py:1-26` ΓÇö engine + session

* `load_dotenv()` `app/database.py:5` ΓåÆ reads `.env`
* `DATABASE_URL = os.getenv(..., "sqlite:///./retail_inventory.db")` `app/database.py:9` ΓÇö Docker sets `postgresql://retail:retail@db:5432/retail` `docker-compose.yml:22`
* `connect_args = {"check_same_thread": False} if sqlite else {}` `app/database.py:14` ΓÇö required for SQLite
* `engine = create_engine(DATABASE_URL, connect_args)` `app/database.py:16`
* `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)` `app/database.py:17`
* `Base = declarative_base()` from `sqlalchemy.orm` `app/database.py:3` (fixed warning, was `sqlalchemy.ext.declarative`)
* `get_db()` `app/database.py:21` ΓÇö FastAPI `Depends` generator, `yield db` then `close()`

### `app/models.py:1-66` ΓÇö 5 tables

**Enum** `app/models.py:8`:
```python
class OrderStatus(str, enum.Enum): PENDING="pending"; CONFIRMED="confirmed"; CANCELLED="cancelled"
```

**Category** `app/models.py:14`:
```python
__tablename__="categories"
id PK, name String(100) unique index, description 255, created_at server_default=func.now()
products = relationship("Product", back_populates="category")
```

**Product** `app/models.py:23`:
```python
name 200 index, sku 50 unique index, description 500, price Numeric(10,2) NOT NULL
category_id FK categories.id ondelete=SET NULL
created_at server_default=now(), updated_at server_default=now() onupdate=now()
category rel, inventory 1:1 cascade="all, delete-orphan", order_items rel
```
* `Numeric(10,2)` `app/models.py:29` ΓÇö money, not `Float` (production fix)
* `ondelete=SET NULL` `app/models.py:30` ΓÇö deleting category doesn't cascade delete products

**Inventory** `app/models.py:38`:
```python
product_id FK products.id ondelete=CASCADE unique NOT NULL
quantity int default 0, low_stock_threshold int default 10
updated_at server_default=now() onupdate=now()
product rel
```
* `unique` `app/models.py:41` enforces 1:1
* `ondelete=CASCADE` `app/models.py:41` ΓÇö product deleted ΓåÆ inventory deleted

**Order** `app/models.py:48`:
```python
status Enum(OrderStatus, native_enum=False) default PENDING
total_amount Numeric(10,2) default 0.0
created_at/updated_at server_default=now()
items rel cascade="all, delete-orphan"
```
* `native_enum=False` `app/models.py:51` ΓÇö works on SQLite

**OrderItem** `app/models.py:58`:
```python
order_id FK orders.id ondelete=CASCADE, product_id FK products.id ondelete=RESTRICT
quantity int NOT NULL, unit_price Numeric(10,2) NOT NULL
order rel, product rel
```
* `RESTRICT` `app/models.py:62` ΓÇö can't delete product if orders exist ΓåÆ router maps to `409`

### `app/schemas.py:1-102` ΓÇö Pydantic v2 DTOs

* `from pydantic import BaseModel, ConfigDict, Field` `app/schemas.py:1` (fixed `validator` unused + `ConfigDict`)
* `CategoryBase: name Field(min_length=1,max_length=100, json_schema_extra={"example":"Electronics"})` `app/schemas.py:8` (was `example=` deprecated)
* `CategoryResponse: model_config = ConfigDict(from_attributes=True)` `app/schemas.py:21` (was `class Config`)
* Same for `ProductResponse:41`, `InventoryResponse:59`, `OrderItemResponse:85`, `OrderResponse:94`
* `InventoryCreate: quantity ge=0, low_stock_threshold ge=0` `app/schemas.py:52`
* `OrderCreate: items List[OrderItemCreate] min_length=1` `app/schemas.py:83`
* `OrderItemResponse: subtotal float =0.0` computed in routers, not here

### `app/main.py:1-59` ΓÇö FastAPI app

* `lifespan` `app/main.py:10-29` ΓÇö `if AUTO_CREATE_TABLES=="true"` ΓåÆ `Base.metadata.create_all(bind=engine)` with 10├ù retry on `could not translate host name "db"` (Docker DNS race) else `print` and don't block `health`
* `FastAPI(title="Retail Inventory Management API", version="1.0.0", lifespan=lifespan)` `app/main.py:32`
* `CORSMiddleware allow_origins=["*"]` `app/main.py:39`
* Routers `app/main.py:47-50` mounted at `/api/v1/{products,categories,inventory,orders}`
* `GET /` `app/main.py:53` ΓåÆ `HTMLResponse` landing page (crazy README-style HTML with Swagger buttons, feature cards, endpoint table) ΓÇö so live link looks pro. `GET /health` `app/main.py:58` ΓåÆ `{"status":"healthy"}`

### `app/routers/products.py:1-72`

* `POST /` `app/routers/products.py:10` ΓÇö check `sku` dup `409`, `category_id` 404, `Product(**product.model_dump())` (was `dict()`), commit
* `GET /` `app/routers/products.py:24` ΓÇö `skip ge0, limit 1-100, category_id, search` ΓåÆ `ilike(f"%{search}%")` on name|sku, `offset/limit`
* `GET /{id}` `404` if not found
* `PUT /{id}` `app/routers/products.py:51` ΓÇö check `category_id`, `updates.model_dump(exclude_unset=True)`
* `DELETE /{id}` `app/routers/products.py:66` ΓÇö check `OrderItem.product_id` ΓåÆ `409` else try `delete` + `exceptΓåÆ409`

### `app/routers/categories.py:1-53`

* `POST /` `409` dup name
* `GET /` list, `GET /{id}` 404
* `PUT /{id}` update
* `DELETE /{id}` `app/routers/categories.py:47` ΓÇö check `Product.category_id` ΓåÆ `409`, else try delete

### `app/routers/inventory.py:1-80`

* `POST /` `app/routers/inventory.py:10` ΓÇö `404` product, `409` inventory exists, `Inventory(**inv.model_dump())`, set `is_low_stock = qty <= threshold`
* `GET /low-stock` `app/routers/inventory.py:25` ΓÇö **must be before `/{product_id}`** (order matters), joins `Inventory+Product`, `threshold_override` optional, `if qty <= threshold` ΓåÆ `LowStockAlert(product_id, product_name, sku, current_quantity, threshold, shortage=max(0,thr-qty))`, `sorted by current_quantity`
* `GET /` `app/routers/inventory.py:48` ΓÇö all, compute `is_low_stock`
* `GET /{product_id}` `404` if no inventory
* `PUT /{product_id}` `70` ΓÇö `updates.model_dump(exclude_unset)`, recompute `is_low_stock`

### `app/routers/orders.py:1-93`

* `POST /` `app/routers/orders.py:10` ΓÇö **dedup** `seen set` ΓåÆ `400 duplicate product_id`, loop: `Product` check `404`, `Inventory with_for_update()` `app/routers/orders.py:19` ΓåÆ `400 no inventory`, `422 insufficient`, `subtotal=float(price)*qty`, `total_amount` sum, `db_order=Order(total_amount, CONFIRMED)` `flush`, then `OrderItem` + `inv.quantity-=qty`, `commit`, return `OrderResponse` with `float()` casts for `Numeric`
* `GET /` `50` ΓÇö all, float casts
* `GET /{id}` `61` ΓÇö 404, float casts
* `PATCH /{id}/cancel` `74` ΓÇö `Order` (with_for_update no-op on SQLite), `400 already cancelled`, `Inventory with_for_update` per item `+=qty`, `CANCELLED`, commit, float casts

### `app/tests/conftest.py:1-51` ΓÇö test wiring

* `TEST_DATABASE_URL = "sqlite:///./test_retail.db"` `app/tests/conftest.py:8` + `test_engine` + `TestingSessionLocal`
* `override_get_db()` yields `TestingSessionLocal`
* `client` fixture `scope=function` `app/tests/conftest.py:22` ΓÇö `create_all(bind=test_engine)`, `app.dependency_overrides[get_db]=override_get_db`, `with TestClient(app) as c: yield c`, then `drop_all`, `clear()`
* `sample_category` `32` ΓÇö `POST /categories/ {"name":"Electronics"}`
* `sample_product` `38` ΓÇö `POST /products/ {"Wireless Headphones","WH-001",299.99, category_id}`
* `sample_inventory` `47` ΓÇö `POST /inventory/ {"product_id", qty 50}`

### `app/tests/test_categories.py:1-51` (11 tests) ΓÇö was missing

* `TestCreateCategory` 3: success 201, dup 409, empty 422
* `TestGetCategories` 3: list 2, get by id, 404
* `TestUpdateCategory` 2: update name, 404
* `TestDeleteCategory` 3: delete 204, delete with products 409, 404

### `app/tests/test_products.py:1-81` (17)

* Create 6: success, without category, dup 409, invalid category 404, negative 422, zero 422
* Get 6: by id, 404, list 2, search sony, filter category, pagination skip/limit
* Update 3: price, 404, preserve sku
* Delete 2: success 204, deleted 404

### `app/tests/test_inventory.py:1-74` (13)

* Creation 4: success is_low_stock false, 404, dup 409, negative 422
* Update 4: qty 200, threshold 25, at threshold true, above false
* LowStock 5: only below, shortage 7, sorted asc, threshold_override 50, empty when stocked

### `app/tests/test_orders.py:1-61` (11)

* Create 5: success deduct, 422 insufficient, stock not deducted on fail, 404, total correct
* Cancel 4: restore stock, status cancelled, double 400, 404
* List 2: list 1, get by id

---

## 4. Data Model / ER

```
Category ||--o{ Product : has
Product ||--|| Inventory : tracked_by (unique, CASCADE delete)
Product ||--o{ OrderItem : ordered_in (RESTRICT delete)
Order ||--o{ OrderItem : contains (CASCADE delete)
```

Indexes: `categories.name unique`, `products.sku unique`, `products.name`, `inventory product_id unique`, etc.

Monies: `Numeric(10,2)` everywhere ΓÇö interview win over `Float`.

---

## 5. API Surface (21 endpoints)

| Method | Path | File | Status |
|---|---|---|---|
| GET | `/` (HTML) | `main.py:53` | 200 |
| GET | `/health` | `main.py:58` | 200 |
| POST | `/api/v1/categories/` | `categories.py:10` | 201/409/422 |
| GET | `/api/v1/categories/` | `22` | 200 |
| GET | `/api/v1/categories/{id}` | `27` | 200/404 |
| PUT | `/api/v1/categories/{id}` | `35` | 200/404 |
| DELETE | `/api/v1/categories/{id}` | `47` | 204/404/409 |
| POST | `/api/v1/products/` | `products.py:10` | 201/409/404/422 |
| GET | `/api/v1/products/?search=&category_id=&skip=&limit=` | `24` | 200 |
| GET | `/api/v1/products/{id}` | `43` | 200/404 |
| PUT | `/api/v1/products/{id}` | `51` | 200/404 |
| DELETE | `/api/v1/products/{id}` | `66` | 204/404/409 |
| POST | `/api/v1/inventory/` | `inventory.py:10` | 201/404/409/422 |
| GET | `/api/v1/inventory/` | `48` | 200 |
| GET | `/api/v1/inventory/low-stock` | `25` | 200 |
| GET | `/api/v1/inventory/{product_id}` | `59` | 200/404 |
| PUT | `/api/v1/inventory/{product_id}` | `69` | 200/404 |
| POST | `/api/v1/orders/` | `orders.py:10` | 201/400/404/422 |
| GET | `/api/v1/orders/` | `50` | 200 |
| GET | `/api/v1/orders/{id}` | `61` | 200/404 |
| PATCH | `/api/v1/orders/{id}/cancel` | `74` | 200/404/400 |

Docs: `/docs` (Swagger), `/redoc`, `/openapi.json`

---

## 6. Business Logic Deep Dive (orders, inventory)

**Order creation flow:**
1. Dedup `product_id` in payload `orders.py:13` ΓåÆ 400
2. For each item: lock `Inventory` row `with_for_update()` `19` (Postgres `SELECT FOR UPDATE`, SQLite no-op)
3. Check stock `if inv.quantity < qty` ΓåÆ 422, else `total_amount += float(price)*qty`
4. `Order(CONFIRMED)` + `flush()` to get `id`, then `OrderItem`s + `inv.quantity -= qty` `35-37`, `commit`
5. Invariant: `test_orders.py:15` stock not deducted on 422 (transaction rolled back)

**Cancel:**
* `404` / `400 already cancelled`, then `with_for_update` per inventory `+= qty`, `CANCELLED` `74-84`

**Low-stock:**
* `GET /low-stock` scans `Inventory join Product` `30`, uses `threshold_override` or `low_stock_threshold`, `if qty <= thr` ΓåÆ alert, `shortage = thr - qty`, `sorted(qty asc)` `45`

---

## 7. Testing (52 Tests)

* `pytest.ini:2` `testpaths=app/tests`, `conftest.py:6` path fix, `app/tests/conftest.py:8` sqlite file + override
* Run: `pytest app/tests/ -v` ΓåÆ `52 passed, 0 warnings` (was 6, fixed `ConfigDict` + `declarative_base`)
* `docker compose exec api pytest app/tests/ -v` same
* CI `.github/workflows/ci.yml:1` runs `ruff check`, `black --check`, `pytest --cov` on `3.11`

---

## 8. Migrations / DB Wiring

* `alembic.ini:1` + `alembic/env.py:12` reads `DATABASE_URL` + `target_metadata = Base.metadata`
* `alembic/versions/001_initial.py:1` creates 5 tables with `Numeric`, `Enum`, `ondelete` ΓÇö `upgrade/downgrade`
* `app/main.py:14` `lifespan` does `create_all` with 10├ù retry on `could not translate host name "db"` (Docker DNS race). For prod: `AUTO_CREATE_TABLES=false` + `alembic upgrade head`; for dev: `true` auto-creates. Stamped: `alembic stamp head` ΓåÆ `001 (head)`

---

## 9. Docker / Infra / Config

* `Dockerfile:1` `python:3.11-slim`, `pip install`, `COPY .`, `EXPOSE 8000`, `CMD sh -c "uvicorn ... --port ${PORT:-8000}"` (Render HF needs `$PORT`)
* `docker-compose.yml:1` `db: postgres:16-alpine` `5432:5432` healthcheck `pg_isready`, `api: 8001:8000` (avoids host `8000` taken by `authforge-api`), `DATABASE_URL=postgresql://retail:retail@db:5432/retail`, `restart: unless-stopped`, volume `pgdata`
* `.env.example:1` `DATABASE_URL=postgresql://...`, `app/database.py:14` `check_same_thread` only for sqlite
* `pyproject.toml:1` `black line-length 100`, `ruff select E,F,I,UP,B,SIM`, `pytest addopts -v`, `coverage omit tests`
* `Makefile:1` `setup/test/run/migrate/docker-up/down`
* `render.yaml:1` Blueprint without DB (no bank), `AUTO_CREATE_TABLES=true`
* `.github/workflows/ci.yml:1` `setup-python 3.11` + `pip install ruff black` + checks

---

## 10. How to Run & Verify

**Docker (recommended):**
```bash
docker compose up --build # API http://localhost:8001/docs (8001!), DB 5432
curl http://localhost:8001/health # {"status":"healthy"}
curl http://localhost:8001/ # HTML landing
docker compose exec api pytest app/tests/ -v # 52 passed
docker compose down # -v to wipe pgdata
```

**Local:**
```powershell
setup.bat # or python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt
uvicorn app.main:app --reload # http://localhost:8000/docs
pytest app/tests/ -v # 52 passed
```

**Manual curl flow:**
```bash
curl -X POST http://localhost:8001/api/v1/categories/ -d '{"name":"Electronics"}'
curl -X POST http://localhost:8001/api/v1/products/ -d '{"name":"Sony TV","sku":"ST-001","price":199,"category_id":1}'
curl -X POST http://localhost:8001/api/v1/inventory/ -d '{"product_id":1,"quantity":50}'
curl -X POST http://localhost:8001/api/v1/orders/ -d '{"items":[{"product_id":1,"quantity":2}]}'
curl http://localhost:8001/api/v1/inventory/low-stock
```

---

## 11. Interview Talking Points

* **Why `Numeric` not `Float`?** `app/models.py:29` avoids money rounding.
* **Why `with_for_update`?** `app/routers/orders.py:19` prevents oversell under concurrency (SQLite no-op, Postgres lock).
* **Why `409` not `500` on delete?** `app/routers/categories.py:47` checks before `delete`, `ondelete=RESTRICT` `app/models.py:62`.
* **Why `lifespan` not `create_all` at import?** `app/main.py:10` ΓÇö prod uses Alembic, dev fallback with retry.
* **Why `52` not `40`?** Added `test_categories.py:1` (was missing) + dedup/409 guards.
* **Why `8001`?** Host `8000` taken by `authforge-api`, `docker-compose.yml:21` maps `8001:8000`.

---

*End. For live demo: `docker compose up --build` ΓåÆ `http://localhost:8001/` (HTML) ΓåÆ `/docs` try-it-out. MIT ┬⌐ 2026.*
