from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parent / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_port: int = 8040
    llm_provider: str = "fake"
    enrichment_provider: str = "fakeweb"
    fakeweb_base_url: str = "http://127.0.0.1:8088"
    mail_host: str = "127.0.0.1"
    mail_port: int = 1025
    mail_from: str = "sdr@northbeam.example"
    sender_name: str = "Alex Rivera"
    approval_channel: str = "dashboard"
    unsubscribe_base_url: str = "http://127.0.0.1:8040"
    store_path: str = "data/store.json"
    daily_send_cap: int = 50
    domain_send_cap: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}
