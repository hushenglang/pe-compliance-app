# Financial Compliance News API

A FastAPI-based application for fetching, processing, and managing financial compliance news from Hong Kong regulatory authorities (HKMA and SFC). This application is designed specifically for private equity and financial institutions to stay updated with the latest regulatory developments.

## 🏗️ Architecture Overview

The application follows a clean architecture pattern with:
- **FastAPI** for REST API endpoints
- **SQLAlchemy** for database operations
- **MySQL** for data persistence
- **OpenRouter API** for AI-powered content summarization
- **Docker** for containerization
- **GitHub Actions** for CI/CD pipeline

## 📋 Features

### Core Functionality
- **Multi-Source News Fetching**: Automatically fetches compliance news from:
  - Hong Kong Monetary Authority (HKMA)
  - Securities and Futures Commission (SFC)
- **AI-Powered Summarization**: Uses OpenRouter API to generate intelligent summaries of regulatory content
- **Flexible Date Range Queries**: Fetch news for specific dates, date ranges, or recent periods
- **Structured Data Storage**: Stores news with metadata in MySQL database
- **RESTful API**: Clean API endpoints for integration with other systems

### Technical Features
- **Environment-Aware Configuration**: Supports development, staging, and production environments
- **Structured Logging**: JSON logging for production, detailed logging for development
- **Health Monitoring**: Built-in health check endpoints
- **Database Connection Pooling**: Efficient database connection management
- **CORS Support**: Configurable cross-origin resource sharing
- **Docker Support**: Containerized deployment with health checks

## 🛠️ Technology Stack

- **Backend**: FastAPI 0.115.14+, Python 3.13+
- **Database**: MySQL with SQLAlchemy ORM
- **AI/ML**: OpenRouter API for content summarization
- **Container**: Docker with multi-stage builds
- **Package Management**: UV for fast dependency management
- **Code Quality**: Ruff for linting, MyPy for type checking
- **CI/CD**: GitHub Actions with automated testing and deployment

## 📦 Installation

### Prerequisites
- Python 3.13 or higher
- MySQL database
- OpenRouter API key
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd pe-compliance-app
```

2. **Install UV package manager**:
```bash
pip install uv
```

3. **Install dependencies**:
```bash
uv sync
```

4. **Set up environment variables**:
Create a `.env` file in the project root:
```bash
# Database Configuration
MySQL_DATABASE_URL=mysql+pymysql://username:password@localhost:3306/compliance_db

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_FILE_PATH=logs/app.log
```

5. **Set up the database**:
```bash
# Create database schema
mysql -u username -p < sql/table_creation.sql
```

6. **Run the application**:
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 🐳 Docker Deployment

### Build and Run with Docker

1. **Build the Docker image**:
```bash
./build.sh
```

2. **Run the container**:
```bash
docker run -d \
  --name pe-compliance-app-container \
  -p 8000:8000 \
  --env-file .env \
  pe-compliance-app:latest
```

3. **View logs**:
```bash
docker logs -f pe-compliance-app-container
```

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
      - MySQL_DATABASE_URL=mysql+pymysql://username:password@db:3306/compliance_db
      - OPENROUTER_API_KEY=your_api_key_here
    depends_on:
      - db
    
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=compliance_db
      - MYSQL_USER=username
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./sql/table_creation.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  mysql_data:
```

Run with: `docker-compose up -d`

## 🔌 API Endpoints

### News Endpoints

#### Fetch Today's News
```http
POST /api/news/today
```
**Parameters:**
- `llm_enabled` (bool, optional): Enable AI summarization (default: true)
- `user` (string, optional): User initiating the request (default: "api")

**Response:** List of compliance news items for today

#### Fetch News by Date
```http
POST /api/news/date/{date}
```
**Parameters:**
- `date` (string): Date in YYYY-MM-DD format (e.g., "2024-12-15")
- `llm_enabled` (bool, optional): Enable AI summarization (default: true)
- `user` (string, optional): User initiating the request (default: "api")

**Response:** List of compliance news items for the specified date

#### Get Last 7 Days News
```http
GET /api/news/last7days
```
**Response:** List of compliance news items from the last 7 days

#### Get HTML Email Format
```http
GET /api/news/html-email/last7days
```
**Response:** HTML-formatted email content with last 7 days of news

### Health Endpoints

#### Health Check
```http
GET /api/health/
```
**Response:** 
```json
{
  "status": "healthy",
  "service": "financial-compliance-api"
}
```

### Response Format

All news endpoints return data in the following format:
```json
{
  "id": 1,
  "source": "HKMA",
  "issue_date": "2024-12-15T00:00:00Z",
  "title": "Regulatory Update on Digital Assets",
  "content": "Full content of the regulatory update...",
  "content_url": "https://www.hkma.gov.hk/...",
  "llm_summary": "AI-generated summary of the content...",
  "creation_date": "2024-12-15T10:00:00Z",
  "creation_user": "api"
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MySQL_DATABASE_URL` | MySQL database connection string | - | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI processing | - | Yes |
| `OPENROUTER_MODEL` | AI model to use | `openai/gpt-4o-mini` | No |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL | `https://openrouter.ai/api/v1` | No |
| `APP_ENV` | Application environment | `development` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_TO_FILE` | Enable file logging | `false` | No |
| `LOG_FILE_PATH` | Log file path | `logs/app.log` | No |

### Database Configuration

The application uses MySQL with the following schema:
- `compliance_news` table for storing news articles
- Support for multiple sources (HKMA, SFC)
- Full-text search capabilities
- Metadata tracking for audit purposes

## 🔧 Development

### Code Quality

The project uses several tools for code quality:

```bash
# Linting
uv run ruff check src/

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Project Structure

```
pe-compliance-app/
├── src/
│   ├── client/          # External API clients
│   ├── config/          # Configuration management
│   ├── constant/        # Application constants
│   ├── model/           # Database models
│   ├── repo/            # Data access layer
│   ├── router/          # API route handlers
│   ├── service/         # Business logic
│   └── util/            # Utility functions
├── sql/                 # Database schemas
├── Dockerfile           # Container configuration
├── pyproject.toml       # Project dependencies
└── build.sh            # Build script
```

## 🚀 Deployment

### CI/CD Pipeline

The application includes a comprehensive GitHub Actions pipeline:

1. **Code Quality**: Linting and type checking
2. **Build**: Docker image creation
3. **Security**: Container vulnerability scanning
4. **Deploy**: Automated deployment to ECS
5. **Monitoring**: Health checks and logging

### Production Deployment

For production deployment:

1. Set environment variables appropriately
2. Configure database with connection pooling
3. Set up log aggregation (ELK stack recommended)
4. Configure monitoring and alerting
5. Set up backup strategies for database

## 🔒 Security Considerations

- API keys are managed through environment variables
- Database connections use connection pooling
- Container runs as non-root user
- Regular security scanning of dependencies
- Input validation on all API endpoints

## 📊 Monitoring and Logging

- Structured JSON logging in production
- Detailed logging in development
- Health check endpoints for monitoring
- Request/response logging for debugging
- Database query logging (development only)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run code quality checks
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Consult the configuration documentation
4. Open an issue in the repository

## 📝 Changelog

### v0.1.0
- Initial release with HKMA and SFC news fetching
- AI-powered content summarization
- RESTful API endpoints
- Docker containerization
- CI/CD pipeline implementation
