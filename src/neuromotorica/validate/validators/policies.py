# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from typing import Dict, Any
from ..run import SectionResult

def validate_policies(thresholds: Dict[str,Any], run_dir):
    s = SectionResult(name="Security Policies"); s.metrics={"policies_checked": 0, "invalid": 0}
    return s
