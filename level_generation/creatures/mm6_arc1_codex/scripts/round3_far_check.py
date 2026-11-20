import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
code=(P/'scripts/round2_assembled_metrics.py').read_text().replace('review/round2/reduction','review/round3/reduction/fitted').replace('for level in [1,2,3]','for level in [3]').replace("W/('unreduced.blend'if label=='high'else f'lod{level}.blend')","(P/'work/round3/unreduced.blend'if label=='high'else P/'work/round3/lod3_fitted.blend')")
exec(compile(code,str(P/'scripts/round2_assembled_metrics.py'),'exec'),{'__file__':str(P/'scripts/round2_assembled_metrics.py'),'__name__':'__main__'})
code=(P/'scripts/round3_lod_gates.py').read_text().replace('for level in [0,1,2,3]','for level in [3]').replace("P/f'work/round2/lod{level}.blend'","P/'work/round3/lod3_fitted.blend'").replace("out=P/f'review/round3/lod_gates/lod{level}'","out=P/'review/round3/far_candidate_gates'")
exec(compile(code,str(P/'scripts/round3_lod_gates.py'),'exec'),{'__file__':str(P/'scripts/round3_lod_gates.py'),'__name__':'__main__'})
