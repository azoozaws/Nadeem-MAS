from pathlib import Path
import asyncio, os
from datetime import datetime, timedelta
from src.utils.logger import setup_custom_logger

logger = setup_custom_logger(__name__)

def _get_latest_file_sync() -> Path | None:

    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent
    yesterday = datetime.now() - timedelta(days=1)
    file_paht = (
        project_root 
        / "data" 
        / "guidelines" 
        / yesterday.strftime("%Y") 
        / yesterday.strftime("%B")
    )
    
    all_files = file_paht.glob("*.md")

    try:
        last_file = max(all_files, key=lambda f: f.stat().st_mtime)
    except ValueError as e:
        logger.warning(f"⚠️ No markdown files found inside: {file_paht.name}, Error Message: ", e)
        return None
        
    
    return last_file


async def get_yesterday_context():

    file_path = await asyncio.to_thread(_get_latest_file_sync)

    if not file_path:
        return None
    
    file_content = None
    with open(file_path, "r", encoding="UTF-8") as file:
        file_content = file.read()
    return file_content