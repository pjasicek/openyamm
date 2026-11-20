"""Per-icon physical dimensions and construction choices, measured from the restored icon designs."""
import copy,json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[2]
owned={r['icon']:r for r in json.loads((P/'ownership.json').read_text())};d=json.loads((P/'designs.json').read_text())

def add(icon,family,**parts):
 assert icon in owned and owned[icon]['family']==family
 d['w02_'+icon]={'icons':[icon],'master_icon':icon,'title':owned[icon]['items'][0]['name'],'family':family,'route':'blender','shape':'components','length':owned[icon]['binding']['length'],**parts}

def knife(icon,guard,width,grip='brown',metal='steel',furniture='brass',shape='up',**extra):
 im=Image.open(R/owned[icon]['icon_reference']).convert('RGBA');a=np.array(im)[...,3];ys,xs=np.nonzero(a>128);height=ys.max()-ys.min()+1;centre=(xs.min()+xs.max())/2;profile=[]
 for t in [0,.15,.4,.65,.83,.94,1]:
  q=(guard-.055)*(1-t)+.008*t;y=int(ys.min()+q*height);span=np.flatnonzero(a[y]>128)
  assert len(span),(icon,y)
  left,right=(span[0]-centre)/height,(span[-1]-centre)/height
  c=(left+right)/2;w=max((right-left)/2,.0009);w=min(w,extra.pop('width_limit',.064))
  profile.append([t,w,c])
 add(icon,'daggers',guard=guard,guard_width=width,guard_shape=shape,grip_cell=grip,blade_cell=metal,furniture=furniture,blade=profile,grip_radius=.021,**extra)

knife('7item015',.71,.065,'brown','worn','iron','straight',guard_radius=.006)
knife('7item016',.66,.14,'red','steel','brass','straight',gem='blue',wrap=False)
knife('7item020',.74,.11,'ochre','iron','brass','up',guard_radius=.01,turns=9)
knife('7item021',.74,.085,'black','worn','iron','up',pommel_gem='white')
knife('7item022',.68,.17,'brown','steel','filigree','down',pommel_gem='red',guard_radius=.014)
knife('dagger1',.69,.15,'black','steel','brass','up',pommel_gem='black')
knife('dagger2',.66,.12,'brown','steel','brass','straight',pommel_gem='green',wrap=False)
knife('dagger3',.66,.14,'ochre','steel','brass','up',gem='blue',guard_radius=.006)
knife('dagger4',.65,.11,'ivory','steel','filigree','up',pommel_gem='green',wrap=False,guard_radius=.008)
knife('dagger5',.67,.15,'red','steel','brass','up',pommel_gem='red',turns=5)
knife('item021',.65,.12,'brown','worn','steel','straight',guard_radius=.007,turns=6)
knife('item022',.63,.13,'red','steel','steel','down',gem='white',pommel_gem='white',guard_radius=.01,turns=3)
# The two already reviewed pilots keep their explicit construction and head profiles.
knife('item023',.69,.14,'ochre','steel','brass','up',guard_radius=.008,turns=8)
knife('item026',.75,.12,'ochre','worn','steel','straight',guard_radius=.008,turns=7)
knife('item027',.70,.12,'brown','steel','brass','straight',guard_radius=.007,turns=8)
knife('ldagger1',.70,.15,'black','worn','brass','up',pommel_gem='black')
knife('ldagger2',.67,.13,'ochre','steel','brass','up',guard_radius=.006,turns=8)

# Each crescent is two independent inner/outer profiles; end notches remain truly open.
C=[[.24,.045,.042],[.27,.1,.05],[.32,.14,.012],[.39,.15,.012],[.45,.12,.055],[.49,.065,.062]]
A=[[.27,.10,.095],[.30,.13,.04],[.38,.16,.008],[.44,.15,.008],[.46,.02,.008]]
def axe(icon,left,**parts):
 add(icon,'axes',left=left,head_cell=parts.pop('head_cell','steel'),furniture=parts.pop('furniture','steel'),haft_cell=parts.pop('haft_cell','ash'),haft_radius=parts.pop('haft_radius',.016),head_mid=parts.pop('head_mid',.36),**parts)
