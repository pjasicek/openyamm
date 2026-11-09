from pathlib import Path
P=Path(__file__).resolve().parents[1]
code=(P/'scripts/gate_equipment.py').read_text();exec(compile(code[:code.index('acts=[a.name')],str(P/'scripts/gate_equipment.py'),'exec'),{'__file__':str(P/'scripts/gate_equipment.py'),'__name__':'__main__'})
