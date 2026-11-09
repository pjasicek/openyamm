"""Use the existing static-model LOD contract for this worker's sculptural hilts."""
import json
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parents[2]/'tools'))
from link_static_model_lods import link,read_glb,write_glb

ownership={r['icon'] for r in json.loads((PROJECT/'ownership.json').read_text())}
for source in sorted((PROJECT/'work/unlinked').glob('swords_*_export.glb')):
    icon=source.name.removeprefix('swords_').removesuffix('_export.glb')
    assert icon in ownership
    destination=PROJECT/'work/exports'/source.name
    if destination.exists() and destination.stat().st_mtime>=source.stat().st_mtime:continue
    document,binary=read_glb(source)
    print(icon,link(document))
    write_glb(destination,document,binary)
