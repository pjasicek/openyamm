"""Geometry checks shared by the offline lighting producer and its regression tests."""
import math


def face_basis(points):
    """Return an orthonormal chart basis from the largest native fan triangle.

    Legacy faces may begin with duplicate or collinear vertices. Only an entirely
    zero-area fan is degenerate; its first triangle is not sufficient evidence.
    """
    if len(points) < 3:
        return None
    best = None
    best_area_squared = 0.0
    for index in range(1, len(points) - 1):
        edge = tuple(points[index][k] - points[0][k] for k in range(3))
        other = tuple(points[index + 1][k] - points[0][k] for k in range(3))
        cross = (edge[1] * other[2] - edge[2] * other[1],
                 edge[2] * other[0] - edge[0] * other[2],
                 edge[0] * other[1] - edge[1] * other[0])
        area_squared = sum(value * value for value in cross)
        if area_squared > best_area_squared:
            best_area_squared = area_squared
            best = edge, cross
    if best is None or best_area_squared < 1e-6:
        return None
    edge, cross = best
    edge_length = math.sqrt(sum(value * value for value in edge))
    normal_length = math.sqrt(best_area_squared)
    axis_u = tuple(value / edge_length for value in edge)
    normal = tuple(value / normal_length for value in cross)
    axis_v = (normal[1] * axis_u[2] - normal[2] * axis_u[1],
              normal[2] * axis_u[0] - normal[0] * axis_u[2],
              normal[0] * axis_u[1] - normal[1] * axis_u[0])
    return axis_u, axis_v