axe('2haxe1',[[.25,.04,.037],[.29,.12,.045],[.36,.15,.008],[.43,.13,.008],[.49,.04,.037]],beak=.15,head_mid=.37,haft_cell='ash',furniture='brass',grips=[[-.45,-.29,'brown'],[.03,.20,'brown']],extra_bands=[[-.46,.015,.022],[-.25,.02,.019]],spike=False)
axe('2haxe2',[[.10,.065,.06],[.15,.105,.03],[.27,.13,.02],[.40,.10,.02],[.49,.03,.028]],head_mid=.27,haft_radius=.012,haft_cell='ash',furniture='brass',grips=[[-.45,-.35,'brown']],pommel_gem='green')
axe('2haxe3',[[.20,.035,.032],[.23,.08,.035],[.33,.105,.008],[.43,.08,.01],[.49,.025,.023]],head_mid=.34,beak=.07,haft_radius=.009,haft_cell='iron',furniture='brass',grips=[[-.45,-.32,'brown'],[-.1,.01,'brown']],extra_bands=[[.12,.012,.013],[.17,.012,.013]])
axe('7item023',[[.28,.13,.01],[.31,.15,.01],[.40,.15,.01],[.46,.14,.01]],head_mid=.37,right=[[.28,.06,.01],[.31,.09,.01],[.40,.09,.01],[.46,.06,.01]],head_cell='brass',furniture='brass',haft_cell='walnut',grips=[[-.46,-.20,'black']],haft_radius=.017)
axe('7item024',C,head_mid=.36,beak=.10,head_cell='iron',furniture='brass',haft_cell='ash',grips=[[-.46,-.14,'black']],haft_radius=.018)
axe('7item025',[[.02,.03,.027],[.07,.11,.045],[.20,.18,.015],[.34,.17,.015],[.45,.11,.05],[.49,.02,.018]],head_mid=.27,head_cell='silverwork',haft_cell='walnut',haft_radius=.017,grips=[[-.46,-.33,'brown']])
axe('7item027',[[.06,.08,.077],[.14,.17,.07],[.28,.20,.008],[.41,.17,.06],[.47,.09,.087]],right=[[.06,.08,.077],[.14,.17,.07],[.28,.20,.008],[.41,.17,.06],[.47,.09,.087]],head_mid=.28,head_cell='iron',haft_cell='iron',haft_radius=.016,grips=[[-.46,-.22,'red']],spike=True,head_top=.43)
axe('7item028',[[.24,.035,.032],[.28,.09,.04],[.36,.12,.008],[.43,.1,.008],[.48,.03,.028]],head_mid=.36,beak=.13,haft_cell='ash',furniture='brass',haft_radius=.013,grips=[[-.45,-.26,'brown'],[.03,.20,'brown']])
axe('7item029',[[.18,.055,.052],[.23,.082,.04],[.31,.10,.008],[.39,.09,.035],[.48,.04,.037]],head_mid=.30,beak=.06,haft_cell='walnut',haft_radius=.009,grips=[[-.45,-.32,'black'],[-.15,-.03,'black']],holes_left=[[-.062,.25,.007],[-.066,.31,.008],[-.065,.37,.007]])
axe('7item030',[[.12,.06,.057],[.18,.10,.045],[.28,.115,.015],[.40,.08,.025],[.49,.025,.023]],head_mid=.25,haft_cell='walnut',haft_radius=.011,grips=[[-.46,-.24,'black'],[.10,.23,'black']],head_cell='steel',extra_bands=[[-.10,.016,.015]])
axe('axe1',[[.20,.11,.105],[.24,.13,.02],[.35,.13,.008],[.39,.10,.009]],head_mid=.31,haft_cell='ash',furniture='brass',haft_radius=.022,grips=[[-.46,-.39,'ash'],[-.15,-.08,'ash']],grip_wrap=False)
axe('axe2',[[.04,.04,.037],[.10,.13,.06],[.26,.16,.008],[.39,.12,.015],[.49,.03,.027]],head_mid=.27,beak=.09,spike=True,head_top=.44,head_cell='silverwork',haft_cell='walnut',haft_radius=.016,grips=[[-.46,-.35,'walnut']],pommel_gem='blue',grip_wrap=False)
axe('axe3',[[.20,.06,.057],[.25,.12,.05],[.36,.14,.008],[.43,.09,.008],[.47,.04,.037]],head_mid=.34,beak=.10,spike=True,furniture='brass',haft_cell='iron',haft_radius=.017,grips=[[-.45,-.31,'red']],extra_bands=[[-.20,.02,.022],[.06,.02,.022]])
axe('item031',[[.28,.12,.115],[.31,.15,.01],[.39,.15,.01],[.45,.10,.009]],head_mid=.36,head_cell='stone',furniture='brass',haft_cell='walnut',haft_radius=.018,grips=[[-.46,.15,'black']],grip_wrap=True)
axe('item032',[[.24,.13,.125],[.29,.12,.06],[.36,.12,.008],[.40,.09,.008]],head_mid=.35,beak=.08,haft_cell='ash',haft_radius=.017,grips=[[-.46,-.24,'brown'],[.18,.26,'brown']])
axe('item033',[[.20,.13,.125],[.27,.12,.06],[.36,.13,.008],[.42,.13,.008]],head_mid=.35,beak=.07,haft_cell='ash',haft_radius=.016,grips=[[-.46,-.21,'brown']],extra_bands=[[-.04,.022,.023]],head_cell='steel')
axe('item034',[[.18,.04,.037],[.23,.13,.04],[.34,.18,.008],[.46,.12,.04],[.49,.065,.062]],head_mid=.34,beak=.09,haft_cell='ash',haft_radius=.016,grips=[[-.46,-.23,'brown']],forked_poll=True,holes_left=[[-.075,.36,.025]],extra_bands=[[-.10,.026,.025]])
axe('item035',[[.12,.06,.056],[.18,.14,.06],[.29,.17,.008],[.42,.13,.045],[.49,.06,.057]],head_mid=.31,beak=.12,haft_cell='walnut',haft_radius=.017,grips=[[-.46,-.43,'walnut']],grip_wrap=False,holes_left=[[-.055,.34,.014]],extra_bands=[[-.08,.025,.024]])
axe('item036',[[.34,.10,.095],[.36,.13,.008],[.42,.13,.008],[.45,.07,.008]],head_mid=.39,spike=True,head_top=.44,haft_cell='ash',head_cell='stone',haft_radius=.012,grips=[[-.46,.12,'black']],grip_wrap=True,furniture='steel')
axe('item037',[[.34,.10,.096],[.37,.13,.05],[.43,.14,.008],[.47,.09,.008]],head_mid=.42,beak=.06,haft_cell='ash',haft_radius=.012,grips=[[-.46,-.28,'brown'],[.07,.32,'brown']],extra_bands=[[.04,.022,.019]])
axe('item038',[[.29,.07,.067],[.34,.11,.04],[.43,.13,.008],[.47,.13,.008]],head_mid=.40,beak=.06,haft_cell='ash',haft_radius=.011,grips=[[-.46,-.27,'brown'],[-.05,.10,'brown']])
axe('item039',[[.25,.065,.061],[.29,.12,.065],[.40,.13,.008],[.47,.12,.008]],head_mid=.40,beak=.06,haft_cell='ash',haft_radius=.011,grips=[[-.46,-.28,'brown']],holes_left=[[-.072,.415,.011],[-.09,.415,.011]])
axe('item040',[[.27,.045,.042],[.30,.08,.045],[.35,.10,.008],[.41,.09,.04],[.44,.045,.042]],head_mid=.36,beak=.075,spike=True,head_top=.44,haft_cell='ash',haft_radius=.011,grips=[[-.46,-.24,'brown']],holes_left=[[-.058,.415,.011],[-.06,.295,.01]],extra_bands=[[.22,.012,.016]])
axe('item240',[[.10,.045,.041],[.17,.14,.05],[.30,.19,.008],[.43,.16,.05],[.49,.07,.066]],head_mid=.30,beak=.12,haft_cell='walnut',haft_radius=.018,grips=[[-.46,-.30,'iron']],holes_left=[[-.06,.29,.017]],grip_wrap=False)
axe('item241',[[.34,.025,.023],[.36,.075,.03],[.41,.09,.008],[.47,.06,.008],[.49,.02,.018]],right=[[.34,.025,.023],[.36,.06,.03],[.41,.085,.008],[.46,.04,.008]],head_mid=.41,spike=True,head_top=.46,haft_cell='ash',furniture='filigree',haft_radius=.01,grips=[[-.46,-.31,'brown']],extra_bands=[[.24,.01,.014],[.06,.01,.014],[-.11,.01,.014]])
for alias,master in [('62haxe4','2haxe3'),('7item305','7item027'),('7item304','7item030'),('item343','item040')]:
 v=copy.deepcopy(d['w02_'+master]);v.update(icons=[alias],master_icon=alias,title=owned[alias]['items'][0]['name'],length=owned[alias]['binding']['length'],variant_of='w02_'+master);d['w02_'+alias]=v
all_icons=[i for v in d.values() for i in v['icons']];assert len(all_icons)==len(set(all_icons))==69 and set(all_icons)==set(owned),(len(all_icons),set(owned)-set(all_icons))
(P/'designs.json').write_text(json.dumps(d,indent=2)+'\n');print('Registered',sum(v['route']=='blender' for v in d.values()),'Blender icons,',sum(len(v['icons']) for v in d.values() if v['route']=='codex'),'Meshy icons')
