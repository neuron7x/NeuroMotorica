from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable
from dataclasses import asdict
from functools import lru_cache
from typing import Dict, Tuple

from .models.nmj import NMJParams
from .models.enhanced_nmj import EnhancedNMJParams
from .models.muscle import MuscleParams

PROFILE_DIR = resources.files("neuromotorica") / "data" / "profiles"

class ProfileNotFoundError(ValueError):
    """Raised when a requested simulation profile is unavailable."""


def _load_profile_file(path: Traversable) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    stem = path.name.rsplit(".", 1)[0]
    name = data.get("name") or stem
    data["name"] = name
    data.setdefault("description", "")
    data["_path"] = str(path)
    return data


@lru_cache(maxsize=None)
def _profiles_index() -> Dict[str, Dict]:
    if not PROFILE_DIR.is_dir():
        raise FileNotFoundError(f"Profile directory not found: {PROFILE_DIR}")
    profiles: Dict[str, Dict] = {}
    json_paths = sorted(
        (child for child in PROFILE_DIR.iterdir() if child.name.endswith(".json")),
        key=lambda traversable: traversable.name,
    )
    for json_path in json_paths:
        profile = _load_profile_file(json_path)
        profiles[profile["name"]] = profile
    if not profiles:
        raise RuntimeError(f"No simulation profiles were discovered in {PROFILE_DIR}")
    return profiles


def available_profiles() -> Tuple[str, ...]:
    """Return the tuple of supported profile names."""
    return tuple(sorted(_profiles_index().keys()))


def get_profile(name: str) -> Dict:
    """Return the raw profile configuration dictionary."""
    try:
        return _profiles_index()[name]
    except KeyError as exc:
        raise ProfileNotFoundError(
            f"Unknown profile '{name}'. Available profiles: {', '.join(available_profiles())}"
        ) from exc


def profile_metadata(name: str) -> Dict:
    profile = get_profile(name)
    meta = dict(profile.get("metadata", {}))
    if "description" not in meta and profile.get("description"):
        meta["description"] = profile["description"]
    meta.setdefault("name", profile["name"])
    return meta


def build_profile_params(name: str) -> Tuple[NMJParams, EnhancedNMJParams, MuscleParams, Dict]:
    profile = get_profile(name)
    nmj_cfg = dict(profile.get("nmj", {}))
    enh_cfg = dict(profile.get("enhanced_nmj", {}))
    muscle_cfg = dict(profile.get("muscle", {}))
    enh_params = {**nmj_cfg, **enh_cfg}
    nmj_params = NMJParams(**nmj_cfg)
    enhanced_params = EnhancedNMJParams(**enh_params)
    muscle_params = MuscleParams(**muscle_cfg)
    meta = profile_metadata(name)
    return nmj_params, enhanced_params, muscle_params, meta


def extended_param_dicts(name: str) -> Tuple[Dict, Dict]:
    """Return dictionaries ready to initialise extended NMJ and muscle params."""
    nmj_params, enhanced_params, muscle_params, _ = build_profile_params(name)
    enhanced_dict = asdict(enhanced_params)
    muscle_dict = asdict(muscle_params)
    return enhanced_dict, muscle_dict
