from pathlib import Path
p=Path(__file__).resolve().parents[1]/'inventory_remaining.py'
s=p.read_text()
old="if r['world']=='mm7':"
if old in s:
 s=s.replace(old,"if r['world'] in ('mm7','mm8'):")
 s=s.replace("candidates=set(sprite_indices['engine'])|set(sprite_indices['mm7'])","candidates=set(sprite_indices['engine'])|set(sprite_indices[r['world']])")
 s=s.replace('# Numbered MM7 actor names', '# Numbered MM7/MM8 actor names')
 p.write_text(s)
print('Inventory requires unused poses for both MM7 and MM8 art stems')
