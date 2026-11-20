from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
s=(P/'scripts/render_final.py').read_text().split('# Neutral close turnarounds')[0]
s=s.replace("rows={}","rows=json.loads((P/'review/clips/frames.json').read_text())")
s=s.replace("['Standing','Walking','Cast','Attack','Hit','Death','Dead','Fidget']","['Attack']")
exec(compile(s,str(P/'scripts/render_final.py'),'exec'))
