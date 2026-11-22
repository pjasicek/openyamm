"""Scratch: native sizes (x4 / 4) of textures by name, from their .oytex headers."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import glob, struct, sys
for n in sys.argv[1:]:
    fs = glob.glob(f'{_REPO_ROOT}/assets_dev/worlds/*/textures_x4/{n}.oytex') + \
        glob.glob(f'{_REPO_ROOT}/assets_dev/engine/textures_x4/{n}.oytex')
    for f in fs[:1]:
        b = open(f, 'rb').read(64)
        w, h = struct.unpack_from('<Q', b, 0x28)[0], struct.unpack_from('<Q', b, 0x30)[0]
        print(n, w // 4, h // 4, f.split('/')[-3])
    if not fs:
        print(n, 'MISSING')
