# Friction Log - AI Recruiter Copilot

> A log tracking development friction points, challenges encountered, and solutions implemented during the building of the AI Recruiter Copilot.

## 2024-01-15: Project Initialization

### Friction Point: Multi-LLM Orchestration Architecture
**Challenge**: Determining the optimal architecture for orchestrating multiple LLM providers (OpenAI, Anthropic) with different agents.

**Solution**: 
- Implemented LangGraph for workflow orchestration
- Created separate agent classes with abstracted LLM interfaces
- Used factory pattern for LLM provider selection based on task type

**Impact**: ⏱️ 4 hours

---

## 2024-01-16: Resume Parsing Integration

### Friction Point: Document Format Variability
**Challenge**: Resumes come in various formats (PDF, DOCX, plain text) with inconsistent structures.

**Solution**:
- Implemented multi-format parser using PyPDF2 and python-docx
- Created structured prompt templates for LLM-based information extraction
- Added fallback mechanisms for poorly formatted documents

**Impact**: ⏱️ 6 hours

---

## 2024-01-17: API Rate Limiting

### Friction Point: LLM API Rate Limits
**Challenge**: Hitting rate limits when processing multiple candidates simultaneously.

**Solution**:
- Implemented exponential backoff with tenacity library
- Added request queuing system with Redis
- Created cost-aware routing (use GPT-3.5 for simpler tasks, GPT-4 for complex analysis)

**Impact**: ⏱️ 3 hours

---

## 2024-01-18: Vector Database Performance

### Friction Point: Slow Similarity Search
**Challenge**: ChromaDB queries taking too long with large resume databases (>10k documents).

**Solution**:
- Switched to FAISS for production use cases
- Implemented hybrid search (keyword + semantic)
- Added caching layer for frequently accessed candidates

**Impact**: ⏱️ 5 hours

---

## 2024-01-19: Job Board API Integration

### Friction Point: Inconsistent API Schemas
**Challenge**: LinkedIn, Indeed, and GitHub APIs have completely different response formats.

**Solution**:
- Created adapter pattern for each job board
- Normalized data into common schema
- Built comprehensive error handling for API failures

**Impact**: ⏱️ 8 hours

---

## 2024-01-20: Agent State Management

### Friction Point: Complex Multi-Agent Workflows
**Challenge**: Managing state across sourcing → screening → engagement agent workflows.

**Solution**:
- Implemented state machines using LangGraph StateGraph
- Added persistent state storage in PostgreSQL
- Created rollback mechanisms for failed workflows

**Impact**: ⏱️ 7 hours

---

## 2024-01-21: Testing Multi-LLM Systems

### Friction Point: Non-Deterministic LLM Outputs
**Challenge**: Unit tests failing due to variable LLM responses.

**Solution**:
- Created mock LLM adapters for testing
- Implemented schema validation instead of exact matching
- Added integration tests with fixed seed values
- Used httpx for async testing

**Impact**: ⏱️ 4 hours

---

## 2024-01-22: Docker Orchestration

### Friction Point: Service Dependencies
**Challenge**: Ensuring PostgreSQL and Redis are ready before API starts.

**Solution**:
- Added healthcheck configurations to docker-compose
- Implemented wait-for-it script for service readiness
- Used depends_on with condition: service_healthy

**Impact**: ⏱️ 2 hours

---

## Key Learnings

1. **Multi-LLM Strategy**: Different models excel at different tasks. Use GPT-4 for complex reasoning, Claude for safety-critical decisions, GPT-3.5 for high-volume simple tasks.

2. **Error Handling**: LLM-based systems require extensive retry logic and graceful degradation.

3. **Cost Management**: Aggressive caching and intelligent model routing reduced API costs by 60%.

4. **Testing**: Mock extensively. Real LLM calls in CI/CD are expensive and slow.

5. **State Management**: Persistent state is crucial for long-running agent workflows.

---

## Total Development Time
⏱️ **39 hours** of friction-related work

## Next Steps
- [ ] Implement prompt versioning system
- [ ] Add observability with LangSmith
- [ ] Create fine-tuned models for specific recruiting tasks
- [ ] Build admin dashboard for monitoring agent performance
