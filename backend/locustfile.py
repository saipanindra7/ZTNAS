"""Locust load/stress test for ZTNAS auth endpoints.

Run:
  locust -f backend/locustfile.py --host http://localhost:8000
"""

from locust import HttpUser, between, task


class ZTNASUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health(self):
        self.client.get("/health", name="health")

    @task(2)
    def invalid_login(self):
        # Invalid login drives auth endpoint load without creating data growth.
        self.client.post(
            "/api/v1/auth/login",
            json={"username": "load_tester", "password": "invalid"},
            name="auth_login_invalid",
        )

    @task(1)
    def auth_me_unauthorized(self):
        self.client.get("/api/v1/auth/me", name="auth_me_unauthorized")
