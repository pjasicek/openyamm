"""Source geography shared by the playable SW crop and its visible terrain buffer."""
from collections import deque
import math
from build_plan import SOURCE, read

PLAYABLE = [-24576, 24576, -24576, 24576]
TERRAIN = [-32768, 32256, -32256, 32768]
CONTEXT_MAPS = [2, 3, 4, 6, 7, 8, 10, 11, 12]
CLASS_NAMES = ['Xeen rim/void', 'grassland', 'dirt/road', 'river water', 'Acid Pond',
               'desert', 'snow', 'lava', 'scorched ground', 'swamp', 'rock shelf']
CLASS_COLORS = ['#263b3d', '#bdc89e', '#b5a384', '#438eae', '#48acb7',
                '#dcc48a', '#e0e8e9', '#bf5532', '#685751', '#778867', '#a19a84']
MATERIALS = [None, 'mm8:grastyl', 'mm8:dirttyl', 'mm8:wtrtyl', 'mm8:wtrtyl',
             'mm7:7sand', 'mm7:7snow', 'mm8:lavtyl', 'mm8:plntyl', 'mm8:gstyl', 'mm8:rctyl']


class SourceGeography:
    def __init__(self):
        self.maps = {n: read(SOURCE/f'maps/dark_initial_state/maze{n:04}.dat.json') for n in range(1, 25)}
        # Identify the actual connected pond; latitude alone is not a water-body identity.
        self.acid = set()
        pending = deque([(14, 31)])  # A3 (14,15), in the pond's southern part.
        while pending:
            gx, gy = pending.popleft()
            if (gx, gy) in self.acid or not (0 <= gx < 96 and 0 <= gy < 64):
                continue
            cell = self.cell(gx, gy)
            if cell['surface'] not in [0, 8] or cell['scenery'] in [1, 7, 9, 10, 12]:
                continue
            self.acid.add((gx, gy))
            pending.extend([(gx-1, gy), (gx+1, gy), (gx, gy-1), (gx, gy+1)])

    def cell(self, gx, gy):
        n = 1 + (gx//16)*4 + (3-gy//16)
        d = self.maps[n]
        c = d['cells'][gy % 16][gx % 16]
        return dict(map=n, x=gx % 16, y=gy % 16, surface=d['surfaceTypes'][c['layers'][0]] & 15,
                    scenery=d['wallTypes'][c['layers'][1]])

    def describe(self, x, y):
        gx, gy = math.floor((x+24576)/1536), math.floor((y+24576)/1536)
        outside = not (0 <= gx < 96 and 0 <= gy < 64)
        # Past Xeen's world edge, continue water only where the original edge is water.
        # Otherwise continue the void; do not extrude a strip of invented mainland.
        cell = self.cell(min(95, max(0, gx)), min(63, max(0, gy)))
        surface, scenery = cell['surface'], cell['scenery']
        if outside:
            category = 3 if surface in [0, 8] and scenery not in [1, 7, 9, 10, 12] else 0
        elif surface == 15:
            category = 0
        elif scenery in [1, 7, 9, 10, 12]:
            category = {7: 6, 10: 8}.get(scenery, 10)
        elif surface in [0, 8]:
            category = 4 if (gx, gy) in self.acid else 3
        else:
            category = {1: 2, 2: 1, 3: 6, 4: 9, 5: 7, 6: 5, 7: 2, 11: 2, 14: 8}.get(surface)
            assert category is not None, ('Unexpected outdoor ground', cell)
        return dict(**cell, globalCell=[gx, gy], outsideSourceWorld=outside, classification=category)

    def __call__(self, x, y):
        return self.describe(x, y)['classification']
