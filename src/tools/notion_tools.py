import json
import os
from pprint import pprint
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool


from src.utils.logger import setup_custom_logger
from src.schemas.agent_task import AgentTask
logger = setup_custom_logger("NotionTools")



# ==========================================
# 1. HELPER UTILITIES
# ==========================================
def get_project_root() -> Path:
    """
    Dynamically finds the project root directory, 
    supporting both standard script execution and Jupyter Notebooks.
    """
    try:
        # Works perfectly in standard .py scripts inside src/tools/
        # __file__ is: project_root/src/tools/notion_tools.py
        # .parent.parent.parent goes up 3 levels to project_root/
        return Path(__file__).resolve().parent.parent.parent
    except NameError:
        # Fallback for Jupyter Notebooks if __file__ is undefined
        # Assumes notebook is running in project_root/tests/ or project_root/notebooks/
        return Path.cwd().parent

# 1. Get the absolute path to the project root
PROJECT_ROOT = get_project_root()

# 2. Construct the bulletproof absolute path to your JSON file
JSON_PATH = PROJECT_ROOT / "data" / "memory" / "Monthly-planner-2026" / "master.json"


def get_db_id_with_tokens_with_headers(get_file_path: bool = False):
    """
    Utility function to load environment tokens and configurations safely.
    """
    
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            important_info = json.load(file)
    except FileNotFoundError:
        logger.error(f"The file {JSON_PATH} was not found.")
        return None
    except json.JSONDecodeError:
        logger.error("The JSON file is corrupted or improperly formatted.")
        return None

    if not (database_id := important_info.get("metadata", {}).get("master_tasks_db_id")):
        logger.error("'master_tasks_db_id' is missing from the JSON metadata.")
        return None
    
    if not (NOTION_ACCESS_TOKEN := os.getenv("NOTION_ACCESS_TOKEN")):
        logger.error("NOTION_ACCESS_TOKEN is not set in the environment variables.")
        return None
    
    NOTION_HEADERS = {
        "Authorization": f"Bearer {NOTION_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    if get_file_path:
        return database_id, NOTION_ACCESS_TOKEN, NOTION_HEADERS, JSON_PATH
    return database_id, NOTION_ACCESS_TOKEN, NOTION_HEADERS


# ==========================================
# 2. AGENT TOOLS (METADATA & STRUCTURING)
# ==========================================
@tool
def update_months_ids(target_months: List[str]) -> None:
    """
    Synchronizes the local JSON mapping file with the latest Notion month page IDs.
    
    This tool should be used when the agent needs to ensure the local 'master.json' file 
    is up-to-date with current month-specific page IDs from the Notion database.
    It preserves existing section IDs and only updates or initializes the month page references.

    Args:
        target_months (List[str]): A list of month names (e.g., ['June', 'July']) to synchronize.
    """
    # CRITICAL FIX: Unpacking 4 values correctly using a placeholder for the raw token (_)
    config = get_db_id_with_tokens_with_headers(get_file_path=True)
    if not config:
        return
    database_id, _, headers, file_path = config

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            important_info = json.load(file)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return
    
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Network or API Error: {e}")
        return

    months_id_map = {
        month_name: block["id"]
        for block in json_response.get("results", [])
        if (title_list := block.get("properties", {}).get("Name", {}).get("title", []))
        and (month_name := title_list[0].get("plain_text", "")) in target_months
    }

    for month, month_id in months_id_map.items():
        if "months" not in important_info:
            important_info["months"] = {}
            
        if month in important_info["months"]:
            important_info["months"][month]["page_id"] = month_id
        else:
            important_info["months"][month] = {
                "page_id": month_id,
                "sections": {}
            }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(important_info, file, ensure_ascii=False, indent=4)
        
    logger.info("Successfully updated the month IDs in the JSON map!")


@tool
def update_month_sections_ids(month_name: str, target_sections: List[str]) -> None:
    """
    Synchronizes local JSON section IDs for a specific month with Notion.
    
    Use this tool when the agent needs to identify block IDs (like weekly toggles) 
    within a specific month's page in Notion. It scans the page children to map 
    the section names to their respective Notion block IDs.

    Args:
        month_name (str): The name of the month (e.g., 'June').
        target_sections (List[str]): A list of section names to locate (e.g., ['First Week', 'Second Week']).
    """
    # CRITICAL FIX: Correctly unpacking 4 values from helper function
    config = get_db_id_with_tokens_with_headers(get_file_path=True)
    if not config:
        return
    _, _, headers, file_path = config

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            important_info = json.load(file)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return

    if "months" not in important_info or month_name not in important_info["months"]:
        logger.error(f"The month '{month_name}' is not initialized in the JSON map.")
        return

    month_page_id = important_info["months"][month_name]["page_id"]
    url = f"https://api.notion.com/v1/blocks/{month_page_id}/children"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Network or API Error while fetching sections for {month_name}: {e}")
        return

    sections_id_map: Dict[str, str] = {}
    for block in json_response.get("results", []):
        block_type = block.get("type", "")
        type_object = block.get(block_type, {})
        
        if rich_text_list := type_object.get("rich_text", []):
            if (section_name := rich_text_list[0].get("plain_text", "")) in target_sections:
                sections_id_map[section_name] = block["id"]

    if not sections_id_map:
        logger.warning(f"No matching sections found in Notion for '{month_name}'.")
        return

    if "sections" not in important_info["months"][month_name]:
        important_info["months"][month_name]["sections"] = {}
        
    important_info["months"][month_name]["sections"].update(sections_id_map)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(important_info, file, ensure_ascii=False, indent=4)
        
    logger.info(f"Successfully updated {len(sections_id_map)} sections for '{month_name}'!")


# ==========================================
# 3. AGENT TOOLS (CRUD & DATA FETCHING)
# ==========================================
@tool
def get_tasks_by_date_range(
    start_date: str,
    end_date: str,
) -> Optional[List[AgentTask]]:
    """
    Retrieves all tasks from the Master Database that fall within a given date range.
    
    Use this tool to fetch tasks for weekly or monthly reports, or when the agent needs 
    to analyze workload for a specific period. Returns a list of clean AgentTask objects.

    Args:
        start_date (str): ISO 8601 start date (YYYY-MM-DD).
        end_date (str): ISO 8601 end date (YYYY-MM-DD).

    Returns:
        List[AgentTask]: A list of objects containing task details, or None if the query fails.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return None
    database_id, _, headers = config

    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    date_property_name = "Date"
    payload = {
        "filter": {
            "and": [
                {"property": date_property_name, "date": {"on_or_after": start_date}},
                {"property": date_property_name, "date": {"on_or_before": end_date}}
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        raw_notion_response = response.json().get("results", [])
        # SYSTEM UPDATE: Return clean AgentTask instances
        return [AgentTask.model_validate(task) for task in raw_notion_response]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Query Error in get_tasks_by_date_range: {e}")
        if e.response is not None:
            logger.error(f"Notion Error Detail: {e.response.text}")
        return None


@tool
def search_notion_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    min_time_spent: Optional[int] = None,
    max_time_spent: Optional[int] = None,
) -> Optional[List[AgentTask]]:
    """
    Performs complex filtering on the Master Database to find specific tasks.
    
    Use this tool when the agent needs to find tasks by status, category, or time constraints 
    (e.g., 'Show me all complete study tasks' or 'Tasks taking over 60 minutes').
    
    Args:
        status (Optional[str]): Task status (e.g., 'Complete', 'In Progress').
        category (Optional[str]): Task category/type (e.g., 'Study', 'Work').
        min_time_spent (Optional[int]): Minimum time spent in minutes.
        max_time_spent (Optional[int]): Maximum time spent in minutes.

    Returns:
        List[AgentTask]: A list of objects containing task details matching the filters.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return None
    database_id, _, headers = config
    
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    filter_conditions = []

    if status:
        filter_conditions.append({"property": "Status", "select": {"equals": status}})

    if category:
        filter_conditions.append({"property": "Type", "multi_select": {"contains": category}})

    if min_time_spent is not None:
        filter_conditions.append({"property": "Time", "number": {"greater_than_or_equal_to": min_time_spent}})
        
    if max_time_spent is not None:
        filter_conditions.append({"property": "Time", "number": {"less_than_or_equal_to": max_time_spent}})

    payload: Dict[str, Any] = {}
    if filter_conditions:
        payload["filter"] = {"and": filter_conditions}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        pprint(results)
        # SYSTEM UPDATE: Return clean AgentTask instances
        return [AgentTask.model_validate(task) for task in results]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Query Error in search_notion_tasks: {e}")
        return None

@tool
def get_notion_monthly_goals(month_name: str) -> Optional[dict[str, list[str]]]:
    """
    Retrieves the list of goals for a specific month.
    
    Use this tool when the agent needs to fetch the defined goals for a month (e.g., 'What are my goals for June?').
    It looks up the month page and extracts the goal entries from the relevant section.

    Args:
        month_name (str): The name of the month to retrieve goals for (e.g., 'June').
    Returns:
        dict[str, list[str]]: A dictionary mapping goal categories (e.g., 'Work', 'Study') to their corresponding lists of goal descriptions for the target month. Returns None if retrieval fails.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return None
    _, _, headers = config

    # Load month and section IDs from the JSON map
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            important_info = json.load(file)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return None

    month_info = important_info.get("months", {}).get(month_name)
    if not month_info:
        logger.error(f"Month '{month_name}' not found in JSON map.")
        return None

    goals_section_id = month_info.get("sections", {}).get("Monthly Goals")
    if not goals_section_id:
        logger.error(f"'Goals' section not found for month '{month_name}'.")
        return None

    url = f"https://api.notion.com/v1/blocks/{goals_section_id}/children"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        ids = {block["toggle"]["rich_text"][0]["plain_text"]:block["id"] for block in json_response["results"]}
        goals = {}

        for goal_type, id in ids.items():
            goals[goal_type] = []
            url = f"https://api.notion.com/v1/blocks/{id}/children"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            json_response = response.json()
            
            for block in json_response.get("results", []):
                block_type = block.get("type", "")
                type_object = block.get(block_type, {})
                if rich_text_list := type_object.get("rich_text", []):
                    goal_text = rich_text_list[0].get("plain_text", "")
                    if goal_text:

                        goals[goal_type].append(goal_text)
        
        return goals
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error while fetching goals for '{month_name}': {e}")
        return None


@tool
def get_notion_weekly_objectives(month_name: str, week_name: str) -> Optional[List[str]]:
    """
    Retrieves the list of objectives for a specific week within a month.
    
    Use this tool when the agent needs to fetch weekly objectives (e.g., 'What are my objectives for the first week of June?').
    It looks up the month page, finds the relevant week section, and extracts the objective entries.

    Args:
        month_name (str): The name of the month (e.g., 'June').
        week_name (str): The name of the week ('First Week', 'Second Week', 'Third Week', 'Fourth Week', 'Fifth Week').
    Returns:
        List[str]: A list of objective descriptions for the specified week, or None if retrieval fails.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return None
    _, _, headers = config

    # Load month and section IDs from the JSON map
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            important_info = json.load(file)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return None

    month_info = important_info.get("months", {}).get(month_name)
    if not month_info:
        logger.error(f"Month '{month_name}' not found in JSON map.")
        return None

    week_section_id = month_info.get("sections", {}).get(week_name)
    if not week_section_id:
        logger.error(f"'{week_name}' section not found for month '{month_name}'.")
        return None

    url = f"https://api.notion.com/v1/blocks/{week_section_id}/children"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        
        week_objectives_id = [block["id"] for block in json_response["results"] if block.get("type", None) == "toggle" and block.get("toggle", {}).get("rich_text", [])[0].get("text", {}).get("content", "") == "Weekly Objectives:"][0]
        
        url = f"https://api.notion.com/v1/blocks/{week_objectives_id}/children"

        response_2 = requests.get(url, headers=headers)
        response_2.raise_for_status()
        json_response_2 = response_2.json()

        objectives = []
        for block in json_response_2.get("results", []):
            block_type = block.get("type", "")
            type_object = block.get(block_type, {})
            if rich_text_list := type_object.get("rich_text", []):
                objective_text = rich_text_list[0].get("plain_text", "")
                if objective_text:
                    objectives.append(objective_text)
        
        return objectives
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error while fetching objectives for '{week_name}' of '{month_name}': {e}")
        return None


@tool
def create_one_notion_task(
    name: str,
    status: Optional[str] = "Not started",
    categories: Optional[List[str]] = None,
    time_spent: Optional[int] = None,
    date: Optional[str] = None,
    icon_type: Optional[str] = None,
    icon_id: Optional[str] = None
) -> Optional[str]:
    """
    Creates a new task in the Master Database.
    
    Use this tool to add new entries to the task database based on user requests. 
    It automatically maps properties like status, categories, time, and date.

    Args:
        name (str): The title of the task.
        status (str): The initial status.
        categories (List[str]): List of categories.
        time_spent (int): Time spent in minutes.
        date (str): Date in ISO 8601 format (YYYY-MM-DD).
        icon_type (str): Icon of task (e.g. 'emoji', 'custom_emoji')
        icon_id (str): if the icon_type was was custom_emoji you must provide icon_id, if the icon_type was emoji you must provide emoji
    Returns:
        str: The new task's page_id if successful, or None if it fails.
    """

    config = get_db_id_with_tokens_with_headers()
    if not config:
        return None
    database_id, _, headers = config

    url = "https://api.notion.com/v1/pages"
    properties: Dict[str, Any] = {
        "Name": {"title": [{"text": {"content": name}}]}
    }

    if status:
        properties["Status"] = {"select": {"name": status}}
    if categories:
        properties["Type"] = {"multi_select": [{"name": cat} for cat in categories]}
    if time_spent is not None:
        properties["Time"] = {"number": time_spent}
    if date:
        properties["Date"] = {"date": {"start": date}}

    
    if icon_type == "custom_emoji":
        icon = {"icon": {"custom_emoji": {"id": icon_id}}}
    else:
        icon = {'icon': {'emoji': icon_id}}
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "icon": icon
    }

    if icon_id:
        if icon_type == "custom_emoji":
            payload["icon"] = {"custom_emoji": {"id": icon_id}}
        else:
            payload["icon"] = {'emoji': icon_id}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        new_page_id = response.json().get("id")
        logger.info(f"Successfully created task: '{name}' (ID: {new_page_id})")
        return new_page_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create task: {e}")
        return None
    

