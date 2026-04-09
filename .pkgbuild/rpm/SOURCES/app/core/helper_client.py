"""Compatibility shim for the removed privileged helper service.

The old root helper is intentionally disabled. All privileged operations should
use explicit pkexec/sudo elevation through core.privilege.
"""

from typing import Any, Dict


class HelperError(RuntimeError):
    pass


DEFAULT_TIMEOUT = 15.0


def helper_available(timeout: float = 2.0) -> bool:
    del timeout
    return False


def send_request(payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    del payload, timeout
    return {
        "code": 1,
        "output": (
            "TuxPulse helper service is disabled for security reasons. "
            "Use the built-in pkexec/sudo elevation flow instead."
        ),
    }
