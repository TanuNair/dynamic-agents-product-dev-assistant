# LangGraph Checkpoint Implementation Guide

## Overview

This document describes the implementation of LangGraph's checkpoint system with SqliteSaver for proper human-in-the-loop approval workflow.

## What Changed

### 1. **Fixed PDF Export** (`src/formatter.py`)
- **Problem**: HTML parsing from markdown caused ReportLab errors
- **Solution**: Direct text formatting with proper ReportLab Paragraph handling
- **Features**:
  - Proper markdown header conversion (H1, H2, H3)
  - Bullet point and numbered list support
  - Bold/italic markdown support
  - Special character escaping
  - Custom styling with colors and spacing

### 2. **Implemented SqliteSaver Checkpoints** (`src/Graph.py`)
- **Problem**: Workflow couldn't properly pause for human approval
- **Solution**: Added SqliteSaver with `interrupt_before=["executor"]`
- **Changes**:
  ```python
  from langgraph.checkpoint.sqlite import SqliteSaver
  
  def build_graph(checkpoint_db_path="checkpoints.db"):
      checkpointer = SqliteSaver.from_conn_string(checkpoint_db_path)
      graph = StateGraph(AppState)
      # ... add nodes ...
      return graph.compile(
          checkpointer=checkpointer,
          interrupt_before=["executor"]
      )
  ```

### 3. **Updated Workflow** (`src/main.py`)
- **Problem**: Manual executor loop bypassed LangGraph's natural flow
- **Solution**: Proper checkpoint-based pause/resume
- **Key Changes**:
  - Added `thread_id` to session state for checkpoint persistence
  - Build graph once per session
  - Use `config = {"configurable": {"thread_id": thread_id}}` for all invocations
  - First invoke stops at executor (checkpoint)
  - After approval, invoke with `None` to resume from checkpoint

### 4. **Added Dependency** (`requirements.txt`)
- Added `langgraph-checkpoint-sqlite==2.0.6`

## How It Works

### Phase 1: Plan Generation (Stops at Checkpoint)
```python
# User clicks "Generate Plan"
graph = st.session_state.graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}
initial_state = AppState(input=user_input, phase=selected_phase, ...)

# Invoke - stops before executor due to interrupt_before
result = graph.invoke(initial_state, config)
# State saved to checkpoints.db
```

### Phase 2: Human Review
- User reviews the enhanced plan
- Can approve as-is, request modifications, or reject
- State remains in checkpoint, waiting

### Phase 3: Resume Execution
```python
# User clicks "Approve & Execute"
graph = st.session_state.graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Resume from checkpoint by passing None
result = graph.invoke(None, config)
# Continues from executor node automatically
```

## Benefits

1. **Proper Pause/Resume**: True checkpoint-based workflow, not a workaround
2. **State Persistence**: Survives app restarts (checkpoints.db file)
3. **Cleaner Code**: Removed manual executor loop and state copying
4. **Better Error Handling**: LangGraph manages state transitions
5. **Thread Isolation**: Each user session has unique thread_id
6. **Queryable History**: Can inspect checkpoints.db with SQLite tools

## File Structure

```
Virtual_PMT/
├── checkpoints.db          # SQLite database (auto-created)
├── requirements.txt        # Updated with checkpoint dependency
├── src/
│   ├── Graph.py           # Updated with SqliteSaver
│   ├── main.py            # Updated with checkpoint workflow
│   ├── formatter.py       # Fixed PDF generation
│   └── ...
└── CHECKPOINT_IMPLEMENTATION.md  # This file
```

## Installation

```bash
# Install new dependency
pip install langgraph-checkpoint-sqlite==2.0.6

# Or install all requirements
pip install -r requirements.txt
```

## Usage

### Running the App
```bash
streamlit run src/main.py
```

### Workflow
1. Enter product description and select phase
2. Click "Generate Plan" → stops at checkpoint
3. Review enhanced plan
4. Click "Approve & Execute" → resumes from checkpoint
5. View results and download PDF report

### Inspecting Checkpoints
```bash
# View checkpoint database
sqlite3 checkpoints.db

# List all checkpoints
SELECT thread_id, checkpoint_id, created_at FROM checkpoints;

# View specific thread
SELECT * FROM checkpoints WHERE thread_id = 'your-thread-id';
```

## Technical Details

### Thread ID Management
- Generated once per session: `str(uuid.uuid4())`
- Stored in `st.session_state.thread_id`
- Reset on "Start New Project"
- Visible in sidebar debug info

### Checkpoint Storage
- Location: `checkpoints.db` (SQLite file)
- Contains: Complete AppState at interrupt point
- Includes: plan, enhanced_plan, validation_errors, etc.
- Persists: Across app restarts

### State Flow
```
User Input → Planner → Judge → Enhancer → Approval
                                              ↓
                                         [CHECKPOINT]
                                              ↓
                                    Human Approval UI
                                              ↓
                                         [RESUME]
                                              ↓
                                          Executor → Results
```

## Troubleshooting

### Import Error: SqliteSaver
```bash
pip install langgraph-checkpoint-sqlite==2.0.6
```

### Checkpoint Not Persisting
- Check if `checkpoints.db` file is created
- Verify thread_id is consistent between invocations
- Ensure config dict is passed to both invoke calls

### PDF Generation Error
- Verify reportlab is installed: `pip install reportlab`
- Check file permissions in working directory
- Review error message for specific character issues

## Migration Notes

### From Old Implementation
The old implementation used:
- Manual executor loop in main.py
- Session state for approval flags
- No persistent checkpoints

The new implementation uses:
- LangGraph's native checkpoint system
- SqliteSaver for persistence
- Proper interrupt_before mechanism

### Breaking Changes
- Graph building now requires checkpoint_db_path parameter
- Invoke calls require config with thread_id
- Resume uses `invoke(None, config)` instead of manual loop

## Future Enhancements

1. **PostgreSQL Backend**: For multi-server deployments
2. **Checkpoint Cleanup**: Periodic cleanup of old checkpoints
3. **Checkpoint Viewer**: UI to browse checkpoint history
4. **Rollback**: Ability to rollback to previous checkpoints
5. **Branching**: Support multiple approval paths

## References

- [LangGraph Checkpoints Documentation](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [SqliteSaver API](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver)
- [Human-in-the-Loop Guide](https://langchain-ai.github.io/langgraph/how-tos/human-in-the-loop/)