"""Fast floor queries (LT) over the static polygons with a bounds prefilter."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mm9r_common"))
from dungeon.source import Project, Source, floor_below


class Floors:
    def __init__(self):
        p = Project.load(Path(__file__).resolve().parents[1], install=False)
        s = Source(p)
        polys = []
        for name in ["PhysicsBSP"] + [m for m in s.models if m.startswith(("Terrain", "WorldObject"))]:
            try:
                polys += s.polygons(name)
            except KeyError:
                pass
        self.polys = [q for q in polys if q.normal[1] >= 0.7 and q.role == "static"]
        self.lo = np.array([q.points.min(0) for q in self.polys])
        self.hi = np.array([q.points.max(0) for q in self.polys])

    def __call__(self, x, z, top=2000.0):
        idx = np.nonzero((self.lo[:, 0] <= x) & (x <= self.hi[:, 0]) & (self.lo[:, 2] <= z) & (z <= self.hi[:, 2]))[0]
        return floor_below([self.polys[i] for i in idx], [x, top, z])
