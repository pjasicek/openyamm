const assets='../../../assets_dev/engine/icons_x2/';
const people=[
  {name:'Ariel',art:'pc01-01',hp:100,mana:75,hasMana:true,buffs:true},
  {name:'Ilyana',art:'pc02-01',hp:82,mana:65,hasMana:true,buffs:false},
  {name:'Corin',art:'pc03-01',hp:51,mana:0,hasMana:false,buffs:true},
  {name:'Lyra',art:'pc04-01',hp:34,mana:40,hasMana:true,buffs:false},
  {name:'Thane',art:'pc05-01',hp:22,mana:90,hasMana:true,buffs:true}
];
const state={mode:'split',count:5,selected:0,aggro:'explore',recovering:false,buffs:true,classic:false,damage:null};
let serial=0;
const $=id=>document.getElementById(id);
const image=(asset,x,y,w,h,extra='')=>`<image href="${assets+asset}.png" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="none" ${extra}/>`;
const pt=(cx,cy,rx,ry,degrees)=>{const angle=degrees*Math.PI/180;return [cx+Math.cos(angle)*rx,cy+Math.sin(angle)*ry];};
function arc(cx,cy,rx,ry,start,end){const a=pt(cx,cy,rx,ry,start),b=pt(cx,cy,rx,ry,end);return `M${a} A${rx} ${ry} 0 ${Math.abs(end-start)>180?1:0} ${end>start?1:0} ${b}`;}
const palette=hp=>hp>=66?['#acd69b','#80ad77','#315834']:hp>33?['#ead28c','#c7a557','#766031']:['#e99682','#c9685e','#76362d'];
function portrait(index,mode,detail=false){
  const p=people[index],uid=`p${++serial}`,selected=index===state.selected&&!state.recovering;
  const hp=palette(p.hp),cx=mode==='vertical'?30.8:39,cy=39.973333,rx=23.76,ry=31.973333;
  let out=`<defs><clipPath id="${uid}-face"><ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}"/></clipPath><linearGradient id="${uid}-metal"><stop stop-color="#544d3d"/><stop offset=".3" stop-color="#b6a47b"/><stop offset=".6" stop-color="#665b44"/><stop offset="1" stop-color="#938666"/></linearGradient><linearGradient id="${uid}-hp"><stop stop-color="${hp[0]}"/><stop offset=".3" stop-color="${hp[1]}"/><stop offset="1" stop-color="${hp[2]}"/></linearGradient><linearGradient id="${uid}-sp"><stop stop-color="#abcfd8"/><stop offset=".3" stop-color="#73a4b7"/><stop offset="1" stop-color="#2d596a"/></linearGradient></defs>`;
  out+=image(p.art,cx-rx,8,rx*2,ry*2,`clip-path="url(#${uid}-face)"`);
  out+=`<ellipse cx="${cx}" cy="${cy}" rx="${rx+1.7}" ry="${ry+1.7}" fill="none" stroke="#090e0d" stroke-width="2.8"/><ellipse class="selection-rim" cx="${cx}" cy="${cy}" rx="${rx+1.3}" ry="${ry+1.3}" fill="none" stroke="${selected?'#f0dca3':`url(#${uid}-metal)`}" stroke-width="${selected?1.5:.85}"/>`;
  const trail=state.damage&&state.damage.index===index?Math.max(p.hp,state.damage.from-(performance.now()-state.damage.at)/850*(state.damage.from-p.hp)):p.hp;
  const meter=(kind,mrx,mry,start,end,width)=>{
    const amount=kind==='hp'?p.hp:p.mana,full=arc(cx,cy,mrx,mry,start,end);
    let s=`<g class="${kind}-meter"><title>${kind==='hp'?'Health':'Mana'}: ${amount}/100</title><path d="${full}" fill="none" stroke="url(#${uid}-metal)" stroke-width="${width+1.7}"/><path d="${full}" fill="none" stroke="#0a1312" stroke-width="${width+.5}"/>`;
    if(kind==='hp'&&trail>amount)s+=`<path d="${arc(cx,cy,mrx,mry,start+(end-start)*amount/100,start+(end-start)*trail/100)}" fill="none" stroke="#e4c793" stroke-width="${width}" opacity=".8"/>`;
    if(amount>0){const filled=arc(cx,cy,mrx,mry,start,start+(end-start)*amount/100);s+=`<path d="${filled}" fill="none" stroke="url(#${uid}-${kind})" stroke-width="${width}"/><path d="${filled}" fill="none" stroke="#eef6d4" stroke-opacity=".22" stroke-width="${width*.22}"/>`;}
    return s+'</g>';
  };
  if(mode==='split'){
    out+=meter('hp',30.2,38.4,100,260,4.6);
    if(p.hasMana)out+=meter('sp',30.2,38.4,80,-80,4.6);
  }else if(mode==='nested'){
    out+=meter('hp',28.8,36.9,115,425,3.3);
    if(p.hasMana)out+=meter('sp',33.3,41.4,115,425,2.6);
  }else{
    for(const kind of p.hasMana?['hp','sp']:['hp']){const x=kind==='hp'?60:68,value=kind==='hp'?p.hp:p.mana;out+=`<g class="${kind}-meter"><rect x="${x-1}" y="9" width="6.8" height="60" fill="#101713" stroke="#837b60" stroke-width=".6"/><rect x="${x}" y="${10+58*(1-value/100)}" width="4.8" height="${58*value/100}" fill="url(#${uid}-${kind})"/></g>`;}
  }
  if(selected)out+=image('obsidian_hud_selection_diamond',cx-9.5,-10.5,19,19,'class="selection-diamond"');
  const ax=mode==='vertical'?2:10,ay=mode==='nested'?78:75,bx=mode==='vertical'?55:68;
  out+=image(`obsidian_aggro_${state.aggro}`,ax-10,ay-10.8,20,21.6,'class="aggro-indicator"');
  if(state.recovering)out+=`<path class="recovery-arc" d="${arc(ax,ay,7.9,7.9,-90,-90+360*(.2+index*.12))}" stroke="#d8e8e5" stroke-width="1.3" fill="none"/>`;
  if(state.buffs&&p.buffs)out+=`<g class="buff-button" role="button" tabindex="0" data-buff="${index}" aria-label="${p.name}: individual buffs">${image('obsidian_personal_buffs',bx-7.7,ay-7.7,15.4,15.4)}<title>Individual buffs</title></g>`;
  out+=`<rect class="focus-outline" x="-1" y="-12" width="80" height="103" rx="7"/>`;
  return detail?`<svg viewBox="-5 -14 88 108" xmlns="http://www.w3.org/2000/svg">${out}</svg>`:`<g class="pc" data-pc="${index}" role="button" tabindex="0" aria-label="Select ${p.name}">${out}</g>`;
}
function frame(width){
  const corner=30.933333,uid=`f${++serial}`,height=88;
  let out=`<defs><pattern id="${uid}-surface" width="640" height="480" patternUnits="userSpaceOnUse">${image('obsidian_reading_surface',0,0,640,480)}</pattern><pattern id="${uid}-top" width="48.286179" height="${corner}" patternUnits="userSpaceOnUse">${image('obsidian_frame_top',0,0,48.286179,corner)}</pattern><pattern id="${uid}-bottom" width="48.286179" height="${corner}" patternUnits="userSpaceOnUse" patternTransform="translate(0 ${height-corner})">${image('obsidian_frame_bottom',0,0,48.286179,corner)}</pattern></defs>`;
  out+=`<rect x="8" y="8" width="${width-16}" height="72" fill="url(#${uid}-surface)"/><rect x="${corner}" y="0" width="${width-2*corner}" height="${corner}" fill="url(#${uid}-top)"/><rect x="${corner}" y="${height-corner}" width="${width-2*corner}" height="${corner}" fill="url(#${uid}-bottom)"/>`;
  for(const [name,x,y] of [['tl',0,0],['tr',width-corner,0],['bl',0,height-corner],['br',width-corner,height-corner]])out+=image(`obsidian_frame_${name}`,x,y,corner,corner);
  for(const right of [false,true])out+=`<g ${right?`transform="translate(${width} 0) scale(-1 1)"`:''}><svg x="-30.7" y="-13" width="40.7" height="110" viewBox="208.32 63.44 535.68 1459.12" preserveAspectRatio="none">${image('obsidian_party_endcap',0,0,992,1586)}</svg></g>`;
  return out;
}
function render(){
  const width=22+80*state.count,scale=state.classic?2:1.875;
  $('bar').innerHTML=`<svg width="${(width+68)*scale}" viewBox="-34 -14 ${width+68} 113" xmlns="http://www.w3.org/2000/svg" aria-label="${state.mode} arrangement, ${state.count} portraits">${frame(width)}${people.slice(0,state.count).map((p,i)=>`<g transform="translate(${12+80*i} 0)">${portrait(i,state.mode)}</g>`).join('')}</svg>`;
  $('scale-note').textContent=`${state.classic?'4:3 · 1280 × 960':'Widescreen · 1600 × 900'} · native ${scale}× logical scale · ${state.count} member${state.count===1?'':'s'}`;
  $('detail').innerHTML=portrait(state.selected,state.mode,true);
  $('selection-note').textContent=state.recovering?'Nobody ready: selection rim and top diamond are suppressed.':'Selection stays on the inner rim. The coloured arcs remain resources.';
  $('mode-note').textContent=state.mode==='split'?'A · HP rises around the left side; mana rises around the right. The gaps leave room for the top diamond and lower controls.':state.mode==='nested'?'B · Health uses the inner coloured ring; mana uses the slimmer outer ring. More continuous travel, but more rings to distinguish.':'Previous layout · both vertical tracks remain at the portrait’s right. The same frame, portrait size and state controls apply.';
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
  const p=people[state.selected];$('active-name').textContent=p.name;$('hp').value=p.hp;$('mana').value=p.mana;$('hp-value').textContent=p.hp+'%';$('mana-value').textContent=p.hasMana?p.mana+'%':'—';$('mana').disabled=!p.hasMana;$('no-mana').checked=!p.hasMana;
  document.querySelectorAll('[data-pc]').forEach(g=>{const choose=()=>{state.selected=Number(g.dataset.pc);render();};g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});});
  document.querySelectorAll('[data-buff]').forEach(g=>{const show=e=>{e.stopPropagation();const p=people[Number(g.dataset.buff)];$('buff-popup').hidden=false;$('buff-popup').innerHTML=`<h3>${p.name}</h3><p>Bless · 22m</p><p>Regeneration · 5m</p><button>Close</button>`;$('buff-popup').querySelector('button').onclick=()=>{$('buff-popup').hidden=true;};};g.addEventListener('click',show);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show(e);}});});
}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode;render();});
$('party').onchange=e=>{state.count=Number(e.target.value);state.selected=Math.min(state.selected,state.count-1);render();};
$('view').onchange=e=>{state.classic=e.target.value==='classic';render();};
$('aggro').onchange=e=>{state.aggro=e.target.value;render();};
$('recovering').onchange=e=>{state.recovering=e.target.checked;render();};
$('buffs').onchange=e=>{state.buffs=e.target.checked;if(!state.buffs)$('buff-popup').hidden=true;render();};
$('no-mana').onchange=e=>{people[state.selected].hasMana=!e.target.checked;render();};
for(const id of ['hp','mana'])$(id).oninput=e=>{people[state.selected][id]=Number(e.target.value);state.damage=null;render();};
$('damage').onclick=()=>{const p=people[state.selected];state.damage={index:state.selected,from:p.hp,at:performance.now()};p.hp=Math.max(0,p.hp-22);const tick=()=>{render();if(state.damage&&performance.now()-state.damage.at<850)requestAnimationFrame(tick);else{state.damage=null;render();}};tick();};
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('buff-popup').hidden=true;});
const query=new URLSearchParams(location.search);if(['split','nested','vertical'].includes(query.get('mode')))state.mode=query.get('mode');
render();
