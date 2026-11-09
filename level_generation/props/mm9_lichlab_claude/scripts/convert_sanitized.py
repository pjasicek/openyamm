"""convert_abc_model.py with non-finite face UVs replaced by 0 (FLAYINGBENCH.abc stores NaN UVs on a few faces).
Run with the isle venv's python from tools/mm9_import_discovery, same arguments as convert_abc_model.py."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools/mm9_import_discovery'))
import convert_abc_model as tool  # noqa: E402

_read = tool.read_abc
FIXED = []


def read_abc(path):
    model = _read(path)
    for piece in model.pieces:
        for lod in piece.lods:
            for face in lod.faces:
                for face_vertex in face.vertices:
                    if not all(math.isfinite(v) for v in face_vertex.uv):
                        face_vertex.uv = (0.0, 0.0)
                        FIXED.append(1)
    return model


tool.read_abc = read_abc
if __name__ == '__main__':
    status = tool.main()
    print("SANITIZED_UVS", len(FIXED), file=sys.stderr)
    sys.exit(status)
