from __future__ import annotations

from collections.abc import Callable
from typing import Union

import httpx
import requests


class CortexAgent:
    def __init__(
        self,
        account: str,
        agent_name: str,
        database: str,
        schema: str,
        token: Union[str, Callable[[], str]],
    ) -> None:
        self.account = account
        self.agent_name = agent_name
        self.database = database
        self.schema = schema
        self.token = token

    def _get_token(self) -> str:
        return self.token() if callable(self.token) else self.token

    @property
    def _host(self) -> str:
        return f"{self.account.replace('_', '-')}.snowflakecomputing.com"

    @property
    def _url(self) -> str:
        return (
            f"https://{self._host}"
            f"/api/v2/databases/{self.database}/schemas/{self.schema}"
            f"/agents/{self.agent_name}:run"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _payload(question: str) -> dict:
        return {
            "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
            "stream": False,
        }

    @staticmethod
    def _parse_response(data: dict) -> str:
        for item in data.get("content", []):
            if item.get("type") == "text":
                return item["text"]
        return str(data)

    def run(self, question: str) -> str:
        response = requests.post(
            self._url,
            headers=self._headers(),
            json=self._payload(question),
            timeout=120,
        )
        response.raise_for_status()
        return self._parse_response(response.json())

    async def arun(self, question: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._url,
                headers=self._headers(),
                json=self._payload(question),
                timeout=120,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
