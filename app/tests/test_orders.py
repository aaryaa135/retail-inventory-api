class TestCreateOrder:
    def test_order_success_deducts_stock(self, client, sample_inventory, sample_product):
        initial = sample_inventory["quantity"]
        r = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 5}]})
        assert r.status_code == 201
        assert r.json()["status"] == "confirmed"
        inv = client.get(f"/api/v1/inventory/{sample_product['id']}").json()
        assert inv["quantity"] == initial - 5

    def test_insufficient_stock_returns_422(self, client, sample_inventory, sample_product):
        r = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 9999}]})
        assert r.status_code == 422
        assert "Insufficient stock" in r.json()["detail"]

    def test_stock_not_deducted_on_failure(self, client, sample_inventory, sample_product):
        initial = client.get(f"/api/v1/inventory/{sample_product['id']}").json()["quantity"]
        client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 9999}]})
        current = client.get(f"/api/v1/inventory/{sample_product['id']}").json()["quantity"]
        assert current == initial

    def test_nonexistent_product_returns_404(self, client):
        r = client.post("/api/v1/orders/", json={"items": [{"product_id": 9999, "quantity": 1}]})
        assert r.status_code == 404

    def test_total_amount_correct(self, client, sample_inventory, sample_product):
        r = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 3}]})
        assert abs(r.json()["total_amount"] - sample_product["price"] * 3) < 0.01


class TestCancelOrder:
    def test_cancel_restores_stock(self, client, sample_inventory, sample_product):
        initial = sample_inventory["quantity"]
        order = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 10}]}).json()
        client.patch(f"/api/v1/orders/{order['id']}/cancel")
        inv = client.get(f"/api/v1/inventory/{sample_product['id']}").json()
        assert inv["quantity"] == initial

    def test_cancel_sets_status(self, client, sample_inventory, sample_product):
        order = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 1}]}).json()
        r = client.patch(f"/api/v1/orders/{order['id']}/cancel")
        assert r.json()["status"] == "cancelled"

    def test_double_cancel_returns_400(self, client, sample_inventory, sample_product):
        order = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 1}]}).json()
        client.patch(f"/api/v1/orders/{order['id']}/cancel")
        r = client.patch(f"/api/v1/orders/{order['id']}/cancel")
        assert r.status_code == 400

    def test_cancel_nonexistent_returns_404(self, client):
        assert client.patch("/api/v1/orders/99999/cancel").status_code == 404


class TestListOrders:
    def test_list_orders(self, client, sample_inventory, sample_product):
        client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 1}]})
        assert len(client.get("/api/v1/orders/").json()) == 1

    def test_get_order_by_id(self, client, sample_inventory, sample_product):
        order = client.post("/api/v1/orders/", json={"items": [{"product_id": sample_product["id"], "quantity": 2}]}).json()
        r = client.get(f"/api/v1/orders/{order['id']}")
        assert r.json()["id"] == order["id"]
