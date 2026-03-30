# Multi-Agent Workflow with Tool Integration

## Complete System Flowchart

```mermaid
flowchart TD
    Start([User Input + Phase Selection]) --> Planner[Planner Node]
    
    Planner --> |Creates Initial Plan| Judge[Judge Node]
    
    Judge --> |Validates Plan| Enhancer[Enhancer Node]
    
    Enhancer --> |Improves Plan| Approval[Approval Checkpoint]
    
    Approval --> |Saves to Checkpoint DB| Interrupt{Human Review}
    
    Interrupt --> |Reject| Start
    Interrupt --> |Modify| ModifyPlan[Apply Modifications]
    ModifyPlan --> Approval
    Interrupt --> |Approve| Executor[Executor Node]
    
    Executor --> CheckAgent{Which Agent Type?}
    
    CheckAgent --> |research_agent| FetchBoth[Fetch Google Trends + Web Search]
    CheckAgent --> |data_analyst| FetchWeb1[Fetch Web Search]
    CheckAgent --> |marketing_agent| FetchWeb2[Fetch Web Search]
    CheckAgent --> |other agents| NoTools[No Tool Data]
    
    FetchBoth --> GoogleTrends[Google Trends API]
    FetchBoth --> WebSearch1[Web Search API]
    FetchWeb1 --> WebSearch2[Web Search API]
    FetchWeb2 --> WebSearch3[Web Search API]
    
    GoogleTrends --> InjectData[Inject Tool Data into Prompt]
    WebSearch1 --> InjectData
    WebSearch2 --> InjectData
    WebSearch3 --> InjectData
    NoTools --> BuildPrompt[Build Agent Prompt]
    
    InjectData --> BuildPrompt
    
    BuildPrompt --> LLM[Execute with LLM]
    
    LLM --> SaveResult[Save Result to State]
    
    SaveResult --> MoreTasks{More Tasks?}
    
    MoreTasks --> |Yes| Executor
    MoreTasks --> |No| Complete[Execution Complete]
    
    Complete --> Report[Generate PDF Report]
    Report --> End([End])
    
    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style Interrupt fill:#fff4e1
    style GoogleTrends fill:#e1f0ff
    style WebSearch1 fill:#e1f0ff
    style WebSearch2 fill:#e1f0ff
    style WebSearch3 fill:#e1f0ff
    style LLM fill:#f0e1ff
```

## Tool Integration Detail

```mermaid
flowchart LR
    subgraph "Tool Fetching Logic"
        Agent[Agent Type] --> Check{Check Agent}
        Check --> |research_agent| Both[Fetch Both Tools]
        Check --> |data_analyst<br/>marketing_agent| Web[Fetch Web Search Only]
        Check --> |other agents| None[No Tools]
        
        Both --> GT[Google Trends Data]
        Both --> WS1[Web Search Data]
        Web --> WS2[Web Search Data]
        
        GT --> Format[Format as Markdown]
        WS1 --> Format
        WS2 --> Format
        None --> Skip[Skip Tool Section]
        
        Format --> Inject[Inject into Prompt]
        Skip --> Inject
    end
    
    style GT fill:#e1f0ff
    style WS1 fill:#e1f0ff
    style WS2 fill:#e1f0ff
```

## Executor Node Flow with Tools

```mermaid
sequenceDiagram
    participant State
    participant Executor
    participant ToolFetcher
    participant GoogleTrends
    participant WebSearch
    participant LLM
    participant Memory
    
    State->>Executor: Current Task + Agent Type
    
    Executor->>ToolFetcher: Check if tools needed
    
    alt research_agent
        ToolFetcher->>GoogleTrends: Fetch trends data
        GoogleTrends-->>ToolFetcher: Trends JSON
        ToolFetcher->>WebSearch: Fetch web results
        WebSearch-->>ToolFetcher: Search results
    else data_analyst or marketing_agent
        ToolFetcher->>WebSearch: Fetch web results
        WebSearch-->>ToolFetcher: Search results
    else other agents
        ToolFetcher-->>Executor: No tool data
    end
    
    ToolFetcher-->>Executor: Formatted tool data
    
    Executor->>Executor: Build prompt with tool data
    Executor->>LLM: Execute prompt
    LLM-->>Executor: Agent output
    
    Executor->>Memory: Save to conversation memory
    Executor->>Memory: Save to semantic memory
    
    Executor->>State: Update results + increment step
```

