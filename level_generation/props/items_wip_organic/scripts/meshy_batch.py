"""Run this worker's prepared Meshy meshes through prep or bake in an isolated Blender process."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    action = arguments[0]
    assert action in ('prep', 'bake')
    names = arguments[1:] or [n for n, d in texture.DESIGNS.items() if d['route'] == 'codex']
    for name in names:
        assert texture.DESIGNS[name]['route'] == 'codex'
        getattr(texture, action)(name)


if __name__ == '__main__':
    main()
