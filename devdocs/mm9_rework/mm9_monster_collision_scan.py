"""MM9 monster collision scan (see MM9_MONSTER_COLLISION_RE.md): per MONSTERS.txt row, MM9's body (half extents of the
static_model animation, else animation 0, x the row's Scale, x 2.56) against our descriptor Height/Radius.
Run from the repository root: python3 devdocs/mm9_rework/mm9_monster_collision_scan.py > out.tsv"""
import csv, sys
from pathlib import Path
sys.path.insert(0, "tools/mm9_import_discovery")
import convert_abc_model as abc

LT = 2.56
MODELS = Path("mm9/extracted/MODELS/MODELS")
model_files = {p.name.lower(): p for p in MODELS.glob("*") if p.suffix.lower() == ".abc"}


def anim_dims(path):
    data = path.read_bytes()
    r = abc.BinaryReader(data)
    sec = abc.read_sections(r)
    r.seek(sec["Header"]); version = r.read_u32(); r.skip(8); node_count = r.read_u32()
    out = []
    r.seek(sec["Animation"]); n = r.read_u32()
    for _ in range(n):
        dims = r.read_vec3()
        name = r.read_string(); r.skip(4)
        if version >= 12: r.read_u32()
        kc = r.read_u32()
        for _ in range(kc): r.read_u32(); r.read_string()
        for _ in range(node_count):
            if version == 13: r.skip(4)
            for _ in range(kc):
                r.skip(12 + 16)
                if version == 13: r.skip(8)
        out.append((name, dims))
    binds = {}
    if "AnimBindings" in sec:
        r.seek(sec["AnimBindings"]); bc = r.read_u32()
        for _ in range(bc):
            b = abc.read_anim_binding(r); binds[b.name.lower()] = b.extents
    return out, binds


def initial(path):
    anims, binds = anim_dims(path)
    pick = next((a for a in anims if a[0].lower() == "static_model"), anims[0])
    name, d = pick
    db = binds.get(name.lower())
    allsame = len({tuple(round(v, 2) for v in (binds.get(a[0].lower()) or a[1])) for a in anims}) == 1
    return name, d, db, allsame


rows = list(csv.reader(open("mm9/extracted/DATA/DATA/MONSTERS.txt", errors="replace"), delimiter="\t"))
hdr = rows[0]; ci = {h: i for i, h in enumerate(hdr)}
desc = {}
for line in open("assets_dev/worlds/mm9/data_tables/monster_descriptors.txt"):
    f = line.rstrip("\n").split("\t")
    if f and f[0].isdigit():
        desc[int(f[0])] = f
w = csv.writer(sys.stdout, delimiter="\t")
w.writerow(["row", "name", "model", "scale", "anim", "animDims", "bindDims", "allAnimsSame",
            "mm9Radius", "mm9Height", "ourHeight", "ourRadius", "ourToHit"])
for r in rows[1:]:
    if not r or not r[0].strip().isdigit():
        continue
    n = int(r[0]); our = desc.get(9000 + n)
    model = r[ci["ModelName"]].strip()
    try:
        scale = float(r[ci["Scale"]] or 1)
    except ValueError:
        scale = 1.0
    p = model_files.get(model.lower())
    if p is None:
        w.writerow([n, r[1], model, scale, "MISSING"]); continue
    name, d, db, same = initial(p)
    use = db or d
    rad = max(use[0], use[2]) * scale * LT
    hgt = 2 * use[1] * scale * LT
    w.writerow([n, r[1], model, scale, name, "%.1f,%.1f,%.1f" % d,
                ("%.1f,%.1f,%.1f" % db) if db else "", int(same), round(rad), round(hgt),
                our[2] if our else "", our[3] if our else "", our[5] if our else ""])
