from locust import HttpUser, task, between
import random

PROVA_CODE = """
arr = [64, 34, 25, 12, 22, 11, 90]

n = len(arr)
for i in range(n):
    for j in range(0, n - i - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]

print(arr)
"""

class ProvaUser(HttpUser):
    wait_time = between(0.5, 2.0)  # think time

    @task
    def execute_prova(self):
        payload = {
            "name": "stress-test",
            "prova_id": random.randint(1, 1_000_000),
            "prova_data": PROVA_CODE
        }

        with self.client.post(
            "/prova_execute",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(response.text)
