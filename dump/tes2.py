import threading
import time
import requests

class BillingSystem:
    def __init__(self):
        self.users = {}  # {user_id: {'duration': seconds, 'timer': Timer}}

    def add_user(self, user_id, duration_seconds):
        if user_id in self.users:
            self.users[user_id]['timer'].cancel()  # Cancel existing timer if any
        self.users[user_id] = {'duration': duration_seconds}
        self.users[user_id]['timer'] = threading.Timer(duration_seconds, self._timeout, args=[user_id])
        self.users[user_id]['timer'].start()
        print(f"User {user_id} added with duration {duration_seconds} seconds.")

    def _timeout(self, user_id):
        try:
            response = requests.get(f"http://127.0.0.1:5000/user{user_id}/timeout")
            print(f"Timeout signal sent for user {user_id}. Response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send timeout signal for user {user_id}: {e}")
        finally:
            if user_id in self.users:
                del self.users[user_id]

    def remove_user(self, user_id):
        if user_id in self.users:
            self.users[user_id]['timer'].cancel()
            del self.users[user_id]
            print(f"User {user_id} removed.")

# Example usage
if __name__ == "__main__":
    billing = BillingSystem()
    # Add users with durations
    billing.add_user(1, 10)  # User 1, 10 seconds
    billing.add_user(2, 20)  # User 2, 20 seconds
    billing.add_user(3, 30)  # User 2, 20 seconds
    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        for user in list(billing.users.keys()):
            billing.remove_user(user)
