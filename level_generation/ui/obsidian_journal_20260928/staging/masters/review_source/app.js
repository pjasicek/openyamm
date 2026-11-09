"use strict";
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const params = new URLSearchParams(location.search);
const views = {map:"Map",quests:"Quests",story:"Story",notes:"Autonotes",status:"Status strip · 2090"};
const categories = {potion:"Potions",fountain:"Fountains",obelisk:"Obelisks",seer:"Seer",misc:"Misc.",trainer:"Trainers"};
const titles = {potion:"Potion Notes",fountain:"Fountain Notes",obelisk:"Obelisk Notes",seer:"Seer Notes",misc:"Miscellaneous Notes",trainer:"Trainer Notes"};
const pick = (key, options, fallback) => options.includes(params.get(key)) ? params.get(key) : fallback;
const state = {view:pick("view",Object.keys(views),"map"),mode:pick("content",["examples","reference","long"],"examples"),
  category:pick("category",Object.keys(categories),"potion"),fog:pick("fog",["start","partial","all"],"partial"),
  alignment:pick("align",["justify","left"],"justify"),
  page:0,zoom:0,center:[.5,.5],closed:false,legacy:params.get("legacy")==="1",selectedPin:-1};
const stage = $("#stage"), journal = $("#journal"), textViewport = $("#text-viewport"), canvas = $("#map");
const mapImage = new Image();
mapImage.src = "assets/new-sorpigal.png";
const party = [.35,.67];
const pins = [{uv:[.36,.51],name:"New Sorpigal · fountain"},{uv:[.43,.46],name:"Temple"},{uv:[.28,.60],name:"Town bridge"}];
let pages = [], drag = null, hoveredPin = -1;
const escapeHtml = value => String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
const icon = name => `assets/generated/journal-${name}-v1.png`;
const arrow = direction => `<svg viewBox="0 0 40 30" aria-hidden="true"><path d="${direction==="previous"?"M29 4 11 15l18 11M12 15h25":"M11 4 29 15 11 26M28 15H3"}"/><path d="M20 2v4M20 24v4" opacity=".3"/></svg>`;
const zoomGlyph = delta => `<svg viewBox="0 0 40 30" aria-hidden="true"><circle cx="16" cy="12" r="9"/><path d="m23 19 11 8M11 12h10${delta>0?"M16 7v10":""}"/></svg>`;
const button = (label, attributes, glyph="", cls="page-button") => `<button class="obs-button ${cls}" ${attributes}>${glyph}<span class="obs-label">${escapeHtml(label)}</span></button>`;

