from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def load_project_env():
    load_dotenv(dotenv_path=ENV_PATH)


def _get_float_env(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc


def _get_csv_env(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    def __init__(self):
        load_project_env()
        self.ebay_api_token = os.getenv("EBAY_API_TOKEN")
        self.ebay_client_id = os.getenv("EBAY_CLIENT_ID")
        self.ebay_client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.ebay_request_timeout = _get_float_env("EBAY_REQUEST_TIMEOUT", 15.0)
        self.http_request_timeout = _get_float_env("HTTP_REQUEST_TIMEOUT", 10.0)
        self.cors_allowed_origins = _get_csv_env(
            "CORS_ALLOWED_ORIGINS",
            [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "https://www.ebay.com",
            ],
        )
        cors_allowed_origin_regex = os.getenv(
            "CORS_ALLOWED_ORIGIN_REGEX",
            r"^chrome-extension://[a-zA-Z0-9_-]+$",
        )
        self.cors_allowed_origin_regex = cors_allowed_origin_regex or None

    @property
    def ebay_credentials_configured(self):
        return bool(self.ebay_client_id and self.ebay_client_secret)


def get_settings():
    return Settings()
