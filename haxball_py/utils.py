from __future__ import annotations
import math
from typing import Any

def decode_ip_from_conn(conn: str | None) -> str | None:
    """Decodes the connection string to extract an IP address if possible.
    Haxball conn is often a hex string representing the IP/port or connection identifier.
    """
    if not conn:
        return None
    try:
        # If it's a hex representation of an IP (4 bytes or more)
        if len(conn) >= 8:
            parts = [str(int(conn[i:i+2], 16)) for i in range(0, 8, 2)]
            return ".".join(parts)
    except Exception:
        pass
    return conn

def calculate_distance(x1: float | None, y1: float | None, x2: float | None, y2: float | None) -> float | None:
    """Calculates the Euclidean distance between two points."""
    if x1 is None or y1 is None or x2 is None or y2 is None:
        return None
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def is_colliding(x1: float | None, y1: float | None, r1: float | None,
                 x2: float | None, y2: float | None, r2: float | None) -> bool:
    """Checks if two circular discs are colliding."""
    dist = calculate_distance(x1, y1, x2, y2)
    if dist is None or r1 is None or r2 is None:
        return False
    return dist <= (r1 + r2)
