"""tools/mm9_import_discovery/convert_abc_model.py with the ABC's non-finite texture coordinates repaired: DRAGONPHAROAH.abc
has 18 face corners (of 2916 in LOD0) whose UV is NaN, which the converter refuses. Each is replaced by the mean of
its face's finite corners (0, 0 if none). Run from the tool's directory with the converter's arguments
(convert_all.py does, for the props in props_table.FINITE_UV)."""
import dataclasses
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path.cwd()))
import convert_abc_model  # noqa: E402

_read_abc = convert_abc_model.read_abc


def read_abc(path):
    model = _read_abc(path)
    fixed = 0
    for piece in model.pieces:
        for lod in piece.lods:
            for face in lod.faces:
                uvs = [np.asarray(v.uv, float) for v in face.vertices]
                good = [uv for uv in uvs if np.all(np.isfinite(uv))]
                mean = tuple(np.mean(good, 0)) if good else (0.0, 0.0)
                for k, (vertex, uv) in enumerate(zip(face.vertices, uvs)):
                    if not np.all(np.isfinite(uv)):
                        replacement = type(vertex.uv)(mean) if isinstance(vertex.uv, (tuple, list)) else np.array(mean)
                        try:
                            vertex.uv = replacement
                        except dataclasses.FrozenInstanceError:
                            face.vertices[k] = dataclasses.replace(vertex, uv=replacement)
                        fixed += 1
    print('repaired non-finite UVs:', fixed, file=sys.stderr)
    return model


convert_abc_model.read_abc = read_abc
sys.argv[0] = 'convert_abc_model.py'
sys.exit(convert_abc_model.main())
