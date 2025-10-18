# AI Recruiter Copilot

AI-powered recruitment copilot with multi-LLM orchestration for automated candidate sourcing, screening, and engagement.

## Overview

The AI Recruiter Copilot is a comprehensive recruitment automation system that leverages multiple Large Language Models (LLMs) to streamline the entire recruitment process. It provides intelligent agents for sourcing, screening, and managing candidates, with seamless integration to major job boards and ATS systems.

## Features

- **Multi-LLM Orchestration**: Support for OpenAI GPT-4 and Anthropic Claude
- **Intelligent Agents**:
  - **Recruiter Agent**: Manages job postings and orchestrates the recruitment process
  - **Sourcing Agent**: Generates search strategies and identifies candidate sources
  - **Screening Agent**: Evaluates candidates and generates interview questions
- **Resume Parsing**: Multi-format support (PDF, DOCX, TXT) with intelligent data extraction
- **API Integrations**: LinkedIn, Indeed, and Greenhouse ATS
- **Workflow Orchestration**: Coordinated multi-agent workflows
- **Pipeline Management**: Track candidates through recruitment stages
- **REST API**: FastAPI-based API for easy integration

## Architecture

```
ai-recruiter-copilot/
├── agents/              # AI agents for different recruitment tasks
│   ├── base_agent.py    # Base agent class
│   ├── recruiter_agent.py
│   ├── sourcing_agent.py
│   └── screening_agent.py
├── tools/               # Utility tools and integrations
│   ├── resume_parser.py
│   └── api_integrations.py
├── workflows/           # Orchestration and pipeline management
│   ├── orchestrator.py
│   └── pipeline.py
├── configs/             # Configuration management
│   ├── llm_config.py
│   └── app_config.py
├── tests/               # Test suite
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker configuration
├── Dockerfile           # Container definition
└── .env.example         # Environment variables template
```

## Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- OpenAI API key and/or Anthropic API key

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/devejya56/ai-recruiter-copilot.git
   cd ai-recruiter-copilot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

### Docker Setup

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PgAdmin: http://localhost:5050

## Usage

### API Endpoints

#### Create Job Posting
```bash
curl -X POST "http://localhost:8000/jobs/create" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python Developer with 5+ years experience",
    "location": "San Francisco"
  }'
```

#### Screen Candidate
```bash
curl -X POST "http://localhost:8000/candidates/screen" \
  -F "resume=@/path/to/resume.pdf" \
  -F 'job_requirements={"skills": ["python", "aws"]}'
```

#### Get Market Insights
```bash
curl -X POST "http://localhost:8000/market/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["python", "machine learning"],
    "location": "Remote"
  }'
```

### Python SDK

```python
from workflows.orchestrator import RecruitmentOrchestrator

# Initialize orchestrator
orchestrator = RecruitmentOrchestrator()

# Create job and get sourcing strategy
result = orchestrator.create_job_and_source(
    job_description="Senior Software Engineer...",
    location="San Francisco"
)

# Screen a candidate
screening_result = orchestrator.screen_candidate(
    resume_file_path="resume.pdf",
    job_requirements=result["job_requirements"]
)

# Get market insights
insights = orchestrator.generate_market_insights(
    skills=["python", "aws"],
    location="Remote"
)
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- **LLM Configuration**: API keys, models, temperature, max tokens
- **Database**: PostgreSQL connection string
- **Redis**: Cache and queue configuration
- **External APIs**: LinkedIn, Indeed, Greenhouse API keys
- **Email**: SMTP configuration for notifications

### LLM Provider Selection

Choose between OpenAI and Anthropic:

```python
# In .env
DEFAULT_LLM_PROVIDER=openai  # or 'anthropic'
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

## Development

### Project Structure

- **agents/**: AI agents implementing specific recruitment tasks
- **tools/**: Reusable tools for parsing, integrations, etc.
- **workflows/**: High-level orchestration logic
- **configs/**: Configuration management
- **tests/**: Comprehensive test suite

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement required methods: `process()`, `name`, `description`
3. Add the agent to the orchestrator
4. Write tests for the new agent

### Adding New Integrations

1. Create integration class inheriting from `BaseAPIIntegration`
2. Implement required methods
3. Add configuration in `configs/`
4. Update `.env.example`

## Deployment

### Production Considerations

- Use environment-specific `.env` files
- Enable SSL/TLS for API endpoints
- Configure proper database backups
- Set up monitoring and logging
- Use production-grade LLM API keys with appropriate rate limits
- Implement proper authentication and authorization

### Scaling

- Use Redis for caching and job queues
- Deploy multiple worker instances
- Configure load balancing
- Use managed database services
- Implement rate limiting

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- Built with LangChain for LLM orchestration
- Powered by OpenAI GPT-4 and Anthropic Claude
- Uses FastAPI for high-performance API
- Resume parsing with PyPDF2 and pdfplumber
