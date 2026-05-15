import requests


class NotificationService:

    def __init__(
        self,
        telegram_bot_token: str | None = None,
        telegram_chat_id: str | None = None,
    ):
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def send_telegram_alert(
        self, numero: str, sender_id: str = ""
    ) -> bool:
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print("[!] Telegram not configured, skipping alert")
            return False

        url = (
            f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        )
        text = (
            f"📢 *Nuevo lead de Messenger!*\n"
            f"👤 ID: `{sender_id}`\n"
            f"📞 Número: `{numero}`"
        )
        data = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.ok:
                print(f"[*] Telegram alert sent for {numero}")
                return True
            print(
                f"[!] Telegram error {response.status_code}: {response.text}"
            )
            return False
        except Exception as e:
            print(f"[!] Telegram exception: {e}")
            return False