## Phase-Based Agent and Tool Availability

```mermaid
graph TB
    subgraph "Ideation Phase"
        I1[product_manager]
        I2[research_agent]
        I3[brainstorm_agent]
        I2 -.->|uses| IT1[Google Trends]
        I2 -.->|uses| IT2[Web Search]
    end
    
    subgraph "Research Phase"
        R1[product_manager]
        R2[research_agent]
        R3[data_analyst]
        R4[user_researcher]
        R2 -.->|uses| RT1[Google Trends]
        R2 -.->|uses| RT2[Web Search]
        R3 -.->|uses| RT3[Web Search]
    end
    
    subgraph "Design Phase"
        D1[product_manager]
        D2[ux_designer]
        D3[ui_designer]
        D4[design_agent]
    end
    
    subgraph "Development Phase"
        DV1[product_manager]
        DV2[technical_architect]
        DV3[developer_agent]
        DV4[qa_engineer]
    end
    
    subgraph "Testing Phase"
        T1[product_manager]
        T2[qa_engineer]
        T3[user_researcher]
        T4[data_analyst]
        T4 -.->|uses| TT1[Web Search]
    end
    
    subgraph "Launch Phase"
        L1[product_manager]
        L2[marketing_agent]
        L3[data_analyst]
        L4[launch_coordinator]
        L2 -.->|uses| LT1[Web Search]
        L3 -.->|uses| LT2[Web Search]
    end
    
    style IT1 fill:#e1f0ff
    style IT2 fill:#e1f0ff
    style RT1 fill:#e1f0ff
    style RT2 fill:#e1f0ff
    style RT3 fill:#e1f0ff
    style TT1 fill:#e1f0ff
    style LT1 fill:#e1f0ff
    style LT2 fill:#e1f0ff
```

## Data Flow: User Input → Final Report

```mermaid
flowchart TD
    Input[User Input:<br/>'Build fitness app'] --> Extract[Extract Keywords]
    
    Extract --> |'fitness app'| Tools{Fetch Tool Data}
    
    Tools --> GT[Google Trends API]
    Tools --> WS[Web Search API]
    
    GT --> |Interest: 75/100<br/>Trend: Rising<br/>Related: 'workout tracker'| Data[Tool Data]
    WS --> |Latest articles<br/>Competitor info<br/>Market size| Data
    
    Data --> Prompt[Build Agent Prompt]
    
    Prompt --> |Prompt with real data| LLM[LLM Execution]
    
    LLM --> Output[Agent Output:<br/>Market Analysis]
    
    Output --> Memory1[Conversation Memory]
    Output --> Memory2[Semantic Memory]
    
    Memory1 --> NextAgent[Next Agent]
    Memory2 --> NextAgent
    
    NextAgent --> |Repeat for each task| AllResults[All Agent Results]
    
    AllResults --> Format[Format as PDF]
    
    Format --> Report[Final Report]
    
    style GT fill:#e1f0ff
    style WS fill:#e1f0ff
    style LLM fill:#f0e1ff
    style Report fill:#e1ffe1
```

## Key Points

### Tool Integration Strategy
1. **Automatic Fetching**: Tools are called automatically based on agent type
2. **Data Injection**: Tool data is injected into agent prompts
3. **No Function Calling**: Agents don't "call" tools - they receive pre-fetched data
4. **Phase-Aware**: Tool availability can be restricted by development phase

### Agent-Tool Mapping
- **research_agent**: Google Trends + Web Search
- **data_analyst**: Web Search
- **marketing_agent**: Web Search
- **Other agents**: No tools (yet)

### Workflow Checkpoints
1. **After Enhancer**: State saved to SQLite
2. **Before Executor**: Human approval required
3. **After Each Task**: Results saved to memory
4. **After All Tasks**: Final report generated
