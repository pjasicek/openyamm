def P(L): return sum(5+l//10 for l in range(2,L+1))
def rank(points):
    r=1
    while (r+1)*(r+2)//2-1<=points: r+=1
    return r
for L in (10,25,40):
    p=P(L); print(L,p,'60%->',rank(0.6*p),'45%->',rank(0.45*p),'35%->',rank(0.35*p))
MM9S=0.033; OYS=2.13333/128
mm9={ # name: (base, avgPerRank, mana, rec)
 'EBolt E':(0,3.5,5,60),'EBolt M':(0,4.5,10,50),'EBolt G':(0,5.5,15,40),
 'Wound E':(10,4,10,90),'Wound M':(10,5,15,60),'Wound G':(10,6,20,30),
 'ColFire M':(30,3.5,30,90),'PoisCloud M':(25,5.5,20,90),'PoisCloud G':(25,5.5,25,60),
 'ChainL M':(0,4.5,20,90),'ChainL G':(0,4.5,20,60),'EBlast G':(0,5.5,20,70),
 'DeathTouch G':(7,4,None,120),'Souldr G':(25,4.5,55,90),'Sparks G(12)':(24,12,20,30),
}
oy={'FireBolt G':(0,2,2,90),'IceBolt G':(0,2.5,4,80),'Lightning E':(0,4.5,10,100),'Lightning M':(0,4.5,10,90),'Lightning G':(0,4.5,10,70),
 'Blades G':(0,5,8,80),'AcidBurst G':(9,5,10,80),'Fireball G':(0,3.5,8,80),'ToxicCloud G':(25,5.5,15,90),
 'Implosion G':(10,5.5,20,90),'PsyShock G':(12,6.5,25,100),'FlyFist G':(20,5.5,25,100),'Incinerate G':(15,8,30,90),
 'Sunray G':(20,10.5,50,135),'DragonBr G':(0,13,50,100),'MindBlast G':(3,2,4,110),'Harm G':(8,1.5,4,80),'LightBolt G':(0,2.5,5,80),
 'Souldr G':(25,4.5,60,300)}
for tbl,unit,label in ((mm9,MM9S,'MM9'),(oy,OYS,'OY')):
  for k,(b,a,m,rec) in tbl.items():
    out=[]
    for R in (6,7,10,12,15,17):
        d=b+a*R; out.append(f'R{R}:{d:.0f}/{d/(rec*unit):.0f}ps')
    print(label,k.ljust(13),f'rec {rec} = {rec*unit:.2f}s',' '.join(out))
