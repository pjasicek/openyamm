from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
s=(P/'scripts/render_props.py').read_text().replace(" if name=='bow_nock':centre=tip"," if name!='bow_nock':continue\n if name=='bow_nock':centre=tip")
exec(compile(s,str(P/'scripts/render_props.py'),'exec'))
