from __future__ import annotations
import math


def decode_ip_from_conn(conn: str | None) -> str | None:
    """Decodes the HaxBall connection string to extract the player's IP address.
    The conn is a URI-encoded octet stream (e.g. '31372E...' -> '17.xx.xx.xx').
    """
    if not conn:
        return None
    try:
        raw = bytes.fromhex(conn)
        return raw.decode("ascii")
    except Exception:
        pass
    return conn


def calculate_distance(
    x1: float | None, y1: float | None, x2: float | None, y2: float | None
) -> float | None:
    """Calculates the Euclidean distance between two points."""
    if x1 is None or y1 is None or x2 is None or y2 is None:
        return None
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def is_colliding(
    x1: float | None,
    y1: float | None,
    r1: float | None,
    x2: float | None,
    y2: float | None,
    r2: float | None,
) -> bool:
    """Checks if two circular discs are colliding."""
    dist = calculate_distance(x1, y1, x2, y2)
    if dist is None or r1 is None or r2 is None:
        return False
    return dist <= (r1 + r2)
