import csv
import datetime
from typing import Dict, Any

class ChatLogger:
    def __init__(self, config):
        self.log_file = config.chat_log_path
        self._init_log_file()

    def _init_log_file(self):
        try:
            with open(self.log_file, 'a+', newline='', encoding='utf-8') as f:
                f.seek(0)
                header = f.read(6)
                if not header.startswith('user_id'):
                    writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
                    writer.writeheader()
        except Exception as e:
            print(f"Error initializing log file: {str(e)}")

    async def log_message(self, message_data: Dict[str, Any]):
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
                writer.writerow(message_data)
        except Exception as e:
            print(f"Error logging message: {str(e)}")

    def _get_fieldnames(self):
        return [
            'timestamp',
            'user_id',
            'username',
            'message_text',
            'bot_response',
            'response_time',
            'total_tokens',
            'cost'
        ]