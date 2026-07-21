from datetime import datetime
import os
import asyncio
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage

from src.utils.logger import setup_custom_logger
logger = setup_custom_logger(__name__)


from src.agents.agent_state import AgentState
from src.agents.evaluator import evaluate_step
from src.agents.executor import execute_step
from src.agents.summarizer import summarize_step

from src.tools.notion_tools import (
    get_notion_monthly_goals,
    get_notion_weekly_objectives,
    get_tasks_by_date_range,
    search_notion_tasks,
    update_months_ids,
    update_month_sections_ids,
    create_one_notion_task,
    create_multiple_notion_tasks,
    update_notion_task,
    delete_notion_task
)
from src.tools.search_tavily import search_engine

# Diagram of the Graph
"""
                     ┌───────────────┐
                     │   __start__   │
                     └───────┬───────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │   Strategic Evaluator   │◄────────────────────┐
                │       (Read-only)       │                     │
                └────────────┬────────────┘                     │
                             │                                  │
                      tools_condition                           │
                        ╱         ╲                             │
                       ╱           ╲                            │
               "tools"              END                         │
                  │                  │                          │
                  ▼                  │                          │
       ┌─────────────────────┐       │            ┌─────────────┘
       │   Evaluator Tools   │───────┘            │ (ReAct Loop)
       │ (ToolNode: 7 Tools) │────────────────────┘
       └─────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Operational Executor   │◄────────────────────┐
                │      (Read / Write)     │                     │
                └────────────┬────────────┘                     │
                             │                                  │
                      tools_condition                           │
                        ╱         ╲                             │
                       ╱           ╲                            │
               "tools"              END                         │
                  │                  │                          │
                  ▼                  │                          │
       ┌─────────────────────┐       │            ┌─────────────┘
       │   Executor Tools    │───────┘            │ (ReAct Loop)
       │ (ToolNode: 11 Tools)│────────────────────┘
       └─────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Executive Summarizer   │
                │   (Structured Output)   │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │    save_result (I/O)    │
                │ (Morning Brief/Context) │
                └────────────┬────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │    __end__    │
                     └───────────────┘
"""


class AssistantAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        
        evaluator_tools = [
            get_notion_monthly_goals, 
            get_notion_weekly_objectives, 
            get_tasks_by_date_range, 
            search_notion_tasks, 
            update_months_ids, 
            update_month_sections_ids, 
            search_engine
        ]
        evaluator_tools_node = ToolNode(evaluator_tools)
        

        executor_tools = [get_notion_monthly_goals, get_notion_weekly_objectives, get_tasks_by_date_range, search_notion_tasks, update_months_ids, update_month_sections_ids, create_one_notion_task, create_multiple_notion_tasks, update_notion_task, delete_notion_task, search_engine]
        executor_tools_node = ToolNode(executor_tools)
        
        # -- Nodes --
        # graph.add_node("greet_user", self._greet_user)
        graph.add_node("evaluator", self._evaluator)
        graph.add_node("evaluator_tools", evaluator_tools_node)
        graph.add_node("executor", self._executor)
        graph.add_node("executor_tools", executor_tools_node)
        graph.add_node("summarizer", self._summarizer)
        graph.add_node("save_result", self._save_result)

        # -- Edges --
        graph.add_edge(START, "evaluator")

        
        graph.add_conditional_edges(
            "evaluator", tools_condition, 
            {"tools": "evaluator_tools", END: "executor"}
        )
        graph.add_edge("evaluator_tools", "evaluator")

        graph.add_conditional_edges(
            "executor", tools_condition, 
            {"tools": "executor_tools", END: "summarizer"}
        )
        graph.add_edge("executor_tools", "executor")
        
        graph.add_edge("summarizer", "save_result")
        graph.add_edge("save_result", END)

        return graph.compile()
    
    # -- Nodes --
    
    async def _evaluator(self, state: AgentState):
        
        result = await evaluate_step(state)
        return result

    async def _executor(self, state: AgentState):
        result = await execute_step(state)
        return result
    
    async def _summarizer(self, state: AgentState):
        result = await summarize_step(state)

        return result

    def _save_result(self, state: dict) -> dict:
        """
        Saves the dual outputs of the Executive Summarizer:
        1. Morning Briefing (Markdown) for the user.
        2. System Context (Markdown/Text) for tomorrow's Evaluator agent.
        """
        try:
            # 1. Safe Extraction of Structured Output
            summary_data = state.get("summarize")
            
            if not summary_data:
                logger.warning("⚠️ Warning: 'summarize' key not found in state!")
                return {}

            # Handle both Pydantic model and Dictionary formats safely
            # LangGraph sometimes serializes Pydantic models to dicts during state transitions
            if isinstance(summary_data, dict):
                morning_briefing = summary_data.get("morning_briefing", "")
                system_context = summary_data.get("system_context", "")
            else:
                morning_briefing = getattr(summary_data, "morning_briefing", "")
                system_context = getattr(summary_data, "system_context", "")

            if not morning_briefing and not system_context:
                logger.warning("⚠️ Warning: Both briefing and context are empty!")
                return {}

            # 2. Build Robust Absolute Paths
            current_file_path = Path(__file__).resolve()
            # Adjust the number of parents based on your project structure (e.g., src/agents/nodes/)
            project_root = current_file_path.parent.parent.parent 
            
            now = datetime.now()
            year_str = now.strftime("%Y")
            month_str = now.strftime("%B")
            date_prefix = now.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Define directories
            feedback_dir = project_root / "data" / "feedback" / year_str / month_str
            context_dir = project_root / "data" / "guidelines" / year_str / month_str
            
            # Create directories pythonically (exist_ok prevents errors if they exist)
            feedback_dir.mkdir(parents=True, exist_ok=True)
            context_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Save the Outputs

            # A) Save Morning Briefing (User Facing)
            if morning_briefing:
                briefing_file = feedback_dir / f"briefing_{date_prefix}.md"
                with open(briefing_file, 'w', encoding='utf-8') as f:
                    f.write('<!-- موجز الصباح -->\n<div dir="rtl">\n\n')
                    f.write(morning_briefing)
                    f.write('\n\n</div>')
                print(f"✅ Morning briefing saved at: {briefing_file}")

            # B) Save System Context (Agent Facing)
            if system_context:
                context_file = context_dir / f"context_{date_prefix}.md"
                with open(context_file, 'w', encoding='utf-8') as f:
                    f.write("# 🤖 System Context for Tomorrow's Evaluator\n")
                    f.write(f"**Generated At:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## 🔄 Core State:\n\n")
                    
                    # Convert the Pydantic model to a dictionary
                    if hasattr(system_context, 'model_dump'):
                        context_dict = system_context.model_dump()
                    else:
                        context_dict = system_context
                    
                    # Iterate through the keys and values to format them cleanly
                    for key, value in context_dict.items():
                        # Format the key for better readability (e.g., 'daily_theme' -> 'Daily Theme')
                        formatted_key = key.replace('_', ' ').title()
                        f.write(f"### {formatted_key}:\n")
                        
                        # Handle lists vs strings
                        if isinstance(value, list):
                            if not value:  # Handle empty lists
                                f.write("- None\n")
                            else:
                                for item in value:
                                    f.write(f"- {item}\n")
                        else:
                            f.write(f"{value}\n")
                        
                        f.write("\n")  # Add space between sections

                    f.write("---\n## 📝 User Notes / ملاحظات المستخدم:\n")
                    f.write("> [اكتب ملاحظاتك، أعذارك، أو تغييراتك الطارئة هنا ليقرأها المقيّم غداً]\n")
                
                print(f"✅ System context saved at: {context_file}")

        except Exception as e:
            # Using print here as fallback, but logger.error(e) is preferred in production
            print(f"❌ Error while attempting to save the files: {e}")

        # In LangGraph, nodes performing Side Effects (like I/O operations)
        # should return an empty dict to avoid unintended state overrides
        return {}

    # -- Execution --
    async def run(self, initial_values: dict):
        
        result = await self.graph.ainvoke(initial_values)
        return result

agent = AssistantAgent()
compiled_graph = agent.graph