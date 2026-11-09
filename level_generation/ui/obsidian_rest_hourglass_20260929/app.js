import {glassPath, chamber, sandState} from './sand-volume.mjs';

const cycleSeconds = 9;
const drainFraction = 8 / 9;
const params = new URLSearchParams(location.search);
let phase = params.has('phase') ? Math.max(0, Math.min(1, Number(params.get('phase')))) : drainFraction / 2;
let playing = !params.has('phase');
let lastTime = performance.now();
let orientation = params.get('turns')==='1' ? 1 : 0;

const art = 'art/v2/hourglass-master-v1.png';
const sandArt = 'art/v2/sand-material.png';

function paintedModel(id) {
  return `<svg viewBox="0 0 1024 1536" role="img" aria-label="Carved obsidian hourglass with champagne sand">
    <defs>
      <clipPath id="glass-${id}"><path d="${glassPath}"/></clipPath>
      <clipPath id="upper-mask-${id}"><path class="upper-mask"/></clipPath>
      <clipPath id="upper-reservoir-${id}">
        <path class="upper-reservoir" transform="rotate(180 512 768)"/>
      </clipPath>
      <pattern id="sand-${id}" width="768" height="768" patternUnits="userSpaceOnUse">
        <image href="${sandArt}" width="768" height="768" preserveAspectRatio="none"/>
      </pattern>
      <linearGradient id="sand-shade-${id}" x1="260" y1="0" x2="760" y2="0" gradientUnits="userSpaceOnUse">
        <stop stop-color="#392b1c" stop-opacity=".6"/><stop offset=".23" stop-color="#68513a" stop-opacity=".18"/>
        <stop offset=".49" stop-color="#fff3cc" stop-opacity=".04"/><stop offset=".72" stop-color="#ac8e62" stop-opacity=".12"/>
        <stop offset="1" stop-color="#493722" stop-opacity=".56"/>
      </linearGradient>
      <linearGradient id="crest-${id}" x1="0" y1="0" x2="1" y2="1">
        <stop stop-color="#fff4d5" stop-opacity=".42"/><stop offset="1" stop-color="#b99964" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="surface-${id}" x1="0" y1="0" x2="0" y2="1">
        <stop stop-color="#fff1c8" stop-opacity=".48"/><stop offset="1" stop-color="#a3804b" stop-opacity=".05"/>
      </linearGradient>
    </defs>
    <g class="rigid-model">
      <g clip-path="url(#glass-${id})">
        <g class="sand-field">
          <g clip-path="url(#upper-mask-${id})">
            <g transform="rotate(180 512 768)">
              <path class="upper-sand" fill="url(#sand-${id})"/>
              <path class="upper-shade" fill="url(#sand-shade-${id})"/>
              <path class="upper-crest" fill="url(#crest-${id})"/>
            </g>
            <path class="upper-surface" fill="url(#surface-${id})" clip-path="url(#upper-reservoir-${id})"/>
          </g>
          <path class="lower-sand" fill="url(#sand-${id})"/>
          <path class="lower-shade" fill="url(#sand-shade-${id})"/>
          <path class="lower-crest" fill="url(#crest-${id})"/>
          <g class="falling-sand">
            <path class="stream-shadow" stroke="#9c7a46" stroke-width="5" stroke-opacity=".23" fill="none"/>
            <path class="stream" stroke="#d9c59a" stroke-width="2.4" stroke-opacity=".75" fill="none"/>
            <path class="stream-grains" stroke="#fff2cf" stroke-width="1.1" stroke-linecap="round"
              stroke-dasharray="2.1 6.3 1 4.7 2.8 8.1" fill="none"/>
            ${Array.from({length:8},(_,i)=>`<circle class="loose-grain" r="${.8+(i%3)*.25}" fill="${i%2?'#b89a67':'#ead8b0'}"/>`).join('')}
          </g>
        </g>
      </g>
      <image class="painted-master" href="${art}" x="0" y="0" width="1024" height="1536"/>
    </g>
  </svg>`;
}

const targets = [...document.querySelectorAll('.hourglass-target')];
function install(el,id) {
  el.innerHTML = el.dataset.design==='wire' ? wireModel(id) : paintedModel(id);
  el.parts = Object.fromEntries([...el.querySelectorAll('[class]')].map(node=>[node.getAttribute('class'),node]));
}
targets.forEach(install);

