"""AutoRanksOFF mod package: public API re-export."""
from .constants import AUTORANKS_FILES
from .patch import modify_autoranks_text, describe_autoranks_patch

__all__ = ['AUTORANKS_FILES', 'modify_autoranks_text', 'describe_autoranks_patch']
