import requests


class MessengerService:

    API_URL = "https://graph.facebook.com/v18.0/me/messages"

    def __init__(self, page_access_token: str):
        self.token = page_access_token

    def send_message(self, recipient_id: str, text: str) -> dict:
        url = f"{self.API_URL}?access_token={self.token}"
        data = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": {"text": text},
        }
        response = requests.post(url, json=data)
        return response.json()

    @staticmethod
    def verify_webhook(
        mode: str, token: str, challenge: str, verify_token: str
    ):
        if mode and token and mode == "subscribe" and token == verify_token:
            return challenge, 200
        return "Verification failed", 403
