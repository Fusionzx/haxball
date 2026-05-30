from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GeoConfig(BaseModel):
    code: str = Field(default="xx", min_length=2, max_length=8)
    lat: float = 0.0
    lon: float = 0.0


class HaxballConfig(BaseModel):
    room_name: str = Field(alias="roomName", min_length=1)
    player_name: str | None = Field(default=None, alias="playerName")
    password: str | None = None
    max_players: int = Field(default=16, alias="maxPlayers", ge=1, le=50)
    public: bool = True
    no_player: bool = Field(default=True, alias="noPlayer")
    token: str | None = None
    geo: GeoConfig | None = None

    proxy_server: str | None = None
    headless: bool = True
    browser_executable_path: str | None = None
    browser_channel: str | None = None
    browser_args: list[str] = Field(default_factory=list)
    timeout_ms: int = Field(default=30_000, ge=1)
    headless_host_url: str = "https://html5.haxball.com/headless"

    class Config:
        populate_by_name = True
        extra = "allow"

    @field_validator("browser_args")
    @classmethod
    def _validate_browser_args(cls, value: list[str]) -> list[str]:
        return list(value)

    @model_validator(mode="after")
    def _normalize(self) -> "HaxballConfig":
        if self.player_name is None and not self.no_player:
            self.player_name = "Haxball.Py"
        return self

    def to_hbinit_config(self) -> dict[str, Any]:
        data = {
            "roomName": self.room_name,
            "maxPlayers": self.max_players,
            "public": self.public,
            "noPlayer": self.no_player,
        }
        if self.token is not None:
            data["token"] = self.token
        if self.player_name is not None:
            data["playerName"] = self.player_name
        if self.password is not None:
            data["password"] = self.password
        if self.geo is not None:
            data["geo"] = self.geo.model_dump()
        return data
