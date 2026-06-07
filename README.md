# My Assistant v1

An autonomous AI-powered task assistant built with LangGraph and LangChain. This agent orchestrates multi-step workflows to extract, research, manage, and summarize tasks while integrating with Notion for persistent task management.

## 🚀 Features

- **Autonomous Workflow**: Multi-stage agentic pipeline (greet → extract → research → manage → update → summarize)
- **Notion Integration**: Seamlessly read/write tasks to your Notion database
- **Web Search**: Leverage Tavily search for research and data gathering
- **Multi-LLM Support**: Compatible with OpenAI, Google Gemini, Groq, Ollama, and OpenRouter models
- **State Management**: Built-in agent state tracking and memory management
- **Logging**: Comprehensive logging system for debugging and monitoring
- **Docker Ready**: Container support for easy deployment
- **Configurable**: YAML-based configuration for agent settings and LLM parameters

## 📋 Requirements

- Python 3.10 or higher
- Notion API token (for database integration)
- API keys for your preferred LLM provider(s)
- Tavily API key (optional, for search functionality)

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd d:\my_assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # On Windows PowerShell
# or
source .venv/bin/activate    # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -e .
```

Or using the pyproject.toml directly:

```bash
pip install gradio langchain langchain-community langgraph tavily-python python-dotenv
```

### 3. Environment Setup

Create a `.env` file in the project root:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_key
NOTION_ACCESS_TOKEN=your_notion_token
TAVILY_API_KEY=your_tavily_key

# Optional: For other LLM providers
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
```

## 📁 Project Structure

```
my_assistant/
├── src/
│   ├── agents/           # Agent definitions and workflows
│   │   ├── assistant_agent.py   # Main autonomous agent
│   │   └── agent_state.py       # State management for agent
│   ├── core/             # Core functionality
│   │   ├── memory.py     # Memory management
│   │   └── reasoning.py  # Reasoning logic
│   ├── tools/            # Tool implementations
│   │   ├── notion_tools.py      # Notion API integration
│   │   └── search_tavily.py     # Tavily search integration
│   ├── schemas/          # Data schemas
│   │   └── agent_task.py # Task schema definitions
│   └── utils/            # Utility functions
│       └── logger.py     # Logging configuration
├── config/
│   └── agent_config.yaml # Agent configuration
├── data/
│   └── memory/           # Agent memory and persistence
├── notebooks/
│   └── notion_apis.ipynb # Notion API exploration
├── tests/
│   └── test_agents.py    # Unit tests
├── main.py              # Entry point
├── pyproject.toml       # Project dependencies
├── Dockerfile           # Container configuration
└── README.md           # This file
```

## ⚙️ Configuration

The agent is configured via `config/agent_config.yaml`:

```yaml
agent:
  name: 'AutonomousTaskAgent'
  model: 'gpt-4o'
  temperature: 0.1
  max_retries: 3
```

**Available Models**:
- `gpt-4o`, `gpt-4-turbo` (OpenAI)
- `gemini-pro` (Google Gemini)
- `groq-models` (Groq)
- `ollama-models` (Local)
- `openrouter-models` (OpenRouter)

## 🚀 Usage

### Run the Assistant

```bash
python main.py
```

### Using the Agent Programmatically

```python
from src.agents.assistant_agent import AssistantAgent

agent = AssistantAgent()
result = agent.run()
```

### With Gradio UI (if configured)

The project includes Gradio for web-based interaction:

```python
import gradio as gr
# UI implementation in development
```

## 🐳 Docker Usage

Build and run with Docker:

```bash
docker build -t my-assistant:v1 .
docker run -e NOTION_ACCESS_TOKEN=your_token -e OPENAI_API_KEY=your_key my-assistant:v1
```

## 📊 Workflow Stages

1. **Greet User**: Initialize and greet the user
2. **Extract Data**: Parse and extract structured data from input
3. **Researcher**: Conduct research using Tavily search and LLM analysis
4. **Manager**: Prioritize and organize tasks
5. **Updater**: Sync changes to Notion database
6. **Summarizer**: Generate summary and insights

## 🔧 Notion Integration

The assistant reads from and writes to your Notion database. Configure your database ID in:

```
data/memory/Monthly-planner-2026/master.json
```

Required metadata:
```json
{
  "metadata": {
    "master_tasks_db_id": "your_notion_db_id"
  }
}
```

## 📝 Testing

Run the test suite:

```bash
pytest tests/
```

## 📦 Dependencies

Key dependencies:
- **LangChain**: LLM orchestration and tools
- **LangGraph**: Agentic workflow graphs
- **Tavily**: Web search integration
- **Gradio**: Web UI framework
- **Python-dotenv**: Environment configuration

See `pyproject.toml` for the complete dependency list.

## 🐛 Troubleshooting

### API Key Issues
- Ensure all required API keys are set in `.env`
- Check that API keys have proper permissions

### Notion Connection
- Verify your Notion token is valid
- Ensure the database ID matches your target database
- Check that the agent has access to the Notion database

### LLM Issues
- Verify your LLM API key is correct
- Check model availability in your subscription tier
- Review token limits and rate limits

## 📚 Resources

- [LangChain Documentation](https://python.langchain.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)
- [Notion API](https://developers.notion.com)
- [Tavily Search API](https://tavily.com)

## 📄 License

Add your license information here.

## 👤 Author

Created for autonomous task management and AI-powered workflow automation.

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-07
