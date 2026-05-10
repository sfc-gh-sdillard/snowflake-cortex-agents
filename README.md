# snowflake-cortex-agents

Python client for [Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents).

## Installation

```bash
pip install snowflake-cortex-agents
```

## Usage

```python
from snowflake_cortex_agents import CortexAgent

agent = CortexAgent(
    account="myorg-myaccount",
    agent_name="revenue_analyst",
    database="ANALYTICS",
    schema="PUBLIC",
    token="my-pat-token",  # or token=my_refresh_function
)

response = agent.run("What are the top 5 accounts by consumption?")
print(response)
```

### Async

```python
response = await agent.arun("What are the top 5 accounts?")
```

### Token Refresh

Pass a callable to `token` for automatic refresh:

```python
agent = CortexAgent(
    ...,
    token=lambda: get_fresh_token(),
)
```

### Framework Integration

Works with any agentic framework — just call `agent.run()`:

```python
# CrewAI
from crewai.tools import tool

@tool
def ask_snowflake(question: str) -> str:
    """Ask a question to the Snowflake Cortex Agent."""
    return agent.run(question)

# LangChain
from langchain_core.tools import tool

@tool
def ask_snowflake(question: str) -> str:
    """Ask a question to the Snowflake Cortex Agent."""
    return agent.run(question)

# Or just call it directly in any pipeline
result = agent.run("How many active users last month?")
```

## Development

```bash
git clone https://github.com/samdillard/snowflake-cortex-agents.git
cd snowflake-cortex-agents
uv sync --all-extras
uv run pytest
uv run pyright
```
