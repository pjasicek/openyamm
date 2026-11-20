from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review1_render.py').read_text().split("sc,r,meshes=load(P/'review/viewer/mm6_natm_b.glb');")[0]
exec(compile(s,str(P/'scripts/review1_render.py'),'exec'))
sc,r,meshes=load(P/'review/viewer/mm6_natm_a.glb');sc.render.film_transparent=True
for frame in [0,21,42,44,45,60,84,108]:
 activate(r,'Attack',frame/48)
 common.render_views(str(folder/f'round3_attack_{frame:02}'),.90,4.0,views=('front','left','three_quarter'),resolution=(750,900),target=(0,-.60))
