from pydantic import BaseModel, Field
from typing import Literal, Optional

class TaskItem(BaseModel):
    # نستخدم اسم مفرد للكلاس لأنه يمثل مهمة واحدة داخل القائمة
    name: str = Field(
        description="The clear, actionable title of the task."
    )
    
    status: Literal["Not started", "In progress", "Completed"] = Field(
        default="Not started",
        description="The current operational status of the task in Notion."
    )
    
    duration_minutes: int = Field(
        description="Estimated time to complete the task in minutes."
    )
    
    task_type: Literal["Habits", "Study", "Work", "Entertainment"] = Field(
        description="The specific category this task falls under."
    )
    
    # حقل أساسي للتعديل (Update)؛ يكون None عند إنشاء مهمة جديدة تماماً
    notion_page_id: Optional[str] = Field(
        default=None,
        description="The unique Notion page ID, required if updating an existing task."
    )

class TaskList(BaseModel):
    """Container schema to allow the LLM to return a list of multiple tasks at once."""
    tasks: list[TaskItem] = Field(description="A list of generated or optimized tasks.")