# customer-support-agent

Graph workflow agent for shipping company customer support. Routes customer queries based on topic:
- **Shipping-related** queries (rates, tracking, delivery, returns) → Shipping FAQ agent
- **Unrelated** queries → Polite decline message

Built with **ADK 2.0 Workflows** and **Groq LLM**.

Agent generated with `agents-cli` version `0.5.0`

## Project Structure

```
customer-support-agent/
├── app/
│   ├── agent.py               # Graph workflow definition
│   ├── groq_utils.py          # Groq API integration
│   ├── .env                   # Environment variables (includes GROQ_API_KEY)
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
└── pyproject.toml             # Project dependencies
```

## Graph Workflow

```
START → classify_query → shipping_faq_agent (if shipping-related)
                      → decline_politely (if unrelated)
```

1. **classify_query**: Determines if query is shipping-related
2. **shipping_faq_agent**: Answers shipping questions using Groq LLM
3. **decline_politely**: Returns friendly decline message for non-shipping topics

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) and add your key to `app/.env`


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