@tool
def create_multiple_notion_tasks(
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Creates multiple new tasks in the Master Database in a single tool call.
    
    Use this tool when the user asks to create several tasks at once.
    
    Args:
        tasks (List[Dict[str, Any]]): A list of task dictionaries. Each dictionary MUST contain a 'name' (str).
            Optional keys for each dictionary:
            - 'status' (str): e.g., "Not started", "In progress"
            - 'categories' (List[str]): List of category names.
            - 'time_spent' (int): Time spent in minutes.
            - 'date' (str): Date in ISO 8601 format (YYYY-MM-DD).
            -  'icon_type' (str): Icon of task (e.g. 'emoji', 'custom_emoji')
            -  'icon_id' (str): if the icon_type was was custom_emoji you must provide icon_id, if the icon_type was emoji you must provide emoji

    Returns:
        Dict[str, Any]: A summary dictionary containing:
            - 'successful_ids' (List[str]): IDs of successfully created tasks.
            - 'failed_tasks' (List[Dict]): Details of tasks that failed to create.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        logger.error("Failed to retrieve Notion configuration.")
        return {"error": "Authentication or Configuration failed."}
        
    database_id, _, headers = config
    url = "https://api.notion.com/v1/pages"
    
    successful_ids = []
    failed_tasks = []

    for task in tasks:
        # استخراج البيانات الأساسية وتعيين القيم الافتراضية
        name = task.get("name")
        if not name:
            logger.warning("Task skipped: Missing required 'name' field.")
            failed_tasks.append({"task_data": task, "reason": "Missing 'name'"})
            continue

        status = task.get("status", "Not started")
        categories = task.get("categories")
        time_spent = task.get("time_spent")
        date = task.get("date")

        # بناء قاموس الخصائص (Properties)
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": name}}]}
        }

        if status:
            properties["Status"] = {"select": {"name": status}}
        if categories:
            properties["Type"] = {"multi_select": [{"name": cat} for cat in categories]}
        if time_spent is not None:
            properties["Time"] = {"number": time_spent}
        if date:
            properties["Date"] = {"date": {"start": date}}

        

        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        if task.get("icon_id", None):
            if task.get("icon_type", None) == "custom_emoji":
                payload["icon"] = {"custom_emoji": {"id": task.get("icon_id", None)}}
            else:
                payload["icon"] = {'emoji': task.get("icon_id", None)}

        # إرسال الطلب ومعالجة الاستجابة لكل مهمة
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            new_page_id = response.json().get("id")
            successful_ids.append(new_page_id)
            logger.info(f"Successfully created task: '{name}' (ID: {new_page_id})")
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to create task '{name}': {e}"
            logger.error(error_msg)
            failed_tasks.append({"name": name, "error": str(e)})

    # إرجاع ملخص للـ Agent ليعرف ما تم إنجازه وما فشل
    return {
        "total_attempted": len(tasks),
        "successful_count": len(successful_ids),
        "successful_ids": successful_ids,
        "failed_tasks": failed_tasks
    }


