from typing import Annotated, Literal
from typing_extensions import TypedDict
import operator
from langchain_core.messages import BaseMessage
from src.schemas.daily_summary_output import DailySummaryOutput
class AgentState(TypedDict):
    # 1. سجل المحادثات (أساسي جداً لعمل LLMs المتعددة)
    messages: Annotated[list[BaseMessage], operator.add]
    
    # 2. نوع التحليل لمعرفة مسار العمل الحالي
    analysis_type: Literal["Monthly", "Weekly", "Auto-detect"]
    
    user_notes: str
    
    summarize: DailySummaryOutput
    
    # 3. معالجة الأخطاء
    error: str | None