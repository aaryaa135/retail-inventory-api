class TestInventoryCreation:
    def test_create_success(self, client, sample_product):
        r = client.post(
            "/api/v1/inventory/",
            json={"product_id": sample_product["id"], "quantity": 100, "low_stock_threshold": 15},
        )
        assert r.status_code == 201
        assert r.json()["quantity"] == 100
        assert r.json()["is_low_stock"] is False

    def test_nonexistent_product_returns_404(self, client):
        r = client.post("/api/v1/inventory/", json={"product_id": 9999, "quantity": 10})
        assert r.status_code == 404

    def test_duplicate_returns_409(self, client, sample_product):
        client.post("/api/v1/inventory/", json={"product_id": sample_product["id"], "quantity": 10})
        r = client.post(
            "/api/v1/inventory/", json={"product_id": sample_product["id"], "quantity": 20}
        )
        assert r.status_code == 409

    def test_negative_quantity_rejected(self, client, sample_product):
        r = client.post(
            "/api/v1/inventory/", json={"product_id": sample_product["id"], "quantity": -5}
        )
        assert r.status_code == 422


class TestInventoryUpdate:
    def test_update_quantity(self, client, sample_inventory, sample_product):
        r = client.put(f"/api/v1/inventory/{sample_product['id']}", json={"quantity": 200})
        assert r.json()["quantity"] == 200

    def test_update_threshold(self, client, sample_inventory, sample_product):
        r = client.put(
            f"/api/v1/inventory/{sample_product['id']}", json={"low_stock_threshold": 25}
        )
        assert r.json()["low_stock_threshold"] == 25

    def test_is_low_stock_true_at_threshold(self, client, sample_product):
        client.post(
            "/api/v1/inventory/",
            json={"product_id": sample_product["id"], "quantity": 10, "low_stock_threshold": 10},
        )
        r = client.get(f"/api/v1/inventory/{sample_product['id']}")
        assert r.json()["is_low_stock"] is True

    def test_is_low_stock_false_above_threshold(self, client, sample_product):
        client.post(
            "/api/v1/inventory/",
            json={"product_id": sample_product["id"], "quantity": 50, "low_stock_threshold": 10},
        )
        r = client.get(f"/api/v1/inventory/{sample_product['id']}")
        assert r.json()["is_low_stock"] is False


class TestLowStockAlerts:
    def _make(self, client, name, sku, qty, threshold):
        p = client.post("/api/v1/products/", json={"name": name, "sku": sku, "price": 10.0}).json()
        client.post(
            "/api/v1/inventory/",
            json={"product_id": p["id"], "quantity": qty, "low_stock_threshold": threshold},
        )
        return p

    def test_returns_only_below_threshold(self, client):
        self._make(client, "Low", "LO-001", 5, 10)
        self._make(client, "OK", "OK-001", 50, 10)
        alerts = client.get("/api/v1/inventory/low-stock").json()
        assert len(alerts) == 1
        assert alerts[0]["product_name"] == "Low"

    def test_shortage_calculated_correctly(self, client):
        self._make(client, "Critical", "CR-001", 3, 10)
        alerts = client.get("/api/v1/inventory/low-stock").json()
        assert alerts[0]["shortage"] == 7

    def test_sorted_by_quantity_ascending(self, client):
        self._make(client, "A", "SA-001", 8, 10)
        self._make(client, "B", "SB-001", 2, 10)
        self._make(client, "C", "SC-001", 5, 10)
        qtys = [a["current_quantity"] for a in client.get("/api/v1/inventory/low-stock").json()]
        assert qtys == sorted(qtys)

    def test_threshold_override(self, client):
        self._make(client, "Normal", "NI-001", 30, 10)
        alerts = client.get("/api/v1/inventory/low-stock?threshold_override=50").json()
        assert len(alerts) == 1

    def test_empty_when_all_stocked(self, client):
        self._make(client, "Full", "FU-001", 999, 10)
        assert client.get("/api/v1/inventory/low-stock").json() == []
