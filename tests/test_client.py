from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import requests

from snowflake_cortex_agents import CortexAgent


@pytest.fixture
def agent():
    return CortexAgent(
        account="test-account",
        agent_name="test_agent",
        database="TEST_DB",
        schema="TEST_SCHEMA",
        token="test-token",
    )


@pytest.fixture
def agent_with_callable():
    return CortexAgent(
        account="test-account",
        agent_name="test_agent",
        database="TEST_DB",
        schema="TEST_SCHEMA",
        token=lambda: "refreshed-token",
    )


def _mock_response(text="Revenue is $4.2M"):
    mock = MagicMock()
    mock.json.return_value = {"content": [{"type": "text", "text": text}]}
    mock.raise_for_status = MagicMock()
    return mock


class TestRun:
    def test_returns_answer(self, agent):
        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()) as mock_post:
            result = agent.run("What is total revenue?")

        assert result == "Revenue is $4.2M"
        mock_post.assert_called_once()

    def test_raises_on_http_error(self, agent):
        mock = MagicMock()
        mock.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

        with patch("snowflake_cortex_agents.client.requests.post", return_value=mock):
            with pytest.raises(requests.HTTPError):
                agent.run("What is total revenue?")


class TestEndpoint:
    def test_correct_url(self, agent):
        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()) as mock_post:
            agent.run("test")

        url = mock_post.call_args[0][0]
        assert "test-account.snowflakecomputing.com" in url
        assert "/api/v2/databases/TEST_DB/schemas/TEST_SCHEMA/agents/test_agent:run" in url

    def test_underscore_replaced_in_host(self):
        agent = CortexAgent(
            account="myorg-myaccount_aws1",
            agent_name="test_agent",
            database="DB",
            schema="SCH",
            token="tok",
        )
        assert agent._host == "myorg-myaccount-aws1.snowflakecomputing.com"

    def test_correct_payload(self, agent):
        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()) as mock_post:
            agent.run("What are top accounts?")

        payload = mock_post.call_args[1]["json"]
        assert payload == {
            "messages": [{"role": "user", "content": [{"type": "text", "text": "What are top accounts?"}]}],
            "stream": False,
        }


class TestAuth:
    def test_string_token(self, agent):
        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()) as mock_post:
            agent.run("test")

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-token"

    def test_callable_token(self, agent_with_callable):
        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()) as mock_post:
            agent_with_callable.run("test")

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer refreshed-token"

    def test_callable_invoked_each_request(self, agent_with_callable):
        call_count = 0

        def counting_token():
            nonlocal call_count
            call_count += 1
            return f"token-{call_count}"

        agent_with_callable.token = counting_token

        with patch("snowflake_cortex_agents.client.requests.post", return_value=_mock_response()):
            agent_with_callable.run("first")
            agent_with_callable.run("second")

        assert call_count == 2


class TestArun:
    @pytest.mark.asyncio
    async def test_returns_answer(self, agent):
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": [{"type": "text", "text": "Async answer"}]}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("snowflake_cortex_agents.client.httpx.AsyncClient", return_value=mock_client):
            result = await agent.arun("What is total revenue?")

        assert result == "Async answer"

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, agent):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("snowflake_cortex_agents.client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await agent.arun("What is total revenue?")