function setUrl() {
  const query = new URLSearchParams(location.search);
  for(const [key,value] of Object.entries({view:state.view,content:state.mode,category:state.category,fog:state.fog,align:state.alignment,legacy:state.legacy?"1":"0"})) query.set(key,value);
  history.replaceState(null,"","?"+query);
}
function scaleStage() {
  const host=$("#stage-host");
  const scale=Math.min(host.clientWidth/1600,host.clientHeight/900);
  stage.style.transform=`scale(${scale})`;
  stage.style.left=(host.clientWidth-1600*scale)/2+"px";
  stage.style.top=(host.clientHeight-900*scale)/2+"px";
}
function buildPages(entries, story=false) {
  const measure=document.createElement("div");
  const bodyStyle=getComputedStyle(textViewport);
  measure.style.cssText=`position:absolute;left:-10000px;top:0;visibility:hidden;width:${textViewport.clientWidth}px;white-space:pre-wrap;overflow-wrap:anywhere;font:${bodyStyle.font};text-align:${bodyStyle.textAlign};text-align-last:left;text-justify:inter-word;hyphens:none`;
  document.body.append(measure);
  const height=textViewport.clientHeight, gap=story?28:35;
  const result=[], page=[];
  let used=0;
  const finish=()=>{if(page.length)result.push(page.splice(0));used=0;};
  const measured=text=>{measure.textContent=text;return measure.getBoundingClientRect().height;};
  for(const entry of entries) {
    let remainder=entry;
    while(remainder.length) {
      const available=height-used-(page.length?gap:0);
      if(measured(remainder)<=available+.1){page.push({text:remainder,continues:false});used+=measured(remainder)+(page.length>1?gap:0);break;}
      if(page.length){finish();continue;}
      const words=remainder.match(/\S+\s*/g)||[remainder];
      let count=0, part="";
      while(count<words.length && measured(part+words[count])<=height+.1) part+=words[count++];
      if(!count){part=words[0];count=1;}
      page.push({text:part.trimEnd(),continues:count<words.length});finish();remainder=words.slice(count).join("");
    }
  }
  finish();measure.remove();return result.length?result:[[]];
}
function journalEntries() {
  if(state.mode==="reference") return state.view==="quests"?[JOURNAL_CONTENT.quests[0].text]:[];
  if(state.view==="quests") return JOURNAL_CONTENT.quests.slice(0,state.mode==="long"?30:5).map(e=>e.text);
  if(state.view==="notes") return JOURNAL_CONTENT.notes[state.category].slice(0,state.mode==="long"?24:6).map(e=>e.text);
  if(state.view==="story") {
    // Use actual table text. Resolve only the two party-name placeholders for the clearly labelled fixture.
    return JOURNAL_CONTENT.story[0].text.replaceAll("%31","Kareth").replaceAll("%33","he").split(/\n\s*\n/);
  }
  return [];
}
function fitTitle() {
  const title=$("#page-title");title.style.fontSize="56.25px";
  for(let size=56.25;size>=42;size-=1.875){title.style.fontSize=size+"px";if(title.scrollWidth<=title.clientWidth && title.scrollHeight<=title.clientHeight)break;}
}
function render() {
  journal.hidden=state.closed||state.view==="status";
  $("#journal-backdrop").hidden=state.closed;
  $("#reopen").hidden=!state.closed;
  if(state.closed){$("#legacy-image").hidden=true;setUrl();return;}
  journal.classList.toggle("story",state.view==="story");
  textViewport.style.textAlign=state.alignment;
  textViewport.dataset.align=state.alignment;
  $("#body-alignment").value=state.alignment;
  $("#alignment-control").hidden=state.view==="map"||state.view==="status";
  $("#status-specimen").hidden=state.view!=="status";
  $("#status-specimen").innerHTML=`<div class="status-sample original"><span class="status-caption">ORIGINAL · 2090</span><img src="../../../test_img/2090.png" alt="Original creation status strip"></div>
    <div class="status-sample"><span class="status-caption">OBSIDIAN · SOFT IVORY / EXISTING MM LETTERING</span>${escapeHtml(JOURNAL_CONTENT.status)}</div>
    <div class="status-sample"><span class="status-caption">SHORTER MESSAGE</span>All adventurers are ready.</div>`;
  $("#legacy-image").hidden=!state.legacy||state.view==="status";
  $("#legacy-image").src=`../../../test_img/${{map:2091,quests:2092,story:2093,notes:2094,status:2090}[state.view]}.png`;
  $("#view-tabs").innerHTML=Object.entries(views).map(([key,label])=>`<button data-view="${key}" aria-pressed="${state.view===key}">${label}</button>`).join("");
  $("#main-navigation").innerHTML=["map","quests","story","notes"].map(key=>button(key==="notes"?"Notes":views[key],`data-view="${key}" aria-pressed="${state.view===key}"`,
    `<img src="${icon(key)}" alt="">`,"main-button")).join("");
  $("#note-categories").hidden=state.view!=="notes";
  $("#note-categories").innerHTML=Object.entries(categories).map(([key,label])=>button(label,`data-category="${key}" aria-pressed="${state.category===key}" title="${titles[key]}"`,
    `<img src="${icon(key)}" alt="">`,"category")).join("");
  $("#view-emblem").src=icon(state.view==="status"?"notes":state.view);
  const isMap=state.view==="map";
  $("#map-area").hidden=!isMap;textViewport.hidden=isMap;
  $("#page-number").hidden=isMap||state.mode==="reference";
  if(isMap){$("#page-title").textContent="New Sorpigal";renderMapControls();drawMap();}
  else {
    $("#page-title").textContent=state.view==="quests"?"Current Quests":state.view==="notes"?titles[state.category]:state.mode==="reference"?"Story":JOURNAL_CONTENT.story[0].title;
    pages=buildPages(journalEntries(),state.view==="story");
    state.page=Math.max(0,Math.min(state.page,pages.length-1));
    textViewport.innerHTML=pages[state.page].map(({text,continues})=>`<p class="entry${continues?" continues":""}">${escapeHtml(text)}</p>`).join("");
    $("#page-controls").innerHTML=button("Previous",`data-page="-1" ${state.page===0?"disabled":""}`,arrow("previous"))+
      button("Next",`data-page="1" ${state.page===pages.length-1?"disabled":""}`,arrow("next"));
    $("#page-number").textContent=`${state.page+1} / ${pages.length}`;
  }
  $("#content-mode").value=state.mode;$("#fog").value=state.fog;$("#legacy").checked=state.legacy;
  $("#fog-control").hidden=!isMap;$("#reopen").hidden=!state.closed;
  $("#caption").textContent=state.view==="status"?"2090 is a creation-status strip; this specimen proposes only its shared surface and text treatment.":
    `${views[state.view]} · ${state.mode==="reference"?"sparse/empty reference state":"actual content-table examples"}${state.view==="notes"?" · "+categories[state.category]:""}`;
  fitTitle();setUrl();scaleStage();
}
function renderMapControls() {
  $("#page-controls").innerHTML=button("Zoom in",`data-zoom="1" ${state.zoom===2?"disabled":""}`,zoomGlyph(1))+
    button("Zoom out",`data-zoom="-1" ${state.zoom===0?"disabled":""}`,zoomGlyph(-1));
}
function mapSpan(){return 1/[1,2,4][state.zoom];}
function clampMap(){const h=mapSpan()/2;state.center=state.center.map(v=>Math.max(h,Math.min(1-h,v)));}
function mapToScreen(uv){const s=mapSpan();return [(uv[0]-state.center[0]+s/2)/s*900,(uv[1]-state.center[1]+s/2)/s*900];}
function revealed(uv) {
  if(state.fog==="all")return true;
  const at=[Math.floor(uv[0]*88)/88,Math.floor(uv[1]*88)/88];
  const radius=state.fog==="start"?.095:.235;
  return Math.hypot(at[0]-party[0],at[1]-party[1])<radius || state.fog==="partial" && Math.hypot(at[0]-.45,at[1]-.39)<.16;
}
function drawMap() {
  if(!mapImage.complete||!mapImage.naturalWidth)return;
  clampMap();const ctx=canvas.getContext("2d"),span=mapSpan(),origin=[state.center[0]-span/2,state.center[1]-span/2];
  ctx.clearRect(0,0,900,900);ctx.fillStyle="#000";ctx.fillRect(0,0,900,900);
  ctx.save();ctx.beginPath();
  for(let y=0;y<88;y++)for(let x=0;x<88;x++){const uv=[(x+.5)/88,(y+.5)/88];if(revealed(uv))ctx.rect((x/88-origin[0])/span*900,(y/88-origin[1])/span*900,900/88/span+.1,900/88/span+.1);}
  ctx.clip();ctx.drawImage(mapImage,-origin[0]/span*900,-origin[1]/span*900,900/span,900/span);ctx.restore();
  if(state.mode!=="reference")pins.forEach((pin,i)=>{
    if(!revealed(pin.uv))return;const [x,y]=mapToScreen(pin.uv);
    ctx.save();ctx.translate(x,y);ctx.fillStyle=i===hoveredPin||i===state.selectedPin?"#fff0b5":"#d9b876";ctx.strokeStyle="#171b16";ctx.lineWidth=2;
    ctx.beginPath();ctx.moveTo(0,-11);ctx.lineTo(8,-2);ctx.lineTo(0,14);ctx.lineTo(-8,-2);ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();
  });
  const [px,py]=mapToScreen(party);ctx.save();ctx.translate(px,py);ctx.strokeStyle="#172016";ctx.lineWidth=3;ctx.fillStyle="#f1ead8";
  ctx.beginPath();ctx.moveTo(13,0);ctx.lineTo(-9,-8);ctx.lineTo(-4,0);ctx.lineTo(-9,8);ctx.closePath();ctx.stroke();ctx.fill();ctx.restore();
  const selected=hoveredPin>=0?hoveredPin:state.selectedPin;
  $("#map-note").textContent=selected>=0&&revealed(pins[selected].uv)&&state.mode!=="reference"?pins[selected].name:"";
}
function changeZoom(delta,recenter) {
  state.zoom=Math.max(0,Math.min(2,state.zoom+delta));
  if(recenter)state.center=[...party];clampMap();renderMapControls();drawMap();
}
function pointerUV(e){const r=canvas.getBoundingClientRect(),s=mapSpan();return [state.center[0]+((e.clientX-r.x)/r.width-.5)*s,state.center[1]+((e.clientY-r.y)/r.height-.5)*s];}
canvas.addEventListener("wheel",e=>{e.preventDefault();changeZoom(e.deltaY<0?1:-1,false);},{passive:false});
canvas.addEventListener("pointerdown",e=>{if(e.button!==0)return;canvas.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,center:[...state.center],moved:false};canvas.classList.add("dragging");});
canvas.addEventListener("pointermove",e=>{
  const r=canvas.getBoundingClientRect();
  if(drag){const dx=(e.clientX-drag.x)/r.width*mapSpan(),dy=(e.clientY-drag.y)/r.height*mapSpan();drag.moved ||= Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>4;state.center=[drag.center[0]-dx,drag.center[1]-dy];clampMap();}
  const uv=pointerUV(e);hoveredPin=state.mode==="reference"?-1:pins.findIndex(p=>revealed(p.uv)&&Math.hypot(p.uv[0]-uv[0],p.uv[1]-uv[1])<mapSpan()*.023);
  $("#coordinates").textContent=`x: ${Math.round(uv[0]*32768-16384)}   y: ${Math.round(16384-uv[1]*32768)}`;drawMap();
});
canvas.addEventListener("pointerup",e=>{if(drag&&!drag.moved&&hoveredPin>=0)state.selectedPin=hoveredPin;drag=null;canvas.classList.remove("dragging");if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);drawMap();});
const stopDrag=()=>{drag=null;canvas.classList.remove("dragging");};
canvas.addEventListener("lostpointercapture",stopDrag);canvas.addEventListener("pointercancel",stopDrag);window.addEventListener("blur",stopDrag);
canvas.addEventListener("pointerleave",()=>{if(!drag){hoveredPin=-1;$("#coordinates").textContent="x: -9728   y: -11319";drawMap();}});
document.addEventListener("click",e=>{
  const target=e.target.closest("button");if(!target)return;
  if(target.dataset.view){state.view=target.dataset.view;state.closed=false;state.page=0;render();}
  else if(target.dataset.category){state.category=target.dataset.category;state.page=0;render();}
  else if(target.dataset.page){state.page+=Number(target.dataset.page);render();}
  else if(target.dataset.zoom)changeZoom(Number(target.dataset.zoom),true);
});
$("#content-mode").addEventListener("change",e=>{state.mode=e.target.value;state.page=0;render();});
$("#body-alignment").addEventListener("change",e=>{state.alignment=e.target.value;render();});
$("#fog").addEventListener("change",e=>{state.fog=e.target.value;drawMap();setUrl();});
$("#legacy").addEventListener("change",e=>{state.legacy=e.target.checked;render();});
$("#close").addEventListener("click",()=>{state.closed=true;render();});
$("#reopen").addEventListener("click",()=>{state.closed=false;render();});
$("#fullscreen").addEventListener("click",async()=>{if(document.fullscreenElement)await document.exitFullscreen();else await $("#stage-host").requestFullscreen();});
document.addEventListener("keydown",e=>{
  if(e.target.matches("input,select,textarea")||state.legacy)return;
  if(e.key==="Escape"&&!document.fullscreenElement){state.closed=!state.closed;render();}
  else if(!state.closed&&state.view==="map"&&["+","=","-"].includes(e.key))changeZoom(e.key==="-"?-1:1,false);
  else if(!state.closed&&state.view!=="map"&&["ArrowLeft","ArrowRight"].includes(e.key)){state.page+=e.key==="ArrowLeft"?-1:1;render();}
});
mapImage.onload=drawMap;
if(params.get("export")==="1")document.body.classList.add("export");
new ResizeObserver(scaleStage).observe($("#stage-host"));
document.addEventListener("fullscreenchange",scaleStage);
Promise.all([document.fonts.load('30.375px NativeAutonote'),document.fonts.load('56.25px NativeBook2'),
  document.fonts.load('25px "Obsidian Fondamento"'),document.fonts.load('33.75px NativeCreate'),
  document.fonts.load('30.375px NativeLucida')])
  .then(()=>{render();window.reviewReady=true;});
