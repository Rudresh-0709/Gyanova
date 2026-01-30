# Gyanova
Gyanova is an intelligent, personalized AI tutor app designed to make learning more accessible, engaging, and intuitive. Whether you're a student, self-learner, or curious mind, Gyanova adapts to your pace, style, and goals — delivering knowledge with clarity and depth.

## LangSmith Integration

LangSmith provides tracing, monitoring, and evaluation for the AI teaching workflow. All LangGraph executions are automatically traced.

### Setup

1. **Install Dependencies** (already done):
   ```bash
   pip install langsmith
   ```

2. **Configure Environment Variables** in `.env`:
   ```bash
   LANGCHAIN_TRACING_V2="true"
   LANGCHAIN_API_KEY="your-api-key"
   LANGCHAIN_PROJECT="AI-Teacher-App"
   ```

3. **Verify Configuration**:
   ```bash
   cd apps/api-server
   python app/test_langsmith_integration.py
   ```

### Viewing Traces

1. Sign in to [LangSmith Dashboard](https://smith.langchain.com)
2. Navigate to "AI-Teacher-App" project
3. View traces for each workflow execution with:
   - Input/output for each node
   - Token usage and costs
   - Execution time per node
   - LLM call details

### Automatic Tracing

All workflows are automatically traced when running:
- `test_workflow.py` - Full workflow test
- `test_narration_batch.py` - Narration batch testing
- `test_optimized_batch.py` - Optimized batch testing

No code changes needed - tracing is automatic once environment variables are set!

### Evaluation (Coming Soon)

See `services/langsmith_evaluator.py` for:
- Creating evaluation datasets
- Running quality assessments
- Comparing different approaches

