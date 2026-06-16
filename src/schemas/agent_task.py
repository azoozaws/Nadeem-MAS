from pydantic import BaseModel, model_validator
from typing import Optional, List, Any

class AgentTask(BaseModel):
    """
    A clean, token-efficient representation of a Notion Task for AI Agents.
    """
    id: str
    name: str
    icon: Optional[dict] = None
    estimated_time_spent: Optional[int] = None
    real_time_spent: Optional[int] = None
    status: Optional[str] = None
    categories: List[str] = []
    date: Optional[str] = None
    created_by: Optional[dict] = None
    last_edited_by: Optional[dict] = None

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
        icon_val = data.get("icon", {})

        # Extract Fields
        estimated_time_spent = props.get("Time", {}).get("number")
        real_time_spent = props.get("Time", {}).get("number")
        
        status = None
        if status_obj := props.get("Status", {}).get("select"):
            status = status_obj.get("name")

        categories = []
        if type_list := props.get("Type", {}).get("multi_select", []):
            categories = [t.get("name") for t in type_list]

        date_val = None
        if date_obj := props.get("Date", {}).get("date"):
            date_val = date_obj.get("start")

        created_by = None
        if created_by_obj := props.get("Created by", {}).get("created_by", {}):
            created_by = {"name": created_by_obj.get("name", None), "type": created_by_obj.get("type", None)}

        last_edited_by = None
        if last_edited_by_obj := props.get("Last edited by", {}).get("last_edited_by", {}):
            last_edited_by = {"name": last_edited_by_obj.get("name", None), "type": last_edited_by_obj.get("type", None)}
        
        return {
            "id": data.get("id"),
            "name": name,
            "icon": icon_val,
            "estimated_time_spent": estimated_time_spent,
            "real_time_spent": real_time_spent,
            "status": status,
            "categories": categories,
            "date": date_val,
            "created_by": created_by,
            "last_edited_by": last_edited_by
        }