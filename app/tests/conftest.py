import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_retail.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_category(client):
    resp = client.post(
        "/api/v1/categories/", json={"name": "Electronics", "description": "Tech products"}
    )
    return resp.json()


@pytest.fixture
def sample_product(client, sample_category):
    resp = client.post(
        "/api/v1/products/",
        json={
            "name": "Wireless Headphones",
            "sku": "WH-001",
            "price": 299.99,
            "category_id": sample_category["id"],
        },
    )
    return resp.json()


@pytest.fixture
def sample_inventory(client, sample_product):
    resp = client.post(
        "/api/v1/inventory/",
        json={"product_id": sample_product["id"], "quantity": 50, "low_stock_threshold": 10},
    )
    return resp.json()
