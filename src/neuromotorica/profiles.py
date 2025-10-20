from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable
from dataclasses import asdict
from functools import lru_cache
from typing import Dict, Tuple
import pathlib

from .models.nmj import NMJParams
from .models.enhanced_nmj import EnhancedNMJParams
from .models.muscle import MuscleParams

_PACKAGE_PROFILE_DIR = resources.files("neuromotorica") / "data" / "profiles"


def _default_profile_dir() -> Traversable:
    """Return the directory containing bundled profile definitions.

    Falls back to the repository-level ``data/profiles`` directory when the
    package data directory is unavailable (e.g. when running from a source
    checkout without installed resources).
    """

    if _PACKAGE_PROFILE_DIR.is_dir():
        return _PACKAGE_PROFILE_DIR

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    fallback = repo_root / "data" / "profiles"
    if fallback.is_dir():
        return fallback
    raise FileNotFoundError(
        "Profile directory not found. Expected either package data at"
        f" {_PACKAGE_PROFILE_DIR} or repository fallback at {fallback}."
    )

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
    profile_dir = _default_profile_dir()
    profiles: Dict[str, Dict] = {}
    json_paths = sorted(
        (child for child in profile_dir.iterdir() if child.name.endswith(".json")),
        key=lambda traversable: traversable.name,
    )
    for json_path in json_paths:
        profile = _load_profile_file(json_path)
        profiles[profile["name"]] = profile
    if not profiles:
        raise RuntimeError(f"No simulation profiles were discovered in {profile_dir}")
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
