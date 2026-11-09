import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_wel_lods.glb'),str(E/'mm6_wel_shadow.glb')]
runpy.run_path(str(P.parent/'mm6_med_claude/scripts/shrink_shadow_lods.py'),run_name='__main__')
extras=[(prefix,key,value) for prefix in ['Water','Trident'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]]
rv.apply_variants(E/'mm6_wel_shadow.glb',E/'mm6_wel.glb',P/'textures/wel_ramps.json',extras)
rv.apply_variants(E/'mm6_wel_runtime_lod0.glb',E/'mm6_wel_portable.glb',P/'textures/wel_ramps.json',extras)
sys.argv=['split_attachment.py',str(E/'mm6_wel.glb'),'--joint','Trident','--body',str(E/'mm6_wel.glb'),'--attachment',str(E/'mm6_wel_trident.glb')]
runpy.run_path('tools/split_attachment.py',run_name='__main__')
sys.argv=['merge_head_material.py',str(E/'mm6_wel.glb'),str(E/'mm6_wel.glb')]
runpy.run_path('tools/merge_head_material.py',run_name='__main__')

# Preserve the three blade tips and small collars at distance; the rigid Poseidon attachment is 972 triangles.
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,compact
d,b=read_glb(E/'mm6_wel_trident.glb');d['meshes']=d['meshes'][:1];d['meshes'][0].pop('extras',None)
write_glb(E/'mm6_wel_trident.glb',*compact(d,b))
