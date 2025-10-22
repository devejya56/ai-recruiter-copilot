# AI Recruiter Copilot

AI-powered recruitment copilot with multi-LLM orchestration for automated candidate sourcing, screening, and engagement.

## 🚀 Project Overview

AI Recruiter Copilot is an intelligent recruitment automation system that leverages multiple Large Language Models (LLMs) to streamline the entire hiring process. The system orchestrates various AI agents to handle candidate sourcing, resume screening, skill assessment, and automated engagement, significantly reducing time-to-hire while improving candidate quality.

Built for hackathon submission, this project demonstrates the power of multi-agent AI systems in revolutionizing traditional recruitment workflows.

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

## 🔑 Environment Configuration

Create a `.env` file in the root directory with the following configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI Configuration
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key_here

# Database Configuration (Optional)
DATABASE_URL=sqlite:///recruiter.db

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Note**: Never commit your `.env` file to version control. Add it to `.gitignore`.

## 🚀 How to Run

### Basic Usage

```bash
# Run the main recruiter agent
python recruiter_agent.py
```

### Advanced Usage

```bash
# Run with specific job description
python recruiter_agent.py --job-file job_description.json

# Run with custom configuration
python recruiter_agent.py --config custom_config.yaml

# Run in interactive mode
python recruiter_agent.py --interactive
```

## 📊 Expected Input/Output

### Input Format

Provide a job description in JSON format:

```json
{
  "title": "Senior Software Engineer",
  "company": "Tech Corp",
  "requirements": [
    "5+ years Python experience",
    "Experience with AI/ML frameworks",
    "Strong problem-solving skills"
  ],
  "nice_to_have": [
    "Open source contributions",
    "Leadership experience"
  ],
  "location": "Remote",
  "salary_range": "$120k-$180k"
}
```

### Output Format

The system generates:

```json
{
  "candidates": [
    {
      "name": "John Doe",
      "score": 92,
      "profile_url": "https://linkedin.com/in/johndoe",
      "match_reasons": [
        "8 years Python experience",
        "Contributed to TensorFlow",
        "Led team of 5 engineers"
      ],
      "email_draft": "Personalized outreach message..."
    }
  ],
  "summary": {
    "total_screened": 150,
    "qualified": 25,
    "contacted": 10
  }
}
```

## 🔄 Workflow Summary

1. **Job Analysis**: Parse and understand job requirements using GPT-4
2. **Candidate Sourcing**: Search platforms using Composio integrations
3. **Resume Screening**: Extract and analyze candidate information with Claude
4. **Skills Matching**: Score candidates against requirements using Gemini
5. **Ranking**: Sort candidates by fit score and availability
6. **Engagement**: Generate personalized outreach emails
7. **Follow-up**: Track responses and schedule interviews
8. **Analytics**: Generate recruitment pipeline reports

## 🤖 Agents Breakdown

### 1. Sourcing Agent
- **Model**: GPT-4
- **Function**: Discovers candidates across multiple platforms
- **Tools**: LinkedIn API, GitHub API, Indeed scraper

### 2. Screening Agent
- **Model**: Claude
- **Function**: Parses resumes and extracts structured data
- **Tools**: PDF parser, NLP extraction, entity recognition

### 3. Assessment Agent
- **Model**: Gemini
- **Function**: Evaluates technical and soft skills
- **Tools**: Skill taxonomy, scoring algorithms

### 4. Engagement Agent
- **Model**: GPT-4
- **Function**: Creates personalized communication
- **Tools**: Email templates, tone analyzer

### 5. Orchestrator Agent
- **Model**: Multi-LLM
- **Function**: Coordinates all agents and manages workflow
- **Tools**: State management, decision routing

## 🤝 Contribution Guide

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest tests/
   ```
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation as needed

## 👥 Team Info

**Project Lead**: Devejya

**Contributors**:
- Devejya - Lead Developer & AI Architect

This project was built as part of [Hackathon Name] to demonstrate innovative applications of AI in recruitment.

## 📧 Contact

- **GitHub**: [@devejya56](https://github.com/devejya56)
- **Project Repository**: [ai-recruiter-copilot](https://github.com/devejya56/ai-recruiter-copilot)
- **Issues**: [Report bugs or request features](https://github.com/devejya56/ai-recruiter-copilot/issues)

For questions or collaboration opportunities, please open an issue or reach out via GitHub.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

```
Copyright (c) 2025 Devejya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

## 🎯 Future Enhancements

- [ ] Video interview scheduling automation
- [ ] Integration with ATS systems
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Chrome extension for quick candidate evaluation

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Anthropic for Claude API
- Google for Gemini API
- Composio for integration platform
- All contributors and supporters

---

**Built with ❤️ for better recruitment experiences**
