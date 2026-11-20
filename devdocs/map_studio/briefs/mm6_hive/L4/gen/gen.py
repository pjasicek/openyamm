import sys;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from lib import *
L4=BASE+'devdocs/map_studio/briefs/mm6_hive/L4'
p=Proj()
R=lambda x0,y0,x1,y1:[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
CAVE={'step':160,'depth':40}
def ramp(name,sector,x0,y0,x1,y1,z0,z1,toward,prev,height=256,maxdrop=80,**kw):
    """A straight ramp in a rectangle, from z0 at the side away from `toward` to z1; cut into pieces so the flat ceiling follows."""
    k=max(1,math.ceil(abs(z1-z0)/maxdrop));last=prev
    for j in range(k):
        f0,f1=j/k,(j+1)/k
        if toward=='e': r=R(round(x0+(x1-x0)*f0),y0,round(x0+(x1-x0)*f1),y1)
        if toward=='w': r=R(round(x1-(x1-x0)*f1),y0,round(x1-(x1-x0)*f0),y1)
        if toward=='n': r=R(x0,round(y0+(y1-y0)*f0),x1,round(y0+(y1-y0)*f1))
        if toward=='s': r=R(x0,round(y1-(y1-y0)*f1),x1,round(y1-(y1-y0)*f0))
        za=round(z0+(z1-z0)*f0);zb=round(z0+(z1-z0)*f1)
        rid=name+('' if k==1 else '_'+'abcdefghij'[j])
        p.room(rid,sector,za,max(za,zb)+height,outline=r,slope={'to':zb,'toward':toward},**kw)
        if last and j>0: p.open(last,rid)
        elif last: p.open(last,rid,**FIRST.pop('o',{}))
        last=rid
    return last
FIRST={}
# ------------------------------------------------------------------ entrance
p.room('s76_entry',76,0,320,outline=R(160,3488,736,4064),name='Entry')
p.room('s1_lock',1,0,320,outline=[(256,4096),(640,4096),(640,4480),(896,4480),(896,5504),(0,5504),(0,4480),(256,4480)],name='Flush lock')
p.open('s76_entry','s1_lock',width=256,height=250)
p.room('s3_gallery',3,0,256,outline=R(192,5536,704,6565),name='Gallery')
p.open('s1_lock','s3_gallery',width=256,height=250)
p.room('s2_ledge',2,0,800,outline=[(192,6565),(704,6565),(832,6661),(1280,6784),(1894,7168),(-998,7168),(-384,6784),(64,6661)],name='Ledge over the great chamber')
p.open('s3_gallery','s2_ledge')
# ------------------------------------------------------------------ the great chamber
t23_end=[(2066,10092),(1966,10292)]
hall=[(-998,7168),(1894,7168),(2048,7552),(1824,8192),(2320,8192),(2495,8623),(2304,9104),(2304,9376),(2150,9460),
      (1290,10342),(640,10627),(256,10627),(-394,10342),(-1254,9460),
      (-1376,9312),(-1376,9120),(-1599,8623),(-1424,8192),(-928,8192),(-1152,7552)]
dome=[(448+rnd(900*math.cos(math.radians(a))),8623+rnd(900*math.sin(math.radians(a)))) for a in range(0,360,45)]
p.room('s4_hall',4,-768,1100,outline=hall,name='Great chamber',theme=p.theme('hvwl4a','hvflorb','hvwl4a'),bands=[{'height':768,'surface':p.surf('hvwl3a')}],
       platforms=[{'at':list(c),'size':list(sz),'rise':16,'top_surface':p.surf('orwtr64')} for c,sz in (((448,8093),(384,192)),((448,7485),(384,256)),((448,10371),(384,256)),((448,9808),(384,224)),((-624,9160),(320,256)),((1520,9320),(320,320)))],
       ceiling_levels=[{'outline':[list(q) for q in dome],'ceiling':1900,'notes':'Stands for the dome: the original ceiling slopes in four rings from z 0 at the walls to 2134 at the apex.'}],
       notes='The original is two sectors: the basin (S4, floor -768) and the dome over it (S2). Pits 5 to 8 are holes in this floor near the walls; here each is a room of its own in a notch of the outline.')
p.open('s2_ledge','s4_hall')
PITNOTE='A hole in the floor of the great chamber, close to the wall, in the original. Here it is a room of its own beside the chamber, open along one side: an opening cannot be cut in a floor.'
p.room('s6_pit',6,-1536,1100,outline=[(-1152,7552),(-928,8192),(-1424,8192),(-1440,7968),(-1440,7680)],name='South-west pit',notes=PITNOTE,bands=[{'height':768,'surface':p.surf('hvflori')},{'height':1536,'surface':p.surf('hvwl3a')}])
p.open('s4_hall','s6_pit')
p.room('s8_pit',8,-1536,1100,outline=[(2048,7552),(2368,7680),(2368,7968),(2320,8192),(1824,8192)],name='South-east pit',notes=PITNOTE,bands=[{'height':768,'surface':p.surf('hvwl5a')},{'height':1536,'surface':p.surf('hvwl3a')}])
p.open('s4_hall','s8_pit')
p.room('s5_pit',5,-1536,1100,outline=[(-1254,9460),(-394,10342),(-816,10272),(-1040,10272),(-1152,10096)],name='North-west pit',notes=PITNOTE,bands=[{'height':768,'surface':p.surf('hvflori')},{'height':1536,'surface':p.surf('hvwl3a')}])
p.open('s4_hall','s5_pit')
p.room('s7_pit',7,-1536,1100,outline=[(2150,9460)]+t23_end+[(1290,10342)],name='North-east pit',notes=PITNOTE,bands=[{'height':768,'surface':p.surf('hvflori')},{'height':1536,'surface':p.surf('hvwl3a')}])
p.open('s4_hall','s7_pit')
# ------------------------------------------------------------------ south-west loop: pit 6 round to the west door of the chamber
p.room('s6_low',6,-1536,-1280,outline=R(-1728,7680,-1440,7968),name='Under the south-west pit')
p.open('s6_pit','s6_low')
p.room('s71_a',71,-1536,-1274,outline=R(-1728,8000,-1472,8256))
p.open('s6_low','s71_a',width=224,height=250)
r71=ramp('s71_b',71,-2240,8000,-1728,8256,-1536,-1664,'w','s71_a')
p.room('s72_store',72,-1664,-1402,outline=R(-2752,8000,-2240,8512),name='Store')
p.open(r71,'s72_store')
T3=p.theme('hvwl3a','hvflorb','hvwl3a')
j47=p.jrect('s11_j47',11,(-1504,3872),(-1,0),144,112,-2038,-1782)
t=p.tunnel('s10',10,[(-1600,7680,-1536),(-1600,7232,-1536),(-1360,6432,-1536),(-704,5936,-1536),(-400,5856,-1536),(-80,5472,-1548),
                    (112,4976,-1587),(-208,4544,-1783),(-608,4256,-1933),(-1216,3872,-2038),(j47['in'][0],j47['in'][1],-2038)])
p.open('s6_low',t['first']);p.open(t['last'],'s11_j47')
p.room('s12_chest',12,-1820,-1520,outline=[(-3648,3640),(-2816,3640),(-2816,4240),(-3216,4240),(-3216,3936),(-3248,3936),(-3248,4240),(-3632,4240),(-3648,3936)],name='Chest alcoves',notes='The tunnel runs along the south side; two alcoves open north of it, a pier between them. The original floor climbs from -1867 at the east mouth to -1772 at the west mouth and in the alcoves.')
t=p.tunnel('s11',11,[(j47['out'][0],j47['out'][1],-2038),(-1776,3872,-2038),(-2624,3744,-1900),(-2816,3744,-1820)])
p.open('s11_j47',t['first']);p.open(t['last'],'s12_chest')
j49=p.jrect('s13_j49',13,(-5824,4408),(-1,0),128,112,-1711,-1455)
t=p.tunnel('s13',13,[(-3648,3840,-1820),(-3904,3840,-1820),(-5024,4064,-1716),(-5440,4408,-1711),(j49['in'][0],j49['in'][1],-1711)])
p.open('s12_chest',t['first']);p.open(t['last'],'s13_j49')
j73=p.jrect('s14_j73',14,(-3936,7104),(2,3),173,112,-1400,-1104)
t=p.tunnel('s14',14,[(-5840,4520,-1711),(-5840,4672,-1700),(-6032,5136,-1612),(-6032,5360,-1612),(-5600,6192,-1542),(-5056,6608,-1536),
                    (-4384,6800,-1450),(-4096,6864,-1400),(j73['in'][0],j73['in'][1],-1400)])
p.open('s13_j49',t['first']);p.open(t['last'],'s14_j73')
a,b=j73['side']('left',0,18)
p.room('s73_keg',73,-1360,-1100,outline=[(-4576,7104),(-4112,7104),a,b,(-4304,7264),(-4304,7376),(-4576,7376)],name='Keg room')
p.open('s14_j73','s73_keg')
t=p.tunnel('s15',15,[(j73['out'][0],j73['out'][1],-1400),(-3744,7392,-1400),(-4000,7712,-1275),(-4384,7936,-1229),(-4960,7904,-1214),
                    (-5632,8512,-1206),(-5600,9280,-1177),(-5120,9568,-1133),(-4000,9632,-1047),(-2624,9344,-911),(-1568,9216,-768),(-1408,9216,-768)])
p.open('s14_j73',t['first']);p.open(t['last'],'s4_hall',width=128,height=250)
# side rooms of the south-west loop
p.room('s47_passage',47,-2038,-1782,outline=R(-1568,3340,-1440,3760))
p.open('s11_j47','s47_passage')
p.room('s46_cell',46,-2038,-1650,outline=[(-1416,2124),(-1336,2188),(-1256,2220),(-1128,2780),(-1304,3308),(-1712,3308),(-2088,3148),(-2248,2732),(-2088,2348),(-1720,2188)],name='South cell')
p.open('s47_passage','s46_cell',width=96,height=250)
p.room('s49_passage',49,-1711,-1455,outline=R(-5904,3608,-5776,4296))
p.open('s13_j49','s49_passage')
p.room('s48_cell',48,-1711,-1330,outline=[(-5684,2473),(-5268,2473),(-5092,3033),(-5252,3417),(-5700,3576),(-6036,3576),(-6212,3033),(-6052,2617)],name='Flush control cell')
p.open('s49_passage','s48_cell',width=96,height=250)

# ------------------------------------------------------------------ north-west loop: pit 5 to the cave and back to the crossing
j74=p.jrect('s31_j74',31,(-4176,11056),(-1,0),160,112,-1565,-1284)
t=p.tunnel('s33',33,[(-928,10272,-1536),(-928,10656,-1536),(-1280,10720,-1560),(-1952,10784,-1795),(-2528,10816,-1753),(-3152,11008,-1666),
                    (-3888,11056,-1565),(j74['in'][0],j74['in'][1],-1565)])
p.open('s5_pit',t['first']);p.open(t['last'],'s31_j74')
p.room('s74_switch',74,-1560,-1284,outline=R(-4304,11168,-4048,11504),name='Flush switch closet')
p.open('s31_j74','s74_switch')
t=p.tunnel('s31',31,[(j74['out'][0],j74['out'][1],-1565),(-4464,11056,-1565),(-4768,11168,-1495),(-5904,11264,-1437),(-6464,11728,-1434),(-6464,12800,-1400)])
p.open('s31_j74',t['first']);t31=t
t30=p.tunnel('s30',30,[(-5728,13712,-1400),(-5600,13776,-1400),(-4576,14448,-1201),(-3936,14432,-1201),(-3488,14144,-1069),(-3040,14016,-984),
                      (-2720,13824,-954),(-2208,13776,-921),(-1984,13600,-906),(-416,13440,-893),(288,13440,-768)])
cave34=t31['m1'][::-1]  # placeholder, replaced below
cave34=[(-6576,12800),(-6352,12800),(-5862,13000),(-5750,13208),(-5958,13432)]+t30['m0']+[(-6150,13512),(-6566,13608),(-6518,13896),(-6582,14136),
        (-6742,14328),(-6742,14504),(-6982,14504),(-6982,14408),(-7206,14344),(-7382,14136),(-7430,13816),(-7286,13416),(-7430,13192),(-7334,13016),(-7190,12936)]
p.room('s34_cave',34,-1400,-1120,outline=cave34,name='North-west cave',rough=CAVE)
p.open(t31['last'],'s34_cave');p.open('s34_cave',t30['first'])
# ------------------------------------------------------------------ the crossing north of the great chamber and the stepped corridor
p.room('s39_corridor',39,-768,-512,outline=R(320,10627,576,13604),name='North corridor and crossing')
p.open('s4_hall','s39_corridor')
p.open(t30['last'],'s39_corridor',width=192,height=250)
FIRST['o']=dict(width=224,height=250);r40=ramp('s40_a',40,320,13636,576,14372,-768,-896,'n','s39_corridor')
p.room('s40_b',40,-896,-640,outline=R(320,14372,576,14628))
p.open(r40,'s40_b')
r41=ramp('s41_a',41,-960,14372,320,14628,-896,-1152,'w','s40_b')
p.room('s41_b',41,-1152,-896,outline=R(-1216,14372,-960,14628))
p.open(r41,'s41_b')
r42=ramp('s42_a',42,-1216,14628,-960,15140,-1152,-1280,'n','s41_b')
p.room('s42_b',42,-1280,-1024,outline=R(-1216,15140,-960,15396))
p.open(r42,'s42_b')
r43=ramp('s43_a',43,-1856,15140,-1216,15396,-1280,-1408,'w','s42_b')
p.room('s43_b',43,-1408,-1152,outline=R(-2112,15140,-1856,15396))
p.open(r43,'s43_b')
r44=ramp('s44_ramp',44,-2112,15396,-1856,16264,-1408,-1536,'n','s43_b')
# ------------------------------------------------------------------ north halls
p.room('s38_west_hall',38,-1536,-880,theme=p.theme('hvceilb','hvflori','hvceilb'),bands=[{'height':256,'surface':p.surf('hvwl5a')}],outline=[(-2368,16296),(-1664,16296),(-1664,17857),(-2368,18169),(-3104,17856),(-3264,17856),(-3264,17712),(-3420,17067),(-3055,16351)],name='West hall')
p.open(r44,'s38_west_hall',width=224,height=250)
p.room('s35_w',35,-1536,-800,theme=p.theme('hvceilb','hvflori','hvceilb'),bands=[{'height':256,'surface':p.surf('hvwl5a')}],platforms=[{'outline':[[-322,16779],[-834,17792],[-834,15790]],'rise':8,'top_surface':p.surf('orwtr64')}],ceiling_levels=[{'outline':[[-1600,16330],[-1300,16120],[340,16120],[340,17440],[-1600,17440]],'ceiling':-500,'notes':'Stands for the barrel vault: its crown runs east to west at z -436 and it comes down to -1024 at the north and south walls.'}],outline=[(-1664,16296),(-888,15724),(384,15620),(384,17998),(-888,17835),(-1664,17857)],name='Great north hall, west half',walls=[{'wall':2,'surface':p.surf('hvwl6')}])
p.open('s38_west_hall','s35_w')
p.room('s35_e',35,-1536,-800,theme=p.theme('hvceilb','hvflori','hvceilb'),bands=[{'height':256,'surface':p.surf('hvwl5a')}],platforms=[{'outline':[[2242,16779],[1730,17770],[1730,15660]],'rise':8,'top_surface':p.surf('orwtr64')}],ceiling_levels=[{'outline':[[490,16120],[2380,16120],[2380,17440],[490,17440]],'ceiling':-500}],outline=[(448,15620),(1730,15620),(2432,16043),(2432,17553),(1784,17835),(448,17998)],name='Great north hall, east half',walls=[{'wall':5,'surface':p.surf('hvwl6')}])
p.open('s35_e','s35_w',width=128,height=250,along=0.056,notes='The doorway at the north end of the wall that divides the hall.')
p.room('s37_east_hall',37,-1536,-700,theme=p.theme('hvceilb','hvflori','hvceilb'),bands=[{'height':256,'surface':p.surf('hvwl5a')}],outline=[(2432,16043),(3120,15660),(3863,15983),(4172,16763),(3968,17408),(3968,17552),(3120,17865),(2432,17553)],name='East hall')
p.open('s35_e','s37_east_hall')
p.room('s36_vestibule',36,-1536,-1100,outline=[(1184,15124),(1456,15124),(1744,15588),(448,15588)],name='Vestibule under the north hall')
p.open('s36_vestibule','s35_e',width=256,height=250)
p.room('s62_passage',62,-1536,-1280,outline=[(-4480,17718),(-3296,17718),(-3296,17846),(-4096,17846),(-4096,18619),(-4480,18619)])
p.open('s38_west_hall','s62_passage',width=96,height=250)
p.room('s63_closet',63,-1536,-1280,outline=R(-4096,17969,-3840,18619),name='Switch closet')
p.open('s62_passage','s63_closet')
# the deep tunnel from the shaft under the great chamber to the vestibule
p.room('s9_shaft',9,-2304,-768,outline=R(288,8760,784,9160),name='Shaft under the great chamber',
       notes='In the original this shaft opens through the floor of the great chamber (a hatch, door 43). A floor opening onto a room below cannot be drawn: the shaft is reached only from the deep tunnel.')
t=p.tunnel('s70',70,[(608,9160,-2304),(608,9440,-2304),(832,10656,-2283),(1184,11744,-2187),(1344,13104,-1940),(1320,14800,-1600),(1320,15124,-1536)],width=256)
p.open('s9_shaft',t['first']);p.open(t['last'],'s36_vestibule')
# ------------------------------------------------------------------ north-east loop: the crossing to pit 7, with the cell blocks
j75=p.jrect('s19_j75',19,(4944,14352),(1,0),160,112,-1082,-826)
t=p.tunnel('s19',19,[(608,13440,-768),(832,13440,-768),(1616,13408,-768),(2016,13536,-768),(2592,13632,-771),(2944,13616,-793),(4384,14112,-1029),(4592,14352,-1082,96),(j75['in'][0],j75['in'][1],-1082)])
p.open('s39_corridor',t['first'],width=192,height=250);p.open(t['last'],'s19_j75')
p.room('s75_chest',75,-1082,-830,outline=[(4816,14464),(5072,14464),(5072,14720),(5584,14720),(5584,14976),(4816,14976)],name='Chest room off the north-east tunnel')
p.open('s19_j75','s75_chest')
j22=p.jrect('s22_cross',22,(5696,11456),(-1,0),128,128,-1530,-1274)
t=p.tunnel('s20',20,[(j75['out'][0],j75['out'][1],-1082),(5232,14352,-1100),(6272,13952,-1353),(6880,13712,-1429),(8496,13968,-1472),(9104,13744,-1484),(9456,12912,-1495),
                    (9392,12464,-1512),(9008,11920,-1533),(8144,11536,-1545),(6992,11376,-1540),(5952,11456,-1530),(j22['in'][0],j22['in'][1],-1530)])
p.open('s19_j75',t['first']);p.open(t['last'],'s22_cross')
t=p.tunnel('s23',23,[(j22['out'][0],j22['out'][1],-1530),(5376,11456,-1530),(4416,11520,-1532),(3712,11424,-1532),(3072,11136,-1532),(2144,10256,-1536),(2016,10192,-1536)])
p.open('s22_cross',t['first']);p.open(t['last'],'s7_pit')
assert t['m1']==t23_end,t['m1']
CELL=dict(floor=-1530,ceiling=-1274)
p.room('s56_cells_n',56,outline=R(5568,11584,5824,13056),name='North cell passage',**CELL);p.open('s22_cross','s56_cells_n')
p.room('s61_cells_s',61,outline=R(5568,9856,5824,11328),name='South cell passage',**CELL);p.open('s22_cross','s61_cells_s')
p.room('s52_cell',52,outline=R(5056,12032,5440,13056),**CELL);p.room('s52_door',52,outline=R(5440,12800,5568,13056),**CELL);p.open('s56_cells_n','s52_door');p.open('s52_door','s52_cell')
p.room('s53_cell',53,outline=[(4480,11840),(5568,11840),(5568,11968),(4992,11968),(4992,12800),(4480,12800)],**CELL);p.open('s56_cells_n','s53_cell')
p.room('s54_cell',54,outline=R(5952,12032,6336,13056),**CELL);p.room('s54_door',54,outline=R(5824,12800,5952,13056),**CELL);p.open('s56_cells_n','s54_door');p.open('s54_door','s54_cell')
p.room('s55_cell',55,outline=[(5824,11840),(6912,11840),(6912,12800),(6400,12800),(6400,11968),(5824,11968)],
       platforms=[{'at':[6656,12192],'size':[256,448],'rise':112,'surface':p.surf('hvflord')}],**CELL);p.open('s56_cells_n','s55_cell')
p.room('s57_cell',57,outline=R(4928,9856,5440,10880),platforms=[{'at':[5184,10336],'size':[256,448],'rise':112,'surface':p.surf('hvflord')}],**CELL);p.room('s57_door',57,outline=R(5440,9856,5568,10112),**CELL);p.open('s61_cells_s','s57_door');p.open('s57_door','s57_cell')
p.room('s58_cell',58,outline=[(4352,10112),(4864,10112),(4864,10944),(5568,10944),(5568,11072),(4352,11072)],**CELL);p.open('s61_cells_s','s58_cell')
p.room('s59_cell',59,outline=R(5952,9856,6336,10880),**CELL);p.room('s59_door',59,outline=R(5824,9856,5952,10112),**CELL);p.open('s61_cells_s','s59_door');p.open('s59_door','s59_cell')
p.room('s60_cell',60,outline=[(6400,10112),(6912,10112),(6912,11072),(5824,11072),(5824,10944),(6400,10944)],**CELL);p.open('s61_cells_s','s60_cell')
# ------------------------------------------------------------------ east loop: the raised mouth in the great chamber round to pit 8
j51=p.jrect('s26_j51',26,(7792,5760),(-1,0),128,112,-1335,-1079)
t=p.tunnel('s24',24,[(2304,9232,-576),(2560,9232,-576),(4352,9152,-817),(5120,8368,-897),(5696,8096,-897),(7520,8128,-888),(8128,8160,-892),(9008,8160,-985),
                    (9280,8016,-1040),(9504,7600,-1096),(9632,6976,-1149),(9552,6384,-1188),(9376,5968,-1233),(8960,5760,-1272),(j51['in'][0],j51['in'][1],-1335)])
p.open('s4_hall',t['first']);p.open(t['last'],'s26_j51')
j45=p.jrect('s27_j45',27,(5824,5760),(-1,0),128,112,-1505,-1249)
t=p.tunnel('s27',27,[(j51['out'][0],j51['out'][1],-1335),(j45['in'][0],j45['in'][1],-1505)])
p.open('s26_j51',t['first']);p.open(t['last'],'s27_j45')
t=p.tunnel('s27w',27,[(j45['out'][0],j45['out'][1],-1505),(5488,5760,-1569)])
p.open('s27_j45',t['first'])
p.room('s28_cave',28,-1569,-1279,outline=[(5392,5628),(5488,5628),(5488,5884),(4944,5980),(4480,6204),(4480,6700),(4304,7260),(3760,7916),(2368,7968),(2368,7680),
       (3024,7612),(3696,7612),(3904,7292),(3808,6652),(4080,5964),(4768,5660)],name='South-east cave',rough=CAVE)
p.open(t['last'],'s28_cave');p.open('s28_cave','s8_pit')
p.room('s51_passage',51,-1335,-1079,outline=R(7728,5872,7856,6688));p.open('s26_j51','s51_passage')
p.room('s50_cell',50,-1335,-890,outline=[(7664,6720),(7920,6720),(8624,6768),(8928,6896),(9056,7088),(8928,7280),(8592,7440),(8592,7632),(8448,7632),(8432,7440),
       (7680,7408),(7376,7280),(7264,7072),(7376,6896)],name='East cell (hatch switch)')
p.open('s51_passage','s50_cell',width=96,height=250)
p.room('s45_passage',45,-1505,-1249,outline=R(5760,5872,5888,6128));p.open('s27_j45','s45_passage')
p.room('s45_cell',45,-1505,-1160,outline=[(5616,6160),(6032,6160),(6400,6320),(6560,6704),(6400,7120),(6032,7296),(5616,7120),(5440,6752)],name='Locked cell',platforms=[{'at':[6000,6818],'size':[448,256],'rise':112,'surface':{'texture':'hvtrim1','size':[32,32]}}])
p.open('s45_passage','s45_cell',width=96,height=250)
# the stair and the stepped corridor from the south-east cave up to the gallery
p.room('s66_landing',66,-1569,-1313,outline=R(4512,6424,5280,6680));p.open('s28_cave','s66_landing',width=224,height=250)
p.room('s66_stairs',66,-1569,-900,outline=R(5024,6680,5280,7190),slope={'to':-1156,'toward':'n','steps':11});p.open('s66_landing','s66_stairs')
p.room('s67_a',67,-1156,-900,outline=R(5024,7190,5280,7446));p.open('s66_stairs','s67_a')
r67=ramp('s67_ramp',67,3231,7190,5024,7446,-1156,-640,'w','s67_a')
p.room('s68_a',68,-640,-384,outline=R(2975,7190,3231,7446));p.open(r67,'s68_a')
r68=ramp('s68_ramp',68,2975,6422,3231,7190,-640,-512,'s','s68_a')
p.room('s69_a',69,-512,-256,outline=R(2975,6166,3231,6422));p.open(r68,'s69_a')
r69=ramp('s69_ramp',69,737,6166,2975,6422,-512,0,'w','s69_a')
p.open(r69,'s3_gallery',width=224,height=250)
# ------------------------------------------------------------------ the way to the reactor
p.room('s64_passage',64,-1536,-1280,outline=R(4000,17414,4832,17542));p.open('s37_east_hall','s64_passage',width=96,height=250)
p.room('s65_upper',65,-1536,-1280,outline=R(4832,17414,5184,17990),name='Guard room, upper floor');p.open('s64_passage','s65_upper')
FIRST['o']=dict(width=224,height=250);r651=ramp('s65_ramp1',65,5216,17414,5824,17670,-1536,-1712,'e','s65_upper')
p.room('s65_landing',65,-1712,-1456,outline=R(5824,17414,6080,17990));p.open(r651,'s65_landing')
r652=ramp('s65_ramp2',65,5184,17734,5824,17990,-1712,-1950,'w','s65_landing')
p.room('s65_ramp3',65,-1950,-1560,outline=R(4832,17734,5184,17990),slope={'to':-2080,'toward':'w'},notes='Runs under the upper floor of the guard room.');p.open(r652,'s65_ramp3')
p.room('s65_low',65,-2080,-1824,outline=R(4576,17734,4832,17990));p.open('s65_ramp3','s65_low')
p.room('s65_west',65,-2080,-1824,outline=R(4288,17734,4544,18502));p.open('s65_low','s65_west',width=224,height=250)
p.room('s80_antechamber',80,-2080,-1700,theme=p.theme('hvwl6','hvflorb','hvdore'),outline=R(3776,18502,5056,19014),name='Reactor antechamber');p.open('s65_west','s80_antechamber')
p.room('s80_steps',80,-2080,-1750,theme=p.theme('hvwl6','swr1','hvdore'),outline=R(3776,19014,5056,19718),slope={'to':-2256,'toward':'n','steps':11});p.open('s80_antechamber','s80_steps')
dais=[(4407+rnd(450*math.cos(math.radians(a))),22466+rnd(450*math.sin(math.radians(a)))) for a in range(15,360,30)]
p.room('s79_reactor',79,-2256,-720,outline=[(3264,19718),(5568,19718),(7104,22406),(5568,25222),(3264,25222),(1984,22406)],name='Reactor chamber',
       platforms=[{'outline':[list(q) for q in dais],'rise':128,'surface':{'texture':'swfloor2b','size':[128,128]}}],
       notes='Inside the hexagonal ring wall (door 53 of the original, which sinks into the floor).')
p.open('s80_steps','s79_reactor')
p.room('s79_ring_w',79,-2256,-850,outline=[(2752,18816),(3648,18816),(3648,19590),(3264,19590),(1856,22406),(3264,25350),(2752,26246),(1216,22432)],name='Outer ring, west')
p.room('s79_ring_e',79,-2256,-850,outline=[(5184,18816),(6096,18816),(8016,22400),(6144,26118),(5568,25350),(7232,22406),(5568,19590),(5184,19590)],name='Outer ring, east')
p.room('s79_ring_n',79,-2256,-976,outline=[(3264,25350),(5568,25350),(6144,26118),(5568,26118),(5568,26502),(5056,26502),(5056,26118),(3776,26118),(3776,26374),(2752,26374),(2752,26246)],name='Outer ring, north',
       notes='North of y 26118 the original has a shelf 832 above the floor between the two bays; it is left out as solid.')
p.open('s79_ring_w','s79_ring_n');p.open('s79_ring_e','s79_ring_n')
p.open('s79_reactor','s79_ring_n',width=2240,height=1100,notes='The three gates of the ring wall (doors 51 and 52: blocks that rise from the floor and sink from above), drawn as one gate.')
p.room('s77_queen',77,-2256,-976,outline=[(2752,26502),(4544,26502),(4544,27136),(5056,27136),(5056,27392),(2752,27392)],name="Queen's chamber and exit")
p.open('s79_ring_n','s77_queen',width=960,height=1100)
p.write(L4)

# =================================================================== objects and wiring
import yaml as _y
ORIG=json.load(open(BASE+'output/studio_cal/mm6_hive/orig.json'))['map']
SCN=_y.safe_load(open(BASE+'assets_dev/worlds/mm6/maps/hive.scene.yml'))
doors=[];events=[];switches=[];chests=[];spawns=[];lights=[];decos=[];placeholders=[];exits=[]
def oid(a,b): return f"open:{a}__{b}"
def door(n,a,b,tex,title='Door',kind='slide_up',event=True,notes=None,speed=85,**ev):
    d={'id':f'door:d{n}','opening':oid(a,b),'kind':kind,'state':'closed','speed':speed,'thickness':32,'surface':dict(p.surf(tex),fit=True) if 'dor' in tex else p.surf(tex)}
    if notes: d['notes']=notes
    doors.append(d)
    if event:
        e={'id':f'evt:door{n}','preset':'door','source':f'door:d{n}','title':title,'action':'open'};e.update(ev);events.append(e)
def last(prefix):
    return [r['id'][5:] for r in p.rooms if r['id'].startswith('room:'+prefix)][-1]
def first(prefix):
    return [r['id'][5:] for r in p.rooms if r['id'].startswith('room:'+prefix)][0]
door(1,'s76_entry','s1_lock','hvdord')
door(45,'s1_lock','s3_gallery','hvdord',notes='The original is a pair of leaves (doors 45 and 46) that part sideways, each 250 into the wall; a leaf here can only slide up or down or swing.')
door(4,r69,'s3_gallery','hvdorc',condition={'map_var':'stair_way'},notes='In the original this door has a handler only on its corridor side (event 4): it cannot be opened from the gallery. A door event cannot be given to one side, so it waits for the stair door (d42), which is on the only other way to the corridor.')
door(5,last('s15_'),'s4_hall','hvdorf',notes="Original: opens from the tunnel side (event 5); from the chamber it says The Door Won't Budge (event 21). Both sides open it here: the tunnel behind is reached from the south-west pit in the same step.")
door(10,last('s30_'),'s39_corridor','hvdorc',notes='Original: opens only from the tunnel side (event 10).')
door(12,'s39_corridor','s19_s0','hvdord',notes='Original: opens only from the tunnel side (event 12).')
door(11,'s39_corridor','s40_a_a','hvdore',condition={'map_var':'north_way'},locked_text="The Door Won't Budge",
     notes="Original: opens from its north side (event 11); from the crossing it says The Door Won't Budge (event 21). One-sided doors cannot be said, so it waits for door 9, which stands on the only way to its north side.")
door(2,'s47_passage','s46_cell','hvdorf');door(3,'s49_passage','s48_cell','hvdorf');door(7,'s51_passage','s50_cell','hvdorf')
door(13,'s6_low','s71_a','hvdord')
door(9,r44,'s38_west_hall','hvdord',effects=[{'set':{'var':{'map_var':'north_way'},'value':1}}])
door(14,'s36_vestibule','s35_e','hvdore')
door(6,'s37_east_hall','s64_passage','hvdorg',condition={'item':'reactor_way_key','consume':True},locked_text='The door is locked')
door(32,'s38_west_hall','s62_passage','hvdorf',event=False,notes='Opened by the switch in the south cell (event 31); it has no handler of its own.')
door(36,'s45_passage','s45_cell','hvdorf',event=False,notes="Toggled by the switch in the closet off the west hall (event 33). From the passage it says The Door Won't Budge (event 21).")
events.append({'id':'evt:door36','preset':'text','source':'door:d36','title':'Door','text':"The Door Won't Budge"})
door(42,'s28_cave','s66_landing','hvdorc',effects=[{'set':{'var':{'map_var':'stair_way'},'value':1}}])
door(8,'s65_upper','s65_ramp1_a','hvwl5a',notes='The original leaf shows the wall texture (hvwl5a) toward the guard room and hvdore toward the ramp; a leaf here has one surface.')
door(28,'s65_low','s65_west','hvdorc')
GATE="The original opens this on entering the map once quest bit 1204 is set (event 100, run by the map); wiring events need an object the player uses, so the gate itself is the object."
door(51,'s79_reactor','s79_ring_n','hvwl6',kind='slide_down',title='Gate',condition={'qbit':'reactor_destroyed'},speed=500,notes=GATE+' Doors 51 and 52 of the original are the lower and upper halves of three gates in the north side of the ring wall; they start shut (state 2).')
door(30,'s79_ring_n','s77_queen','hvwl6',kind='slide_down',title='Gate',condition={'qbit':'reactor_destroyed'},speed=500,notes=GATE+' Door 30: a block 1008 wide and 1279 high that sinks into the floor.')
# switches
def switch(n,room,x,y,z,off,on=None,**ev):
    w,al=p.wall_at(room,x,y);m=p.meta['room:'+room]
    sw={'id':f'switch:s{n}','room':'room:'+room,'wall':w,'along':al,'height':max(48,z-m['zmin']),'size':[32,32],'off':dict(p.surf(off))}
    if on: sw['on']=on
    switches.append(sw)
    e={'id':f'evt:switch{n}','source':f'switch:s{n}','title':'Switch'};e.update(ev);events.append(e)
switch(16,'s48_cell',-5496,2473,-1558,'hvtrim4',preset='switch',lua='evt.MoveToMap(468, 3690, 1, 45, 0, 0, 0, 0)',text='Flush system deactivated',
       effects=[{'set':{'var':{'map_var':'flush_armed'},'value':0}}],notes='Event 16: also moves the button (door 16).')
switch(31,'s46_cell',-1548,2180,-1958,'hvtrim4',preset='switch',opens=['door:d32'],once=True)
switch(33,'s63_closet',-3840,18294,-1408,'hvwl5',preset='switch',toggles=['door:d36'])
switch(36,'s50_cell',8301,7440,-1191,'hvtrim4',preset='switch',lua='evt.MoveToMap(536, 8960, -2300, 512, 0, 0, 0, 0)',
       notes='Event 36 of the original toggles the hatch (door 43) over the shaft in the middle of the great chamber; the party then walks back and drops through it. A hatch in a floor cannot be built, so the switch carries the party to the foot of the shaft itself.')
switch(50,'s74_switch',-4152,11504,-1428,'hvflorh',preset='switch',sets={'map_var':'flush_off'},once=True,notes='Event 50: the flush system is switched off for good (map variable 23). A floor button in the original.')
switch(34,'s65_upper',4832,17862,-1408,'hvwl4',preset='text',text='Nothing happens.',
       notes='Event 34 of the original slides a floor panel (door 38) in and out between the upper floor and the passage below; a moving floor that is not a lift cannot be built.')
# chests
CH={1:(4608,10144,-1530,'s58_cell'),2:(5533,14848,-1082,'s75_chest'),3:(8519,7577,-1335,'s50_cell'),4:(-2859,4182,-1820,'s12_chest'),5:(-6888,14444,-1400,'s34_cave')}
for n,(x,y,z,room) in CH.items():
    chests.append({'id':f'chest:c{n}','room':'room:'+room,'at':[x,y],'treasure_level':6,'random_items':2})
    events.append({'id':f'evt:chest{n}','preset':'chest','source':f'chest:c{n}','title':'Chest'})
# spawns and lights at the original's places
for i,sp in enumerate(SCN['spawns']):
    x,y,z=sp['position']['x'],sp['position']['y'],sp['position']['z'];idx=sp['index']
    slot=idx if idx<=3 else (idx-4)//3+1
    e={'id':f'spawn:m{i:02d}','room':p.room_at(x,y,z),'at':[x,y],'slot':slot,'radius':sp['radius']}
    if idx>3: e['notes']=f'Original spawn index {idx}: a fixed rank of slot {slot}, which a spawn here cannot say.'
    spawns.append(e)
for i,li in enumerate(ORIG['lights']):
    x,y,z=li['position'];room=p.room_at(x,y,z);m=p.meta[room]
    lights.append({'id':f'light:l{i:02d}','room':room,'at':[x,y],'height':max(16,min(z-m['zmin'],m['ceiling']-m['zmin']-16)),'radius':li['radius'],'brightness':li['brightness']})
decos.append({'id':'deco:skull_pile','room':'room:s1_lock','decoration':'sklplrev','at':[76,5408]})
decos.append({'id':'deco:keg','room':'room:s73_keg','decoration':'smlbarel','at':[-4528,7312],'notes':'Event 23 of the original: drinking gives 20 hit points. A wiring event cannot have a decoration as its source.'})
placeholders+= [
 {'id':'ph:reactor','room':'room:s79_reactor','stands_for':'Fixed actor: the Hive reactor (monster id 647), 1300 hit points, group 85, standing on the dais.','at':[4416,22464],'size':[120,120,300]},
 {'id':'ph:queen','room':'room:s77_queen','stands_for':'Fixed actor: the Demon Queen (monster id 646), 1300 hit points, group 85.','at':[3328,26880],'size':[120,120,300]},
 {'id':'ph:floor_item','room':'room:s1_lock','stands_for':'An item lying on the floor (object 337, item 1817).','at':[128,5248],'size':[32,32,32]},
 {'id':'ph:hatch','room':'room:s4_hall','stands_for':'A hatch in the floor over the shaft (door 43: a cover 480 by 400 that slides east), opened by the switch in the east cell.','at':[536,8960],'size':[496,400,32],
  'notes':'The shaft below is room:s9_shaft. An opening in a floor onto a room below cannot be drawn.'},
 {'id':'ph:ring_wall','room':'room:s79_reactor','stands_for':'The hexagonal ring wall round the reactor floor (door 53), 128 thick and 1279 high, which sinks into the floor once the reactor is destroyed.','at':[4416,22470],'size':[5120,5504,1279],
  'notes':'Built as fixed wall between the reactor chamber and the two halves of the outer ring.'},
 {'id':'ph:bridge','room':'room:s65_low','stands_for':'A floor panel at the height of the upper floor (door 38) that slides east out of the way.','at':[4704,17862],'size':[256,256,32]},
]
exits.append({'id':'exit:south','room':'room:s76_entry','wall':'south','size':[192,256],'surface':dict(p.surf('hvdord'),fit=True),'to':'exit:sweet_water'})
exits.append({'id':'exit:final','room':'room:s77_queen','wall':'east','size':[128,200],'surface':dict(p.surf('hvdorf'),fit=True),'to':'exit:new_sorpigal'})
events.append({'id':'evt:exit_south','preset':'exit','source':'exit:south','title':'Exit'})
events.append({'id':'evt:exit_final','preset':'exit','source':'exit:final','title':'Exit','condition':{'qbit':'exit_unlocked'},'locked_text':'The door is locked'})
obj={'format':0,'start':{'room':'room:s76_entry','at':[384,3712],'facing':'n'},'doors':doors,'switches':switches,'chests':chests,'spawns':spawns,'lights':lights,
     'decorations':decos,'placeholders':placeholders,'exits':exits,
     'notes':'Doors, spawns, lights and chests stand at the places of the original. Placeholders hold what cannot be said: the two fixed actors, the floor item, the hatch, the ring wall, the sliding floor panel.'}
_y.safe_dump(obj,open(L4+'/objects.yml','w'),default_flow_style=None,sort_keys=False,width=100000)
wir={'format':0,'variables':['flush_armed','flush_off','north_way','stair_way'],'events':events,
     'notes':"Not wired, for want of a way to say it: the flush system (events 17, 19, 22, 29, 51, 54, 56, 57, 58: 182 floor faces that run a handler when walked on, the water pads that protect from the flush damage, and the timed sequence), the keg (event 23, on a decoration), event 27 (a floor face in the stepped corridor that shuts the hatch), event 100 (run on entering the map). Events 30 and 62 have faces but no handler in the original."}
_y.safe_dump(wir,open(L4+'/wiring.yml','w'),default_flow_style=None,sort_keys=False,width=100000)
proj={'format':0,'id':'mm6hive','name':'The Hive','world':'mm6','kind':'indoor','profile':'dungeon',
 'map_stats':{'id':9714,'reference':'hive.blv'},
 'neighbours':[{'id':'exit:sweet_water','to':'outa1.odm','kind':'door','arrival':[-14355,15010,3841],'direction':247.5},
               {'id':'exit:new_sorpigal','to':'oute3.odm','kind':'door','arrival':[0,0,0],'direction':0,'notes':'The arrival is the original event 60: 0, 0, 0 on New Sorpigal.'}],
 'qbits':{'reactor_destroyed':1204,'exit_unlocked':1226},'items':{'reactor_way_key':2190},
 'notes':'Rebuild of the Hive (MM6, hive.blv) in its own frame, for the Map Studio calibration (devdocs/map_studio/REBUILD_PROCEDURE.md). The project files are written by output/studio_cal/mm6_hive/tools/gen.py from measured stations and outlines; NOTES.md says where the rebuild stands.'}
_y.safe_dump(proj,open(L4+'/project.yml','w'),default_flow_style=None,sort_keys=False,width=100000)
