from fastapi import FastAPI
from app.routers import products, categories, inventory, orders
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Retail Inventory Management API",
    description="Production-grade REST API for retail inventory — FastAPI + PostgreSQL + TDD",
    version="1.0.0",
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
