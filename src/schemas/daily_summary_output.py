from pydantic import BaseModel, Field

# Define the structured schema for the system context
class SystemContext(BaseModel):
    daily_theme: str = Field(
        description="The overarching theme of strictly TODAY'S evaluation."
    )
    new_observations: list[str] = Field(
        description="New behaviors or bottlenecks noticed ONLY today. Do not include past issues."
    )
    persisting_patterns: list[str] = Field(
        description="Ongoing behaviors (e.g., nocturnal schedule). The Evaluator must not give advice on these unless they worsen."
    )
    resolved_issues: list[str] = Field(
        description="Past warnings that the user successfully handled today (e.g., fixed sleep schedule)."
    )
    assigned_tasks: list[str] = Field(
        description="Tasks assigned for tomorrow."
    )
    evaluator_goals: list[str] = Field(
        description="Clear, actionable goals for tomorrow's evaluation. Based on the 'new_observations'."
    )
    
# Main output model that nests the SystemContext
class DailySummaryOutput(BaseModel):
    morning_briefing: str = Field(
        description="The full Markdown text in Arabic formatted exactly as the Morning Briefing template."
    )
    system_context: SystemContext = Field(
        description="The structured system context for tomorrow's evaluator."
    )