function drawWire(el,p,angle,value) {
  const e=el.parts;
  const top=95-62*Math.sqrt(1-p), bottom=151-56*Math.sqrt(p), radius=27*Math.sqrt(p);
  const sand=`M${60-radius} 151Q${60-radius/2} ${bottom+8} 60 ${bottom}
    Q${60+radius/2} ${bottom+8} ${60+radius} 151L${60+radius} 157H${60-radius}Z`;
  e['rigid-model'].setAttribute('transform',`rotate(${orientation*180+angle} 60 95)`);
  e['sand-layer'].setAttribute('transform',`rotate(${orientation*180} 60 95)`);
  e['upper-limit'].setAttribute('y',top);e['upper-limit'].setAttribute('height',95-top);
  e['sand-shape'].setAttribute('d',sand);e['sand-grain'].setAttribute('d',sand);
  for (const key of ['stream','stream-grains']) {
    e[key].setAttribute('d',`M60 94V${bottom}`);
    e[key].style.opacity=p<.995?'1':'0';
  }
  e['stream-grains'].setAttribute('stroke-dashoffset',-value*250);
}

function drawPainted(el,p,angle,value,turns=orientation) {
  const e=el.parts, c=chamber(turns);
  const {lower, upper, upperCut: level}=sandState(turns,p);
  e['rigid-model'].setAttribute('transform',`rotate(${turns*180+angle} 512 768)`);
  e['sand-field'].setAttribute('transform',`rotate(${turns*180} 512 768)`);
  // The full upper reservoir is the other orientation's lower reservoir after a half-turn.
  // Shared material coordinates preserve grains at the loop boundary as well as the frame's geometry.
  for(const key of ['upper-sand','upper-shade','upper-reservoir'])e[key].setAttribute('d',upper.d);
  e['upper-crest'].setAttribute('d',upper.crest);
  e['upper-mask'].setAttribute('d',`M0 ${level}H1024V1536H0Z`);
  e['upper-surface'].setAttribute('d',`M150 ${level}Q512 ${level+8} 874 ${level}
    Q512 ${level+28} 150 ${level}Z`);
  e['upper-surface'].style.opacity=Math.min(1,p*25,(1-p)*25);
  for(const key of ['lower-sand','lower-shade'])e[key].setAttribute('d',lower.d);
  e['lower-crest'].setAttribute('d',lower.crest);
  const spout=Math.min(c.neck-7,1536-upper.top-3);
  const stream=`M512 ${spout}Q513 ${(c.neck+lower.top)/2} 512 ${lower.top+2}`;
  for(const key of ['stream','stream-shadow','stream-grains'])e[key].setAttribute('d',stream);
  e['stream-grains'].setAttribute('stroke-dashoffset',-value*2350);
  e['falling-sand'].style.opacity=Math.min(1,p*60,Math.max(0,(1-p)*120));
  el.querySelectorAll('.loose-grain').forEach((grain,i)=>{
    const fall=(value*13.5+i*.127)%1;
    grain.setAttribute('cx',512+Math.sin(i*4.1+fall*2.8)*(1+fall*3));
    grain.setAttribute('cy',spout+fall*Math.max(0,lower.top-spout));
    grain.setAttribute('opacity',.28+fall*.45);
  });
}

function draw(value) {
  const p=Math.min(1,value/drainFraction);
  const turn=Math.max(0,(value-drainFraction)/(1-drainFraction));
  const angle=180*turn*turn*(3-2*turn);
  for(const el of targets) {
    if(el.dataset.design==='wire')drawWire(el,p,angle,value);
    else if(el.dataset.fill)drawPainted(el,Number(el.dataset.fill),0,value,0);
    else drawPainted(el,p,angle,value);
  }
  document.getElementById('state').textContent=p<1?'Sand falling':'Rigid half-turn';
  document.getElementById('phase').value=value;
}
document.getElementById('play').textContent=playing?'Pause':'Play';
document.getElementById('play').onclick=()=>{
  playing=!playing;document.getElementById('play').textContent=playing?'Pause':'Play';
};
document.getElementById('phase').oninput=e=>{
  phase=Number(e.target.value);playing=false;document.getElementById('play').textContent='Play';draw(phase);
};
document.getElementById('backdrop').onchange=e=>document.body.classList.toggle('light',e.target.value==='light');
document.getElementById('design').onchange=e=>{
  targets[0].dataset.design=e.target.value;install(targets[0],0);draw(phase);
};
if(params.get('backdrop')==='light') {
  document.body.classList.add('light');document.getElementById('backdrop').value='light';
}
if(params.get('view')==='detail')document.body.classList.add('detail-view');
function resize() {
  document.getElementById('stage').style.transform=`scale(${document.getElementById('stage-wrap').clientWidth/1600})`;
}
window.addEventListener('resize',resize);resize();draw(phase);
function animate(now) {
  if(playing) {
    const next=phase+(now-lastTime)/1000/cycleSeconds;
    orientation=(orientation+Math.floor(next))%2;phase=next%1;draw(phase);
  }
  lastTime=now;requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
window.hourglassStudy={
  setPhase(value,turns=0){phase=value;orientation=turns%2;playing=false;draw(phase);},targets
};
