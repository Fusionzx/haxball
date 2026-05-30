from __future__ import annotations
import asyncio
from typing import Any, TYPE_CHECKING
from .utils import calculate_distance, is_colliding

if TYPE_CHECKING:
    from .extended import RoomExtended

class AbstractDisc:
    __slots__ = (
        "_x", "_y", "_xspeed", "_yspeed", "_xgravity", "_ygravity",
        "_radius", "_b_coeff", "_inv_mass", "_damping", "_c_mask", "_c_group",
        "_color", "_settings", "_room", "_disc_id", "_is_player"
    )

    def __init__(self, **kwargs: Any) -> None:
        self._x: float | None = kwargs.get("x")
        self._y: float | None = kwargs.get("y")
        self._xspeed: float | None = kwargs.get("xspeed")
        self._yspeed: float | None = kwargs.get("yspeed")
        self._xgravity: float | None = kwargs.get("xgravity")
        self._ygravity: float | None = kwargs.get("ygravity")
        self._radius: float | None = kwargs.get("radius")
        self._b_coeff: float | None = kwargs.get("b_coeff") or kwargs.get("bCoef")
        self._inv_mass: float | None = kwargs.get("inv_mass") or kwargs.get("invMass")
        self._damping: float | None = kwargs.get("damping")
        self._c_mask: int | None = kwargs.get("c_mask") or kwargs.get("cMask")
        self._c_group: int | None = kwargs.get("c_group") or kwargs.get("cGroup")
        self._color: int | None = kwargs.get("color")
        self._settings: dict[str, Any] = kwargs.get("settings") if kwargs.get("settings") is not None else {}
        self._room: Any = kwargs.get("room")
        self._disc_id: int | None = kwargs.get("disc_id")
        self._is_player: bool = kwargs.get("is_player", False)

    def _set_property(self, key: str, value: Any) -> None:
        setattr(self, f"_{key}", value)
        room: RoomExtended | None = getattr(self, "_room", None)
        if room is not None and self._disc_id is not None:
            native = getattr(room, "native", None)
            if native is not None:
                if self._is_player:
                    asyncio.create_task(native.set_player_disc_properties(self._disc_id, {key: value}))
                else:
                    asyncio.create_task(native.set_disc_properties(self._disc_id, {key: value}))

    @property
    def x(self) -> float | None: return self._x
    @x.setter
    def x(self, value: float | None) -> None: self._set_property("x", value)

    @property
    def y(self) -> float | None: return self._y
    @y.setter
    def y(self, value: float | None) -> None: self._set_property("y", value)

    @property
    def xspeed(self) -> float | None: return self._xspeed
    @xspeed.setter
    def xspeed(self, value: float | None) -> None: self._set_property("xspeed", value)

    @property
    def yspeed(self) -> float | None: return self._yspeed
    @yspeed.setter
    def yspeed(self, value: float | None) -> None: self._set_property("yspeed", value)

    @property
    def xgravity(self) -> float | None: return self._xgravity
    @xgravity.setter
    def xgravity(self, value: float | None) -> None: self._set_property("xgravity", value)

    @property
    def ygravity(self) -> float | None: return self._ygravity
    @ygravity.setter
    def ygravity(self, value: float | None) -> None: self._set_property("ygravity", value)

    @property
    def radius(self) -> float | None: return self._radius
    @radius.setter
    def radius(self, value: float | None) -> None: self._set_property("radius", value)

    @property
    def b_coeff(self) -> float | None: return self._b_coeff
    @b_coeff.setter
    def b_coeff(self, value: float | None) -> None: self._set_property("b_coeff", value)

    @property
    def inv_mass(self) -> float | None: return self._inv_mass
    @inv_mass.setter
    def inv_mass(self, value: float | None) -> None: self._set_property("inv_mass", value)

    @property
    def damping(self) -> float | None: return self._damping
    @damping.setter
    def damping(self, value: float | None) -> None: self._set_property("damping", value)

    @property
    def c_mask(self) -> int | None: return self._c_mask
    @c_mask.setter
    def c_mask(self, value: int | None) -> None: self._set_property("c_mask", value)

    @property
    def c_group(self) -> int | None: return self._c_group
    @c_group.setter
    def c_group(self, value: int | None) -> None: self._set_property("c_group", value)

    @property
    def color(self) -> int | None: return self._color
    @color.setter
    def color(self, value: int | None) -> None: self._set_property("color", value)

    @property
    def settings(self) -> dict[str, Any]: return self._settings
    @settings.setter
    def settings(self, value: dict[str, Any]) -> None: self._settings = value

    def distance_to(self, other: AbstractDisc) -> float | None:
        return calculate_distance(self.x, self.y, other.x, other.y)

    def colliding_with(self, other: AbstractDisc) -> bool:
        return is_colliding(self.x, self.y, self.radius, other.x, other.y, other.radius)


class Disc(AbstractDisc):
    __slots__ = ("_index",)

    def __init__(self, index: int, **kwargs: Any) -> None:
        kwargs.setdefault("disc_id", index)
        kwargs.setdefault("is_player", False)
        super().__init__(**kwargs)
        self._index = index

    @property
    def index(self) -> int: return self._index
    @index.setter
    def index(self, value: int) -> None: self._index = value
