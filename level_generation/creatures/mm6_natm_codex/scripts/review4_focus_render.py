from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/review4_costume_diagnostic.py'))
s=(P/'scripts/review1_render.py').read_text().split("sc,r,meshes=load(P/'review/viewer/mm6_natm_b.glb');")[0]
exec(compile(s,str(P/'scripts/review1_render.py'),'exec'))
for revision in [3,4]:
 sc,r,meshes=load(P/f'review/round4_skin_models/round{revision}.glb');activate(r,'Standing',0)
 common.render_views(str(folder/f'round4_compare_r{revision}_chest'),1.32,.95,views=('front','three_quarter'),resolution=(1000,850))
sc,r,meshes=load(P/'review/viewer/mm6_natm_a.glb');sc.render.film_transparent=True
for frame in [0,32,37,44]:
 activate(r,'Attack',frame/48)
 common.render_views(str(folder/f'round4_attack_{frame:02}'),.90,4.0,views=('front','left','three_quarter'),resolution=(750,900),target=(0,-.60))
