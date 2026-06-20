"""Heuristic helpers."""


def _get_coords(point):
    """
    Extract (x, y) coordinates from various point formats:
    - Node objects with 'x' and 'y' attributes
    - Dictionary with 'x' and 'y' keys
    - Tuples or lists of at least 2 elements
    """
    if hasattr(point, "x") and hasattr(point, "y"):
        return point.x, point.y
    if isinstance(point, dict) and "x" in point and "y" in point:
        return point["x"], point["y"]
    try:
        return point[0], point[1]
    except (TypeError, IndexError):
        raise TypeError(f"Cannot extract coordinates from point of type: {type(point)}")


def manhattan(a, b):
    """Manhattan distance (L1 norm)."""
    x1, y1 = _get_coords(a)
    x2, y2 = _get_coords(b)
    return abs(x1 - x2) + abs(y1 - y2)


def euclidean(a, b):
    """Euclidean distance (L2 norm)."""
    x1, y1 = _get_coords(a)
    x2, y2 = _get_coords(b)
    dx = x1 - x2
    dy = y1 - y2
    return (dx * dx + dy * dy) ** 0.5


def chebyshev(a, b):
    """Chebyshev distance (L-infinity norm, for 8-way grid movement)."""
    x1, y1 = _get_coords(a)
    x2, y2 = _get_coords(b)
    return max(abs(x1 - x2), abs(y1 - y2))


def octile(a, b):
    """Octile distance (for 8-way grid movement with diagonal cost sqrt(2))."""
    x1, y1 = _get_coords(a)
    x2, y2 = _get_coords(b)
    dx = abs(x1 - x2)
    dy = abs(x1 - y2)
    return (dx + dy) + (2 ** 0.5 - 2) * min(dx, dy)


def custom_heuristic(a, b):
    """Custom heuristic (defaulting to Manhattan)."""
    return manhattan(a, b)
