from pydantic import BaseModel, Field

class DailySummaryOutput(BaseModel):
    morning_briefing: str = Field(
        description="The full Markdown text in Arabic formatted exactly as the Morning Briefing template."
    )
    system_context: str = Field(
        description="A dense, highly technical summary of today's state, unresolved bottlenecks, and Evaluator's warnings. Written in English. This will be read by tomorrow's Evaluator."
    )