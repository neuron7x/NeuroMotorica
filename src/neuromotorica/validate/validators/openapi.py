# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from typing import Dict, Any
from ..run import SectionResult, Finding

def validate_openapi(thresholds: Dict[str,Any], run_dir):
    s = SectionResult(name="OpenAPI")
    # Placeholder spec check (no FastAPI app in this generated bundle)
    # In real repo, fetch /openapi.json and run openapi-spec-validator + diff
    s.metrics = {"paths": 0, "schemas": 0}
    return s
