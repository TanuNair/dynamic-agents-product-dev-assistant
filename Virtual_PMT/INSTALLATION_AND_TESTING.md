# Installation and Testing Guide

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running
- Llama3 model downloaded in Ollama

## Installation Steps

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /Users/tanunair/Documents/Virtual_PMT

# Install/upgrade the new checkpoint dependency
pip install langgraph-checkpoint-sqlite==2.0.6

# Or install all requirements (recommended)
pip install -r requirements.txt
```

### 2. Verify Ollama Setup

```bash
# Check if Ollama is running
ollama list

# Ensure llama3 model is available
# If not, download it:
ollama pull llama3

# Also ensure all-minilm for embeddings
ollama pull all-minilm
```

### 3. Verify Installation

```bash
# Test checkpoint import
python3 -c "from langgraph.checkpoint.sqlite import SqliteSaver; print('✅ SqliteSaver available')"

# Test other imports
python3 -c "from reportlab.lib.pagesizes import letter; print('✅ ReportLab available')"
```

## Testing the Workflow

### Test 1: Basic Plan Generation

1. **Start the app:**
   ```bash
   streamlit run src/main.py
   ```

2. **Generate a plan:**
   - Enter: "Build a fitness tracking app for runners"
   - Select Phase: "Research 🔍"
   - Click "🎯 Generate Plan"

3. **Expected behavior:**
   - Planner creates initial plan
   - Judge validates the plan
   - Enhancer applies improvements
   - Plan stops at checkpoint (before execution)
   - You see the approval interface

4. **Verify checkpoint:**
   ```bash
   # In another terminal
   ls -la checkpoints.db  # File should exist
   sqlite3 checkpoints.db "SELECT COUNT(*) FROM checkpoints;"  # Should show 1
   ```

### Test 2: Human Approval and Execution

1. **Review the plan** in the UI
2. **Click "✅ Approve & Execute"**
3. **Expected behavior:**
   - Graph resumes from checkpoint
   - Executor runs each task sequentially
   - Progress bar shows execution
   - Results displayed in tabs

4. **Verify execution:**
   - Check "🤖 Agent Outputs" tab
   - Verify all agents completed their tasks
   - Check "📊 Summary" tab for metrics

### Test 3: PDF Export

1. **After execution completes:**
   - Go to "📥 Export" tab
   - Click "📥 Download PDF Report"

2. **Expected behavior:**
   - PDF file generated successfully
   - Download button appears
   - File downloads to your system

3. **Verify PDF:**
   ```bash
   # Check if PDF was created
   ls -la product_report_*.pdf
   
   # Open the PDF to verify formatting
   open product_report_research.pdf  # macOS
   ```

### Test 4: Plan Modification

1. **Generate a new plan** (or start over)
2. **In the approval interface:**
   - Enter modification request: "Add a task for competitive analysis"
   - Click "🔧 Modify & Execute"

3. **Expected behavior:**
   - LLM processes modification request
   - Plan updated with new task
   - Execution proceeds with modified plan

### Test 5: Checkpoint Persistence

1. **Generate a plan** and wait at approval
2. **Stop the Streamlit app** (Ctrl+C)
3. **Restart the app:**
   ```bash
   streamlit run src/main.py
   ```

4. **Expected behavior:**
   - New session starts (new thread_id)
   - Previous checkpoint remains in database
   - Can generate new plan independently

5. **Verify checkpoint persistence:**
   ```bash
   sqlite3 checkpoints.db "SELECT thread_id, created_at FROM checkpoints ORDER BY created_at;"
   ```

## Common Issues and Solutions

### Issue 1: Import Error - SqliteSaver

**Error:**
```
ModuleNotFoundError: No module named 'langgraph.checkpoint.sqlite'
```

**Solution:**
```bash
pip install langgraph-checkpoint-sqlite==2.0.6
```

### Issue 2: Ollama Connection Error

**Error:**
```
Error: Could not connect to Ollama
```

**Solution:**
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
ollama list
```

### Issue 3: PDF Generation Error

**Error:**
```
Error saving report: ...
```

**Solution:**
```bash
# Reinstall reportlab
pip install --upgrade reportlab

# Check file permissions
ls -la .  # Ensure you can write to current directory
```

