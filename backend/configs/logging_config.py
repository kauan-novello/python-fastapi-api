import json
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.configs.settings import Settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.now(tz=ZoneInfo('UTC')).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    settings = Settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT.lower() == 'json':
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s [%(name)s] %(message)s'
            )
        )

    root.addHandler(handler)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
