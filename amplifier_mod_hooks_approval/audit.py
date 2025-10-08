"""Audit trail logging for approval decisions."""

import json
import logging
from datetime import datetime
from pathlib import Path

from amplifier_core import ApprovalRequest
from amplifier_core import ApprovalResponse

logger = logging.getLogger(__name__)

# Default audit file location
DEFAULT_AUDIT_FILE = Path.home() / ".amplifier" / "audit" / "approvals.jsonl"


def audit_log(request: ApprovalRequest, response: ApprovalResponse, audit_file: Path | None = None) -> None:
    """
    Log approval request and response to audit trail.

    Args:
        request: Approval request
        response: Approval response
        audit_file: Optional custom audit file path
    """
    if audit_file is None:
        audit_file = DEFAULT_AUDIT_FILE

    # Ensure directory exists
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    # Build audit record
    record = {
        "timestamp": datetime.now().isoformat(),
        "request": {
            "tool_name": request.tool_name,
            "action": request.action,
            "risk_level": request.risk_level,
            "details": request.details,
            "timeout": request.timeout,
        },
        "response": {"approved": response.approved, "reason": response.reason, "remember": response.remember},
    }

    # Append to JSONL file
    try:
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
