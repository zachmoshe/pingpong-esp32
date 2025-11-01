"""Utilities for loading and processing configuration files."""
import os
import json
from typing import Any, Dict


def expand_env_vars(obj: Any) -> Any:
    """
    Recursively expand environment variables in a configuration object.
    Supports ${VAR} and $VAR syntax via os.path.expandvars.
    
    Args:
        obj: The configuration object (dict, list, or primitive)
        
    Returns:
        The configuration object with all environment variables expanded
    """
    if isinstance(obj, dict):
        return {key: expand_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return os.path.expandvars(obj)
    else:
        return obj


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a JSON config file and expand all environment variables.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        The configuration dictionary with expanded environment variables
    """
    with open(config_path, "r") as f:
        cfg = json.load(f)
    return expand_env_vars(cfg)

