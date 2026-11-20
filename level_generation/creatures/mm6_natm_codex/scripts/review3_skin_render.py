from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=(P/'scripts/review1_render.py').read_text().split("sc,r,meshes=load(P/'review/viewer/mm6_natm_b.glb')")[0]
exec(compile(source,str(P/'scripts/review1_render.py'),'exec'))
for revision in [1,2,3]:
 sc,r,meshes=load(P/f'review/round3_skin_models/round{revision}.glb');activate(r,'Standing',0)
 common.render_views(str(folder/f'round3_compare_r{revision}_body'),.86,1.90,views=('front',),resolution=(750,1000))
 common.render_views(str(folder/f'round3_compare_r{revision}_chest'),1.32,.95,views=('front','three_quarter'),resolution=(1000,850))
