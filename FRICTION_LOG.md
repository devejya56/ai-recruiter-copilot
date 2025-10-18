# Friction Log

This document tracks implementation challenges, decisions, and learnings during the development of the AI Recruiter Copilot.

## Project Setup Phase

### 2024-01-15: Initial Project Structure
- **Challenge**: Designing a scalable architecture for multi-LLM orchestration
- **Decision**: Adopted a modular approach with separate agents, tools, and workflows directories
- **Rationale**: This structure allows for easy extension and independent testing of components

### LLM Integration
- **Challenge**: Managing multiple LLM providers (OpenAI, Anthropic) with different APIs
- **Decision**: Created a unified LLM manager in configs/ to abstract provider differences
- **Rationale**: Simplifies switching between providers and enables fallback mechanisms

### Resume Parsing
- **Challenge**: Supporting multiple resume formats (PDF, DOCX, plain text)
- **Decision**: Implemented a multi-format parser with dedicated handlers for each type
- **Rationale**: Ensures robust parsing regardless of candidate submission format
- **Friction Point**: PyPDF2 struggles with complex PDFs; pdfplumber added as backup

### Agent Design
- **Challenge**: Coordinating multiple agents (recruiter, sourcing, screening) without conflicts
- **Decision**: Implemented a workflow orchestrator with clear agent responsibilities
- **Rationale**: Prevents redundant work and ensures consistent candidate evaluation

### Testing Strategy
- **Challenge**: Testing LLM-dependent code without excessive API costs
- **Decision**: Implemented mock LLM responses and test fixtures
- **Rationale**: Enables fast, cost-effective testing while maintaining coverage

## Data Management

### Candidate Data Storage
- **Challenge**: Storing and retrieving candidate information efficiently
- **Decision**: PostgreSQL for structured data with SQLAlchemy ORM
- **Rationale**: Provides ACID compliance and complex query support

### Caching Strategy
- **Challenge**: Reducing duplicate LLM calls for similar queries
- **Decision**: Redis caching layer for LLM responses and parsed resumes
- **Rationale**: Significantly reduces API costs and improves response times

## Security and Privacy

### Data Privacy
- **Challenge**: Handling sensitive candidate information (PII)
- **Decision**: Implemented data encryption and access controls
- **Rationale**: GDPR/CCPA compliance and candidate trust

### API Key Management
- **Challenge**: Secure storage of multiple API keys
- **Decision**: Environment variables with .env.example template
- **Rationale**: Prevents accidental credential exposure in version control

## Integration Challenges

### External APIs
- **Challenge**: Different rate limits and response formats across job boards
- **Decision**: Implemented adapter pattern for each external API
- **Rationale**: Isolates integration complexity and simplifies testing

### Error Handling
- **Challenge**: Graceful degradation when external services fail
- **Decision**: Implemented retry logic with exponential backoff and fallback options
- **Rationale**: Improves system reliability and user experience

## Performance Optimization

### LLM Response Time
- **Challenge**: Long wait times for complex screening tasks
- **Decision**: Implemented async processing with status updates
- **Rationale**: Better UX through progressive results and non-blocking operations

### Batch Processing
- **Challenge**: Efficiently processing large candidate pools
- **Decision**: Implemented batch processing with worker queues
- **Rationale**: Scalable approach for high-volume recruitment scenarios

## Future Improvements

1. **Vector Database Integration**: Add vector search for semantic candidate matching
2. **Multi-language Support**: Extend resume parsing to non-English resumes
3. **Advanced Analytics**: Dashboard for recruitment metrics and insights
4. **Interview Scheduling**: Automated coordination with calendar systems
5. **Bias Detection**: ML model to identify and mitigate unconscious bias in screening

## Lessons Learned

- **Start Simple**: Begin with core functionality before adding advanced features
- **Test Early**: Mock LLM responses enable rapid iteration without API costs
- **Document Everything**: Clear documentation reduces onboarding friction
- **Monitor Costs**: LLM API calls can become expensive; implement caching and monitoring
- **User Feedback**: Regular feedback from recruiters drives meaningful improvements
