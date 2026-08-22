class TestCreateCategory:
    def test_create_success(self, client):
        r = client.post("/api/v1/categories/", json={"name": "Books", "description": "All books"})
        assert r.status_code == 201
        assert r.json()["name"] == "Books"

    def test_duplicate_returns_409(self, client, sample_category):
        r = client.post("/api/v1/categories/", json={"name": sample_category["name"]})
        assert r.status_code == 409

    def test_empty_name_rejected(self, client):
        r = client.post("/api/v1/categories/", json={"name": ""})
        assert r.status_code == 422


class TestGetCategories:
    def test_list_all(self, client, sample_category):
        client.post("/api/v1/categories/", json={"name": "Toys"})
        assert len(client.get("/api/v1/categories/").json()) == 2

    def test_get_by_id(self, client, sample_category):
        r = client.get(f"/api/v1/categories/{sample_category['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Electronics"

    def test_get_nonexistent_404(self, client):
        assert client.get("/api/v1/categories/99999").status_code == 404


class TestUpdateCategory:
    def test_update_name(self, client, sample_category):
        r = client.put(f"/api/v1/categories/{sample_category['id']}", json={"name": "Gadgets"})
        assert r.json()["name"] == "Gadgets"

    def test_update_nonexistent_404(self, client):
        assert client.put("/api/v1/categories/99999", json={"name": "X"}).status_code == 404


class TestDeleteCategory:
    def test_delete_success(self, client, sample_category):
        assert client.delete(f"/api/v1/categories/{sample_category['id']}").status_code == 204
        assert client.get(f"/api/v1/categories/{sample_category['id']}").status_code == 404

    def test_delete_with_products_returns_409(self, client, sample_product, sample_category):
        r = client.delete(f"/api/v1/categories/{sample_category['id']}")
        assert r.status_code == 409

    def test_delete_nonexistent_404(self, client):
        assert client.delete("/api/v1/categories/99999").status_code == 404
