# AI Recruiter Copilot

AI-powered recruitment copilot with multi-LLM orchestration for automated candidate sourcing, screening, and engagement.

## 🚀 Project Overview

AI Recruiter Copilot is an intelligent recruitment automation system that leverages multiple Large Language Models (LLMs) to streamline the entire hiring process. The system orchestrates various AI agents to handle candidate sourcing, resume screening, skill assessment, and automated engagement, significantly reducing time-to-hire while improving candidate quality.

## ✨ Features

- **Multi-LLM Orchestration**: Intelligent routing between different LLMs (GPT-4, Claude, Gemini) based on task requirements
- **Automated Candidate Sourcing**: AI-powered search across multiple platforms (LinkedIn, GitHub, job boards)
- **Intelligent Resume Screening**: Automated parsing and ranking of candidate profiles against job requirements
- **Skills Assessment**: Dynamic evaluation of technical and soft skills using AI-driven analysis
- **Automated Engagement**: Personalized email outreach and follow-up communication
- **Recruiter Agent**: Dedicated agent in `recruiter_agent.py` for end-to-end recruitment workflow
- **Composio Integration**: Seamless integration with external tools and platforms
- **Real-time Analytics**: Dashboard for tracking recruitment metrics and pipeline status

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Anthropic API key (for Claude)
- Google AI API key (for Gemini)
- Composio account and API key
- Internet connection for API calls

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/devejya56/ai-recruiter-copilot.git
   cd ai-recruiter-copilot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

### .env File Setup

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI Configuration
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key_here

# Database Configuration (if applicable)
DATABASE_URL=sqlite:///./recruitment.db

# Email Configuration (for automated outreach)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

**Important**: Ensure all API keys are valid and have sufficient credits/quota for the workflow to run smoothly.

## 🏃 How to Run

### Running the Main Workflow

1. **Execute the main recruitment flow**
   ```bash
   python main.py
   ```

2. **Run specific agent workflows**
   ```bash
   python agents/workflows/recruitment_flow.py
   ```

3. **Test the recruiter agent**
   ```bash
   python recruiter_agent.py
   ```

### Expected Input

The system expects:
- Job description or requirements (text file or direct input)
- Target platforms for candidate sourcing
- Minimum qualification criteria
- Number of candidates to screen

### Expected Output

- **Candidate Reports**: Ranked list of candidates with scores and summaries
- **Screening Results**: Detailed analysis of each candidate's fit
- **Engagement Logs**: Record of automated communications sent
- **Analytics Dashboard**: Visual representation of recruitment pipeline
- **Export Options**: CSV/JSON files with candidate data

## 🔄 Workflow Summary

1. **Input Phase**: User provides job requirements and search parameters
2. **Sourcing Phase**: AI agents search multiple platforms for potential candidates
3. **Screening Phase**: Automated resume parsing and initial qualification check
4. **Assessment Phase**: Deep analysis of skills, experience, and cultural fit
5. **Ranking Phase**: ML-powered scoring and ranking of candidates
6. **Engagement Phase**: Automated personalized outreach to top candidates
7. **Tracking Phase**: Monitor responses and update pipeline status
8. **Reporting Phase**: Generate comprehensive recruitment analytics

### Agent Orchestration

The system uses multiple specialized agents:
- **Sourcing Agent**: Finds candidates across platforms
- **Screening Agent**: Filters candidates based on requirements
- **Assessment Agent**: Evaluates technical and soft skills
- **Communication Agent**: Handles outreach and follow-ups
- **Recruiter Agent**: Orchestrates the entire workflow (`recruiter_agent.py`)

## 🤝 How to Contribute

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 👥 Team Info

**Project Lead**: [Your Name]
**Development Team**: [Team Member Names]
**Hackathon**: [Hackathon Name]
**Category**: AI/ML, Recruitment Technology

### Contact Information

- **GitHub**: [@devejya56](https://github.com/devejya56)
- **Email**: contact@ai-recruiter-copilot.com
- **Project Repository**: [ai-recruiter-copilot](https://github.com/devejya56/ai-recruiter-copilot)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Anthropic for Claude API
- Google for Gemini API
- Composio for integration platform
- All contributors and hackathon organizers

## 📊 Project Status

✅ Structurally ready for hackathon submission
✅ Core agents implemented
✅ Multi-LLM orchestration functional
✅ End-to-end workflow tested

---

*Built with ❤️ for efficient and fair recruitment*
