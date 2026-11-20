import textwrap
M='/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/'
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/Tables/'
O='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
def rd(p): return [l.split('\t') for l in open(p,encoding='latin-1').read().replace('\r','').split('\n')]
b=rd(B+'Class Starting Skills.txt'); m=rd(M+'Class Starting Skills.txt'); o=rd(O+'class_starting_skills.txt')
bs={r[0]:r for r in b[1:] if r and r[0]}; ms={r[0]:r for r in m[1:] if r and r[0]}
oh=o[0]; orow={r[0]:r for r in o[1:] if r and r[0]}
ren={'Leather':'LeatherArmor','Chain':'ChainArmor','Plate':'PlateArmor','Fire':'FireMagic','Air':'AirMagic','Water':'WaterMagic','Earth':'EarthMagic','Spirit':'SpiritMagic','Mind':'MindMagic','Body':'BodyMagic','Light':'LightMagic','Dark':'DarkMagic','Repair':'RepairItem'}
labels=[r[0] for r in o[1:] if r and r[0]]
print(labels)
# verify our rows == base columns
for k,lab in enumerate(labels):
    for sk in bs:
        osk=ren.get(sk,sk)
        oi=oh.index(osk)
        if orow[lab][oi].strip()!=bs[sk][k+1].strip(): print('OURS!=BASE',lab,sk,orow[lab][oi],bs[sk][k+1])
for k,lab in enumerate(labels):
    ch=[]
    for sk in ms:
        bv=bs[sk][k+1].strip(); mv=ms[sk][k+1].strip()
        if bv!=mv: ch.append('%s %s>%s'%(ren.get(sk,sk),bv,mv))
    if ch: print('| %s (k%d) | %s |'%(lab,k,', '.join(ch)))
for k,nm in ((26,'Seraphim'),(27,'Angel/Archangel (k27)'),(28,'DeathKnight'),(29,'Shaman'),(30,'Sekhem/Marabou (k30)'),(31,'Elementalist')):
    F=[ren.get(sk,sk) for sk in ms if ms[sk][k+1].strip()=='F']
    C=[ren.get(sk,sk) for sk in ms if ms[sk][k+1].strip()=='C']
    print('| %s | k%d | %s | %s |'%(nm,k,' '.join(F),' '.join(C)))
