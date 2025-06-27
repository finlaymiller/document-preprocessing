from typing import Any, Dict

import yaml


def load_config(path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    path : str
        Path to the YAML file.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the configuration.
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)
