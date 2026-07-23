from datetime import datetime
import os
from src.agents.agent_state import AgentState
from langchain_core.output_parsers import PydanticOutputParser
from src.models import gemini_3_6_flash_model, gemini_3_5_flash_model
from src.prompts.prompts import summarizer_prompt
from src.schemas.daily_summary_output import DailySummaryOutput

async def summarize_step(state:AgentState):

    primary_model_with_tools = gemini_3_5_flash_model.with_structured_output(DailySummaryOutput)
    fallback_model_with_tools = gemini_3_6_flash_model.with_structured_output(DailySummaryOutput)

    summarizer_model = primary_model_with_tools.with_fallbacks([fallback_model_with_tools])


    chain = summarizer_prompt | summarizer_model

    response = await chain.ainvoke({"messages": state["messages"]})

    return {"summarize": response}