@tool
def update_notion_task(
    page_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    categories: Optional[List[str]] = None,
    time_spent: Optional[int] = None,
    date: Optional[str] = None
) -> bool:
    """
    Updates the properties of an existing Notion task.
    
    Use this tool to modify existing tasks (e.g., changing status to 'Complete', 
    updating date, or changing the task name). Provide only the fields to be updated.

    Args:
        page_id (str): The unique ID of the task page to update.
        name (Optional[str]): New title for the task.
        status (Optional[str]): New status.
        categories (Optional[List[str]]): New list of categories.
        time_spent (Optional[int]): New time spent.
        date (Optional[str]): New date (YYYY-MM-DD).

    Returns:
        bool: True if successful, False otherwise.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return False
    _, _, headers = config

    url = f"https://api.notion.com/v1/pages/{page_id}"
    properties: Dict[str, Any] = {}

    if name:
        properties["Name"] = {"title": [{"text": {"content": name}}]}
    if status:
        properties["Status"] = {"select": {"name": status}}
    if categories is not None:
        properties["Type"] = {"multi_select": [{"name": cat} for cat in categories]}
    if time_spent is not None:
        properties["Time"] = {"number": time_spent}
    if date:
        properties["Date"] = {"date": {"start": date}}

    if not properties:
        logger.warning("No properties provided to update.")
        return False

    try:
        response = requests.patch(url, headers=headers, json={"properties": properties})
        response.raise_for_status()
        logger.info(f"Successfully updated task ID: {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update task: {e}")
        return False


@tool
def delete_notion_task(page_id: str) -> bool:
    """
    Deletes/Archives an existing Notion task.
    
    Use this tool when the user explicitly asks to remove or archive a task. 
    This performs a soft-delete by archiving the page in Notion.

    Args:
        page_id (str): The unique ID of the task page to archive.

    Returns:
        bool: True if successful, False otherwise.
    """
    config = get_db_id_with_tokens_with_headers()
    if not config:
        return False
    _, _, headers = config
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    try:
        response = requests.patch(url, headers=headers, json={"archived": True})
        response.raise_for_status()
        logger.info(f"Successfully deleted (archived) task ID: {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to delete task: {e}")
        return False
    

notion_tools = [
    update_months_ids,
    update_month_sections_ids,
    get_tasks_by_date_range,
    search_notion_tasks,
    get_notion_monthly_goals,
    get_notion_weekly_objectives,
    create_one_notion_task,
    create_multiple_notion_tasks,
    update_notion_task,
    delete_notion_task
]