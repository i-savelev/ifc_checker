"""Публичный API пакета `ifc_checker_script`."""

from ifc_checker_script.checker import check_ifc
from ifc_checker_script.confighelper import (
    ifc_exist_in_ids_dict,
    read_json_config,
    save_json_config_template,
)
from ifc_checker_script.htmlparser import (
    delete_skipped,
    delete_skipped_from_one_html,
)

__all__ = [
    "check_ifc",
    "delete_skipped",
    "delete_skipped_from_one_html",
    "ifc_exist_in_ids_dict",
    "read_json_config",
    "save_json_config_template",
]
