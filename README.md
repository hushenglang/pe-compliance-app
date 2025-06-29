# PE Company Compliance Application

A comprehensive application for financial compliance news crawling and AI-powered analysis.

## Features

- **SFC News Crawler**: Scrapes compliance news from Hong Kong Securities and Futures Commission (SFC)
- **AI Agent Service**: Uses GPT-4o-mini via OpenRouter for financial compliance analysis
- **Database Storage**: Stores compliance news with metadata in MySQL database
- **RESTful API**: Provides endpoints for accessing and managing compliance data

## Components

### SFC News Service
- Fetches compliance news from SFC official website
- Stores news content with full metadata
- Supports date-based queries and filtering

### Agent Service
- Powered by OpenAI Agent SDK using GPT-4o-mini via OpenRouter
- Specialized system prompt for financial compliance analysis
- Simple LLM calls without tools or handoffs
- Configurable system prompts

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

2. **Environment Variables**:
   Create a `.env` file with the following variables:
   ```
   # Database Configuration
   MySQL_DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
   
   # OpenRouter API Key (for Agent Service)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. **Database Setup**:
   ```bash
   # Run the SQL script to create necessary tables
   mysql -u username -p database_name < doc/table_creation.sql
   ```

## Usage

### SFC News Service Example
```python
from service.sfc_news_service import SfcNewsService

# Fetch today's news
with SfcNewsService() as service:
    news_items = service.fetch_and_persist_today_news()
    print(f"Found {len(news_items)} news items")
```

### Agent Service Example
```python
from service.agent_service import AgentService

# Initialize agent with default financial compliance prompt
agent = AgentService()

# Generate response
response = agent.generate_response("What are key SFC compliance requirements?")
print(response)

# Update system prompt
agent.update_system_prompt("You are a specialized Hong Kong SFC regulatory expert...")
```

### Running Examples
```bash
python src/example_usage.py
```

## API Keys

### OpenRouter API Key
1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Create an API key
3. Set the `OPENROUTER_API_KEY` environment variable

## Project Structure

```
src/
├── client/          # External API clients (SFC)
├── config/          # Database configuration
├── model/           # Data models
├── repo/            # Repository layer
├── service/         # Business logic services
│   ├── sfc_news_service.py    # SFC news operations
│   └── agent_service.py       # AI agent operations
└── util/            # Utility functions
```

## Dependencies

- Python 3.13+
- SQLAlchemy 2.0+
- OpenAI Agents SDK
- Requests
- PyMySQL
- Pydantic

## License

This project is licensed under the MIT License.
