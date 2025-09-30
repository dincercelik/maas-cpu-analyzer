"""
Configuration loader that supports environment variables with a fallback to
values defined in a local config.ini file.

Priority order:
1) Environment variables
2) config.ini

Expected config.ini structure:

[maas]
url = http://your-maas-server:5240/MAAS
api_key = consumer:token:secret

[openstack]
auth_url = http://your-openstack:5000/v3
username = your-username
password = your-password
project_name = your-project
user_domain_name = Default
project_domain_name = Default
"""

import os
from configparser import ConfigParser
from contextlib import suppress
from typing import Optional

_CONFIG_PATHS = [
    os.path.join(os.getcwd(), "config.ini"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini"),
]


def _load_config() -> ConfigParser:
    parser = ConfigParser()

    # Allow overriding the path via CONFIG_INI environment variable
    override_path = os.environ.get("CONFIG_INI")
    if override_path:
        _paths = [override_path]
    else:
        _paths = _CONFIG_PATHS

    for path in _paths:
        with suppress(Exception):
            if os.path.exists(path):
                parser.read(path)
                break

    return parser


def get_value(
    env_var_name: str, section: str, option: str, default: Optional[str] = None
) -> Optional[str]:
    """Get a configuration value.

    Lookup order:
    1. Environment variable `env_var_name`
    2. config.ini -> [section] option
    3. default
    """
    # 1) Environment
    value = os.environ.get(env_var_name)
    if value is not None and value != "":
        return value

    # 2) config.ini
    parser = _load_config()
    with suppress(Exception):
        if parser.has_section(section) and parser.has_option(section, option):
            ini_value = parser.get(section, option)
            if ini_value is not None and ini_value != "":
                return ini_value

    # 3) default
    return default
