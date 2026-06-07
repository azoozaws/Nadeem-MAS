from pydantic import BaseModel, model_validator
from typing import Optional, List, Any

class AgentTask(BaseModel):
    """
    A clean, token-efficient representation of a Notion Task for AI Agents.
    """
    id: str
    name: str
    icon: Optional[str] = None
    time_spent: Optional[int] = None
    status: Optional[str] = None
    categories: List[str] = []
    date: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def extract_notion_data(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "object" not in data:
            return data

        props = data.get("properties", {})

        # Extract Task Name
        name = ""
        if title_list := props.get("Name", {}).get("title", []):
            name = title_list[0].get("plain_text", "")

        # Extract Icon
        icon_val = None
        if icon_obj := data.get("icon"):
            icon_type = icon_obj.get("type")
            if icon_type == "custom_emoji":
                icon_val = icon_obj.get("custom_emoji", {}).get("url")
            elif icon_type == "emoji":
                icon_val = icon_obj.get("emoji")
            elif icon_type in ["file", "external"]:
                icon_val = icon_obj.get(icon_type, {}).get("url")

        # Extract Fields
        time_spent = props.get("Time", {}).get("number")
        
        status = None
        if status_obj := props.get("Status", {}).get("select"):
            status = status_obj.get("name")

        categories = []
        if type_list := props.get("Type", {}).get("multi_select", []):
            categories = [t.get("name") for t in type_list]

        date_val = None
        if date_obj := props.get("Date", {}).get("date"):
            date_val = date_obj.get("start")

        return {
            "id": data.get("id"),
            "name": name,
            "icon": icon_val,
            "time_spent": time_spent,
            "status": status,
            "categories": categories,
            "date": date_val
        }