def summarize(report):
 rows=report['clips'];assert set(rows)=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'};fail=[]
 for role,a in rows.items():
  for side in 'LR':
   if a['elbow'][side]['flex'][0]<-5 or a['elbow'][side]['roll_max']>15:fail.append(role+' elbow '+side)
   if a['g4'][side]['p99_max']>2:fail.append(role+' G4 '+side)
   if a['g5'][side]>4.5:fail.append(role+' G5 '+side)
   if a['g6_mm'][side]>2:fail.append(role+' G6 '+side)
   if role in ['Standing','Fidget']and max(abs(x)for x in a['feet'][side]['lowest_m']+[a['feet'][side]['heel_max_m'],a['feet'][side]['toe_max_m']])>.01:fail.append(role+' sole '+side)
  if a.get('head_shoulder_mm',0)>10:fail.append(role+' head/shoulder')
  if a['cloth_mm']>2:fail.append(role+' cloth')
 return {'pass':not fail,'failures':fail,'g4_p99':max(x['p99_max']for a in rows.values()for x in a['g4'].values()),'g5':max(x for a in rows.values()for x in a['g5'].values()),'g6_mm':max(x for a in rows.values()for x in a['g6_mm'].values()),'cloth_mm':max(a['cloth_mm']for a in rows.values())}
