import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.database import Base, engine
from app.routers import categories, inventory, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Prefer Alembic migrations: `alembic upgrade head`
    # Fallback for local SQLite dev / tests where Alembic hasn't run yet
    if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
        import time

        from sqlalchemy.exc import OperationalError

        for attempt in range(10):
            try:
                Base.metadata.create_all(bind=engine)
                break
            except OperationalError as e:
                if "could not translate host name" in str(e) and attempt < 9:
                    time.sleep(2)
                    continue
                # Don't block startup on DB errors in dev; health endpoint will still work
                print(f"[lifespan] DB init failed (attempt {attempt+1}): {e}")
                if attempt == 9:
                    break
                time.sleep(2)
    yield


app = FastAPI(
    title="Retail Inventory Management API",
    description="Production-grade REST API for retail inventory — FastAPI + PostgreSQL + TDD",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])


@app.get("/", tags=["Health"], response_class=HTMLResponse)
def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Retail Inventory API — Live</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.6}
.container{max-width:960px;margin:0 auto;padding:32px 20px}
.hero{text-align:center;padding:40px 0 24px;border-bottom:1px solid #1e293b}
.hero h1{font-size:2.4rem;color:#f8fafc}
.hero p{color:#94a3b8;margin-top:8px}
.badge{display:inline-block;padding:4px 10px;border-radius:999px;font-size:.75rem;margin:4px;background:#1e293b;border:1px solid #334155}
.btn{display:inline-block;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:600;margin:8px}
.btn-primary{background:#0ea5e9;color:#fff}
.btn-dark{background:#1e293b;color:#e2e8f0;border:1px solid #334155}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:24px 0}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px}
.card h3{color:#f8fafc;margin-bottom:8px}
.card ul{padding-left:18px;color:#cbd5e1}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:.9rem}
th,td{padding:8px 10px;border:1px solid #334155;text-align:left}
th{background:#1e293b;color:#f8fafc}
code{background:#1e293b;padding:2px 6px;border-radius:4px;font-size:.85rem}
.footer{text-align:center;padding:24px;color:#64748b;border-top:1px solid #1e293b;margin-top:32px}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <h1>🛒 Retail Inventory API</h1>
    <p>Production-grade REST API — FastAPI + PostgreSQL + SQLAlchemy 2.0 + Pydantic v2 + Alembic + TDD</p>
    <p>
      <span class="badge">Python 3.11</span>
      <span class="badge">FastAPI 0.115</span>
      <span class="badge">PostgreSQL 16</span>
      <span class="badge">52 tests passing</span>
      <span class="badge">Docker 8001</span>
    </p>
    <div style="margin-top:20px">
      <a class="btn btn-primary" href="/docs">📚 Swagger Docs</a>
      <a class="btn btn-dark" href="/redoc">📖 ReDoc</a>
      <a class="btn btn-dark" href="/health">💚 Health</a>
      <a class="btn btn-dark" href="/openapi.json">🔗 OpenAPI</a>
    </div>
    <p style="margin-top:12px"><a style="color:#38bdf8" href="https://github.com/aaryaa135/retail-inventory-api" target="_blank">GitHub: aaryaa135/retail-inventory-api</a></p>
  </div>

  <div class="grid">
    <div class="card">
      <h3>✨ Features</h3>
      <ul>
        <li>SKU-unique catalog, category CRUD</li>
        <li>1:1 inventory + low-stock alerts (sorted)</li>
        <li>Stock-aware orders (with_for_update) + cancel restore</li>
        <li>Numeric(10,2) for money, 409 guards not 500</li>
      </ul>
    </div>
    <div class="card">
      <h3>🧱 Tech Stack</h3>
      <ul>
        <li>FastAPI 0.115 + Uvicorn 0.30.6</li>
        <li>SQLAlchemy 2.0 + Alembic 1.13 (001_initial)</li>
        <li>Pydantic 2.9 + pytest 8.3 (52 tests)</li>
        <li>Docker + Compose 8001:8000 + CI</li>
      </ul>
    </div>
  </div>

  <h3 style="margin-top:8px">🔌 Core Endpoints</h3>
  <table>
    <tr><th>Method</th><th>Path</th><th>Description</th></tr>
    <tr><td>POST</td><td><code>/api/v1/products/</code></td><td>Create (409 SKU)</td></tr>
    <tr><td>GET</td><td><code>/api/v1/products/?search=&category_id=&skip=&limit=</code></td><td>List + filter + pagination</td></tr>
    <tr><td>POST</td><td><code>/api/v1/categories/</code></td><td>Create category</td></tr>
    <tr><td>POST</td><td><code>/api/v1/inventory/</code></td><td>Create 1:1 stock</td></tr>
    <tr><td>GET</td><td><code>/api/v1/inventory/low-stock</code></td><td>Alerts sorted asc</td></tr>
    <tr><td>POST</td><td><code>/api/v1/orders/</code></td><td>Create (422 if stock low)</td></tr>
    <tr><td>PATCH</td><td><code>/api/v1/orders/{id}/cancel</code></td><td>Cancel + restore</td></tr>
  </table>

  <div class="card" style="margin-top:16px">
    <h3>🚀 Try It Live</h3>
    <p><code>curl https://YOUR-URL/api/v1/categories/ -H "Content-Type: application/json" -d '{"name":"Electronics"}'</code></p>
    <p style="margin-top:8px">See <a style="color:#38bdf8" href="/docs">/docs</a> for interactive try-it-out. Health: <code>/health</code> → <code>{"status":"healthy"}</code></p>
  </div>

  <div class="footer">
    Built for interviews — <code>make test</code> → <code>docker compose up --build</code> → <code>52 passed</code><br/>
    MIT © 2026 — Deploy: Render / Railway / Fly.io with <code>DATABASE_URL</code> + <code>alembic upgrade head</code>
  </div>
</div>
</body>
</html>
    """


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
