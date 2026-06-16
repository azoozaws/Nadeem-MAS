from datetime import datetime

from src.agents.agent_state import AgentState
from src.models import gemini_3_5_flash_model, gemini_3_1_flash_model
from src.prompts.prompts import evaluater_prompt
from src.utils.get_yesterday_context import get_yesterday_context

from src.tools.notion_tools import(
    get_notion_monthly_goals,
    get_notion_weekly_objectives,
    get_tasks_by_date_range,
    search_notion_tasks,
    update_months_ids,
    update_month_sections_ids
)
from  src.tools.search_tavily import search_engine

async def evaluate_step(state:AgentState):
    tools = [get_notion_monthly_goals, get_notion_weekly_objectives, get_tasks_by_date_range, search_notion_tasks, update_months_ids, update_month_sections_ids, search_engine]

    primary_model_with_tools = gemini_3_5_flash_model.bind_tools(tools)
    fallback_model_with_tools = gemini_3_1_flash_model.bind_tools(tools)
    evaluater_model = primary_model_with_tools.with_fallbacks([fallback_model_with_tools])

    """
    - Current Date & Time: {current_date}
    - Explicit Mode (if any): {evaluation_mode} // Can be "Monthly", "Weekly", or "Auto-detect"
    - User Notes/Context (if any): {user_notes}
    """


    yesterday_context= await get_yesterday_context()

    if not yesterday_context:
        yesterday_context = " "

    chain = evaluater_prompt | evaluater_model

    
    response = await chain.ainvoke({"messages": state["messages"], "current_date": datetime.now().strftime("%Y-%m-%d"), "evaluation_mode": state.get("analysis_type", "Auto-detect"), "yesterday_context": yesterday_context, "user_notes": state.get("user_notes", " ")})
    return {"messages": [response]}