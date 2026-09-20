"""Typed factory boundaries and fail-closed parsing of model proposals."""
from __future__ import annotations
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any

class Component(str, Enum):
    ENGINE = "engine"
    OBSERVATION = "observation_adapter"
    RECONSTRUCTION = "reconstruction"
    SEARCH = "search"

class Verdict(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    NO_CHANGE = "no_change"

@dataclass(frozen=True)
class Bounds:
    nodes: int
    max_actions: int
    turn_pairs: int
    deadline_seconds: int
    memory_bytes: int
    concurrency: int
    max_model_calls: int
    max_candidate_attempts: int

    @classmethod
    def parse(cls, obj):
        exact(obj, {f.name for f in fields(cls)})
        for k, v in obj.items():
            if type(v) is not int or v < 1: raise ValueError("positive integer required: " + k)
        b = cls(**obj)
        if b.concurrency > 2 or b.max_candidate_attempts > 2 or b.max_model_calls > 12:
            raise ValueError("initial integration exceeds supervised epoch bounds")
        if b.max_actions > 512: raise ValueError("native action cap exceeded")
        return b

@dataclass(frozen=True)
class Plan:
    status: str
    component: Component
    issue_ids: list[str]
    hypothesis: str
    changes: str
    validation: str
    risks: list[str]

    @classmethod
    def parse(cls, obj):
        exact(obj, {f.name for f in fields(cls)})
        if obj["status"] not in ("propose", "no_safe_change"): raise ValueError("invalid plan status")
        if not isinstance(obj["issue_ids"], list) or not all(isinstance(x, str) for x in obj["issue_ids"]): raise ValueError("invalid origins")
        for k in ("hypothesis", "changes", "validation"):
            if not isinstance(obj[k], str): raise ValueError("invalid plan text")
        if not isinstance(obj["risks"], list) or not all(isinstance(x,str) for x in obj["risks"]): raise ValueError("invalid risks")
        return cls(**{**obj, "component": Component(obj["component"])})

@dataclass(frozen=True)
class Review:
    approve: bool
    findings: list[str]
    rationale: str

    @classmethod
    def parse(cls, obj):
        exact(obj, {f.name for f in fields(cls)})
        if type(obj["approve"]) is not bool: raise ValueError("review approval must be boolean")
        if not isinstance(obj["findings"], list) or not all(isinstance(x,str) for x in obj["findings"]): raise ValueError("invalid review findings")
        if not isinstance(obj["rationale"],str): raise ValueError("invalid review rationale")
        return cls(**obj)

@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str

    @classmethod
    def parse(cls, obj):
        exact(obj, {"path", "old", "new"})
        if not all(isinstance(v, str) for v in obj.values()): raise ValueError("edit fields must be strings")
        if not obj["old"] or obj["old"] == obj["new"]: raise ValueError("edit must replace nonempty differing text")
        return cls(**obj)

def exact(obj: Any, keys: set[str]):
    if not isinstance(obj, dict) or set(obj) != keys:
        raise ValueError("expected exactly these fields: " + ", ".join(sorted(keys)))

def safe_relative(path: str):
    from pathlib import PurePosixPath
    p = PurePosixPath(path)
    if p.is_absolute() or not p.parts or any(x in (".","..") for x in p.parts) or "\\" in path:
        raise ValueError("unsafe relative path")
    return path
