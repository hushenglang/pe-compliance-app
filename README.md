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
   ```bash
   # OpenRouter Configuration (used instead of direct OpenAI)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_MODEL=openai/gpt-4o-mini
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   
   # Database Configuration
   MySQL_DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
   
   # Optional: Application Environment
   APP_ENV=production
   LOG_LEVEL=INFO
   ```
   
   **Environment Variable Loading (Production-Ready)**:
   - **Development**: Automatically loads `.env` file when `APP_ENV=development` (default)
   - **Production**: Only uses environment variables from container runtime (no `.env` file loading)
   - **Docker**: Environment variables passed via `-e` flag or `--env-file` override all defaults
   - **Precedence**: Docker env vars > .env file (dev only) > Dockerfile defaults

3. **Database Setup**:
   ```bash
   # Run the SQL script to create necessary tables
   mysql -u username -p database_name < doc/table_creation.sql
   ```

## Docker Deployment

### Option 1: Using Docker Compose (Recommended for Development)
```bash
# For development with .env file loading (default)
docker-compose up -d

# For production mode (environment variables only)
APP_ENV=production docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Docker Commands
```bash
# Build the image
./build.sh

# Run with .env file
docker run -d --name pe-compliance-app -p 8000:8000 --env-file .env pe-compliance-app:latest

# Or run with individual environment variables (PRODUCTION)
docker run -d --name pe-compliance-app -p 8000:8000 \
  -e APP_ENV="production" \
  -e OPENROUTER_API_KEY="your_api_key" \
  -e MySQL_DATABASE_URL="your_db_url" \
  pe-compliance-app:latest
```

### Environment Variable Management in Docker

1. **Development**: Use `--env-file .env` for local development with `APP_ENV=development`
2. **Production**: Pass environment variables directly using `-e` flags with `APP_ENV=production`
3. **CI/CD**: Use secrets management (e.g., GitHub Secrets, AWS Secrets Manager)

**Security Best Practices**:
- ✅ `.env` files are **only loaded in development** (when `APP_ENV=development`)
- ✅ **Production mode** (`APP_ENV=production`) **never** loads `.env` files
- ✅ Never commit `.env` files to version control
- ✅ Use Docker secrets or orchestration platform secrets for production
- ✅ Rotate API keys regularly and validate environment variables on startup

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