### Issue 4: Checkpoint Not Found

**Error:**
```
Checkpoint not found for thread_id
```

**Solution:**
- This is normal for new sessions
- Each session gets a new thread_id
- Previous checkpoints remain in database but aren't used
- Click "Generate Plan" to create new checkpoint

### Issue 5: Graph Already Compiled

**Error:**
```
Graph has already been compiled
```

**Solution:**
- Restart Streamlit app
- Graph is built once per session
- If you modify Graph.py, restart is required

## Performance Testing

### Test Execution Time

```bash
# Time a complete workflow
time streamlit run src/main.py
# Then manually execute workflow and note times
```

**Expected times:**
- Plan generation: 10-30 seconds
- Validation & enhancement: 5-15 seconds
- Execution (3-5 tasks): 30-90 seconds
- PDF generation: 1-3 seconds

### Test Checkpoint Size

```bash
# Check checkpoint database size
ls -lh checkpoints.db

# View checkpoint details
sqlite3 checkpoints.db "SELECT 
    thread_id, 
    LENGTH(checkpoint) as size_bytes,
    created_at 
FROM checkpoints 
ORDER BY created_at DESC 
LIMIT 5;"
```

## Debugging Tips

### Enable Debug Mode

In `src/main.py`, the debug expander shows:
- `plan_generated` status
- `execution_complete` status
- `human_approved` flag
- `approved_plan` length

### View Checkpoint Contents

```bash
# Connect to database
sqlite3 checkpoints.db

# List all checkpoints
.mode column
.headers on
SELECT thread_id, checkpoint_id, created_at FROM checkpoints;

# View specific checkpoint (replace with actual thread_id)
SELECT * FROM checkpoints WHERE thread_id = 'your-thread-id-here';
```

### Check Logs

```bash
# Streamlit logs show:
# - Node execution (Planner, Judge, Enhancer, Approval, Executor)
# - Checkpoint saves
# - State updates

# Watch for these messages:
# "APPROVAL CHECKPOINT: Plan ready for human review"
# "EXECUTOR: Step X/Y"
# "✅ Execution complete"
```

### Test Individual Components

```python
# Test formatter
python3 -c "
from src.formatter import AgentReport
report = AgentReport('test_report')
report.add_agent_output('test_agent', 'Test output')
print(report.save(to_pdf=True))
"

# Test graph building
python3 -c "
from src.Graph import build_graph
graph = build_graph()
print('Graph built successfully')
"

# Test checkpoint
python3 -c "
from langgraph.checkpoint.sqlite import SqliteSaver
saver = SqliteSaver.from_conn_string('test.db')
print('Checkpoint saver created')
"
```

## Success Criteria

✅ **Installation successful if:**
- All dependencies install without errors
- Ollama is running with llama3 model
- SqliteSaver imports successfully
- Streamlit app starts without errors

✅ **Workflow successful if:**
- Plan generation stops at checkpoint
- Approval interface displays correctly
- Execution resumes after approval
- Results display in all tabs
- PDF downloads successfully

✅ **Checkpoint system working if:**
- `checkpoints.db` file is created
- Database contains checkpoint records
- Thread ID is consistent during session
- State persists across invoke calls

## Next Steps

After successful testing:

1. **Customize for your use case:**
   - Modify agent prompts in `src/executor.py`
   - Add new phases in `src/config.py`
   - Integrate additional tools

2. **Production deployment:**
   - Consider PostgreSQL for multi-user
   - Add authentication
   - Implement checkpoint cleanup
   - Add monitoring and logging

3. **Extend functionality:**
   - Add more agent types
   - Integrate external APIs
   - Implement agent collaboration
   - Add error recovery

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review `CHECKPOINT_IMPLEMENTATION.md` for technical details
3. Verify all prerequisites are met
4. Check Ollama and Python versions
5. Review Streamlit logs for errors

## Cleanup

To reset everything:

```bash
# Remove checkpoint database
rm checkpoints.db

# Remove generated reports
rm product_report_*.pdf

# Clear memory database
rm -rf memory_db/

# Restart with fresh state
streamlit run src/main.py