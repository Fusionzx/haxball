from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _BaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True, str_strip_whitespace=False)


class Position(_BaseModel):
    x: float = 0.0
    y: float = 0.0


class Player(_BaseModel):
    id: int
    name: str
    team: int
    admin: bool = False
    position: Position | None = None
    auth: str | None = None
    conn: str | None = None


class Scores(_BaseModel):
    red: int = 0
    blue: int = 0
    time: float = 0.0
    score_limit: int = Field(default=0, alias="scoreLimit")
    time_limit: float = Field(default=0.0, alias="timeLimit")


class DiscProperties(_BaseModel):
    x: float | None = None
    y: float | None = None
    xspeed: float | None = None
    yspeed: float | None = None
    gravity: float | None = None
    invMass: float | None = None
    damping: float | None = None
    radius: float | None = None
    bCoef: float | None = Field(default=None, alias="bCoef")
    cGroup: int | None = None
    cMask: int | None = None
    color: int | None = None

    @classmethod
    def from_js(cls, value: Any) -> "DiscProperties":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls()
        if isinstance(value, dict):
            return cls.model_validate(value)
        return cls.model_validate(dict(value))
