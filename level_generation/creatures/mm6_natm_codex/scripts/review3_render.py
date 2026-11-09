"""Runtime review and revision comparison under identical lights and cameras."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=(P/'scripts/review1_render.py').read_text().replace('round1','round3').replace('ROUND1','ROUND3')
source=source.replace("mm6_natm_b.glb');print","mm6_natm_a.glb');print")
source=source.replace('[(0,700),(1,550),(2,220),(3,88)]','[(0,700),(0,550),(0,220),(0,88),(1,550),(2,220),(3,88)]').replace("if level==0 else['natm_b']","if level==0 and size==700 else['natm_b']")
exec(compile(source,str(P/'scripts/review1_render.py'),'exec'))
sc,r,meshes=load(P/'review/viewer/mm6_natm_a.glb')
for frame in [0,21,34,42,44,45,60,84,108]:
 activate(r,'Attack',frame/48)
 common.render_views(str(folder/f'round3_attack_{frame:02}'),.90,4.0,views=('front','left','three_quarter'),resolution=(750,900),target=(0,-.60))
for revision in [1,2,3]:
 sc,r,meshes=load(P/f'review/round3_skin_models/round{revision}.glb');activate(r,'Standing',0)
 common.render_views(str(folder/f'round3_compare_r{revision}_body'),.86,1.90,views=('front',),resolution=(750,1000))
 common.render_views(str(folder/f'round3_compare_r{revision}_chest'),1.32,.95,views=('front','three_quarter'),resolution=(1000,850))
