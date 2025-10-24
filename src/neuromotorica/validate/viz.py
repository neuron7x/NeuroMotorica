# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from typing import List
from .run import SectionResult
def charts_section(sections: List[SectionResult])->str:
    items=[f"<details><summary>Metrics: {s.name}</summary><pre>{s.metrics}</pre></details>" for s in sections]
    return "\n".join(items)
