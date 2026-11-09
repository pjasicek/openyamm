from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/check_full.py').read_text().replace("('Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead','Dying')","('Death','Dead','Dying')").replace("review/full_gates.json","review/death_gates.json")
exec(compile(s,str(P/'scripts/check_full.py'),'exec'))
