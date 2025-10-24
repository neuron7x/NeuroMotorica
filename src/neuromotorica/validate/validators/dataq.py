# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from typing import Dict, Any
from ..run import SectionResult

def validate_data_quality(thresholds: Dict[str,Any], run_dir):
    s = SectionResult(name="Data Quality"); s.metrics={"datasets": 0}
    return s
