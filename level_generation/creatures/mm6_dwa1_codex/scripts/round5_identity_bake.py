from pathlib import Path
P=Path(__file__).resolve().parents[1];path=P/'scripts/round5_project_bake.py';source=path.read_text().replace("step=config.get('step',6)","step=0");exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
