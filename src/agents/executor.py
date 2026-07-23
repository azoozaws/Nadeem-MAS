from datetime import datetime

from langchain_core.messages import HumanMessage

from src.agents.agent_state import AgentState
from langchain_core.output_parsers import StrOutputParser
from src.models import gemini_3_6_flash_model, gemini_3_5_flash_model
from src.prompts.prompts import executor_prompt

from src.tools.notion_tools import(
    get_notion_monthly_goals,
    get_notion_weekly_objectives,
    get_tasks_by_date_range,
    search_notion_tasks,
    update_months_ids,
    update_month_sections_ids,
    create_one_notion_task,
    create_multiple_notion_tasks,
    delete_notion_task,
    update_notion_task,
)

from  src.tools.search_tavily import search_engine

async def execute_step(state:AgentState):

    tools = [get_notion_monthly_goals, get_notion_weekly_objectives, get_tasks_by_date_range, search_notion_tasks, update_months_ids, update_month_sections_ids, create_one_notion_task, create_multiple_notion_tasks, update_notion_task, delete_notion_task, search_engine]

    
    primary_model_with_tools = gemini_3_6_flash_model.bind_tools(tools)
    fallback_model_with_tools = gemini_3_5_flash_model.bind_tools(tools)
    executor_model = primary_model_with_tools.with_fallbacks([fallback_model_with_tools])

    """
    - Current Date & Time: {current_date}
    """
    chain = executor_prompt | executor_model

    response = await chain.ainvoke({"messages": state["messages"], "current_date": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), "user_notes": state.get("user_notes", " ")})
    return {"messages": [response]}