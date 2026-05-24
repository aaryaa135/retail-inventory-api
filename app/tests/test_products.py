class TestCreateProduct:
    def test_create_product_success(self, client, sample_category):
        r = client.post("/api/v1/products/", json={"name": "Laptop", "sku": "LP-001", "price": 1299.99, "category_id": sample_category["id"]})
        assert r.status_code == 201
        assert r.json()["sku"] == "LP-001"

    def test_create_product_without_category(self, client):
        r = client.post("/api/v1/products/", json={"name": "Generic", "sku": "GI-001", "price": 9.99})
        assert r.status_code == 201

    def test_duplicate_sku_returns_409(self, client):
        p = {"name": "Item", "sku": "DUPE-001", "price": 10.0}
        client.post("/api/v1/products/", json=p)
        r = client.post("/api/v1/products/", json=p)
        assert r.status_code == 409

    def test_invalid_category_returns_404(self, client):
        r = client.post("/api/v1/products/", json={"name": "X", "sku": "X-001", "price": 10.0, "category_id": 9999})
        assert r.status_code == 404

    def test_negative_price_rejected(self, client):
        r = client.post("/api/v1/products/", json={"name": "X", "sku": "X-002", "price": -5.0})
        assert r.status_code == 422

    def test_zero_price_rejected(self, client):
        r = client.post("/api/v1/products/", json={"name": "X", "sku": "X-003", "price": 0})
        assert r.status_code == 422


class TestGetProducts:
    def test_get_by_id(self, client, sample_product):
        r = client.get(f"/api/v1/products/{sample_product['id']}")
        assert r.status_code == 200

    def test_get_nonexistent_returns_404(self, client):
        assert client.get("/api/v1/products/99999").status_code == 404

    def test_list_all(self, client):
        client.post("/api/v1/products/", json={"name": "A", "sku": "A-001", "price": 1.0})
        client.post("/api/v1/products/", json={"name": "B", "sku": "B-001", "price": 2.0})
        assert len(client.get("/api/v1/products/").json()) == 2

    def test_search_by_name(self, client):
        client.post("/api/v1/products/", json={"name": "Sony TV", "sku": "ST-001", "price": 199.0})
        client.post("/api/v1/products/", json={"name": "Apple Watch", "sku": "AW-001", "price": 399.0})
        r = client.get("/api/v1/products/?search=sony")
        assert len(r.json()) == 1

    def test_filter_by_category(self, client, sample_category):
        client.post("/api/v1/products/", json={"name": "TV", "sku": "TV-001", "price": 500.0, "category_id": sample_category["id"]})
        client.post("/api/v1/products/", json={"name": "Other", "sku": "OT-001", "price": 10.0})
        r = client.get(f"/api/v1/products/?category_id={sample_category['id']}")
        assert len(r.json()) == 1

    def test_pagination(self, client):
        for i in range(5):
            client.post("/api/v1/products/", json={"name": f"Item {i}", "sku": f"IT-00{i}", "price": 10.0})
        assert len(client.get("/api/v1/products/?skip=0&limit=2").json()) == 2


class TestUpdateProduct:
    def test_update_price(self, client, sample_product):
        r = client.put(f"/api/v1/products/{sample_product['id']}", json={"price": 399.99})
        assert r.json()["price"] == 399.99

    def test_update_nonexistent_returns_404(self, client):
        assert client.put("/api/v1/products/99999", json={"price": 10.0}).status_code == 404

    def test_partial_update_preserves_sku(self, client, sample_product):
        client.put(f"/api/v1/products/{sample_product['id']}", json={"price": 150.0})
        r = client.get(f"/api/v1/products/{sample_product['id']}")
        assert r.json()["sku"] == sample_product["sku"]


class TestDeleteProduct:
    def test_delete_success(self, client, sample_product):
        assert client.delete(f"/api/v1/products/{sample_product['id']}").status_code == 204

    def test_deleted_returns_404(self, client, sample_product):
        client.delete(f"/api/v1/products/{sample_product['id']}")
        assert client.get(f"/api/v1/products/{sample_product['id']}").status_code == 404
