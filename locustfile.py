from locust import HttpUser, task, between

class PharmaStockUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def read_medicines(self):
        self.client.get("/medicines?skip=0&limit=10", name="GET /medicines")

    @task(1)
    def create_transaction(self):
        # ID 1 harus tersedia. Jalankan seed.py sebelum pengujian.
        self.client.post(
            "/transactions",
            json={"medicine_id": 1, "jumlah": 1},
            name="POST /transactions",
        )