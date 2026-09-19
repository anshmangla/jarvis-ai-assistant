import importlib
import inspect
import os
from typing import Dict

from config import config
from skills.base import BaseSkill
from utils.logger import logger

def getattr_static(obj, attr, default=None):
    return getattr(obj, attr, default)

def load_plugins() -> Dict[str, BaseSkill]:
    """
    Dynamically load all skills from the skills folder and register them.
    
    Returns:
        Dict[str, BaseSkill]: A dictionary mapping skill names to their instantiated BaseSkill objects.
    """
    skills_dir = config.BASE_DIR / "skills"
    available_skills: Dict[str, BaseSkill] = {}
    
    if not skills_dir.exists():
        logger.warning(f"Skills directory not found at {skills_dir}")
        return available_skills
        
    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and filename != "__init__.py" and filename != "base.py":
            module_name = filename[:-3]
            try:
                # Import the module dynamically based on folder structure
                module = importlib.import_module(f"skills.{module_name}")
                
                # Find all classes in the module that inherit from BaseSkill but are not BaseSkill itself
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        # Ensure the class belongs to the actual module being inspected (prevents cross-imports)
                        if obj.__module__ == module.__name__:
                            skill_instance = obj()
                            if skill_instance.name:
                                available_skills[skill_instance.name] = skill_instance
                                logger.info(f"Successfully loaded skill plugin: {skill_instance.name}")
                            else:
                                logger.warning(f"Skill '{name}' in '{filename}' is missing a 'name' attribute. Skipping.")
            except Exception as e:
                logger.error(f"Error loading plugin from {filename}: {e}")
                
    return available_skills
