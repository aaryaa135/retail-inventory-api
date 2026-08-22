import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, categories, inventory, orders
from app.database import Base, engine


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


@app.get("/", tags=["Health"])
def root():
    return {"message": "Retail Inventory API is running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
