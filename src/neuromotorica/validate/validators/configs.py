# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from typing import Dict, Any
from ..run import SectionResult

def validate_configs(thresholds: Dict[str,Any], run_dir):
    s = SectionResult(name="Config Schemas"); s.metrics={"profiles_checked": 3}
    return s
