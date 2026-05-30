from __future__ import annotations
from typing import Any
from .utils import calculate_distance, is_colliding

class AbstractDisc:
    __slots__ = (
        "x", "y", "xspeed", "yspeed", "xgravity", "ygravity",
        "radius", "b_coeff", "inv_mass", "damping", "c_mask", "c_group",
        "color", "settings"
    )

    def __init__(self, **kwargs: Any) -> None:
        self.x: float | None = kwargs.get("x")
        self.y: float | None = kwargs.get("y")
        self.xspeed: float | None = kwargs.get("xspeed")
        self.yspeed: float | None = kwargs.get("yspeed")
        self.xgravity: float | None = kwargs.get("xgravity")
        self.ygravity: float | None = kwargs.get("ygravity")
        self.radius: float | None = kwargs.get("radius")
        self.b_coeff: float | None = kwargs.get("b_coeff") or kwargs.get("bCoef")
        self.inv_mass: float | None = kwargs.get("inv_mass") or kwargs.get("invMass")
        self.damping: float | None = kwargs.get("damping")
        self.c_mask: int | None = kwargs.get("c_mask") or kwargs.get("cMask")
        self.c_group: int | None = kwargs.get("c_group") or kwargs.get("cGroup")
        self.color: int | None = kwargs.get("color")
        self.settings: dict[str, Any] = kwargs.get("settings") if kwargs.get("settings") is not None else {}

    def distance_to(self, other: AbstractDisc) -> float | None:
        """Calculates Euclidean distance to another disc."""
        return calculate_distance(self.x, self.y, other.x, other.y)

    def colliding_with(self, other: AbstractDisc) -> bool:
        """Checks if colliding with another disc."""
        return is_colliding(
            self.x, self.y, self.radius,
            other.x, other.y, other.radius
        )


class Disc(AbstractDisc):
    __slots__ = ("index",)

    def __init__(self, index: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.index = index
