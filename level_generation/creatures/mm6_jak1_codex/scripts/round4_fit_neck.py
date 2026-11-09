from pathlib import Path
p=Path(__file__).parent/'round4_fit_grips.py'
s=p.read_text().replace("[(0,'L'),(2,'L'),(3,'L'),(2,'R'),(3,'R')]","[(2,'L')]").replace("grip_fit.json","grip_neck_fit.json")
exec(compile(s,str(p),'exec'))
