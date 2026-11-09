"use strict";
(async () => {
  const data = window.MINIMAP_STUDY;
  const $ = id => document.getElementById(id);
  const variants = {
    original_x2: ["Original · nearest x2", "The archived 512×512 map, enlarged without changing its pixels."],
    vinevi_noise_light_x2: ["Terrain noise · light", "Gentler lighting with subtle, repeatable tonal texture on land. Building artwork, open water and map coordinates are preserved."],
    vinevi_noise_medium_x2: ["Terrain noise · medium", "The same land texture at a stronger intensity, for comparison. No added features or changes to the lighting."],
    vinevi_x2: ["Vinevi process · gentler shading, less smoothing", "Softer lighting contrast, lighter terrain edge treatment and a little more native slope definition. Buildings stay aligned; vegetation remains absent."],
    vinevi_previous_x2: ["Vinevi process · previous stronger shading", "The previous version, retained for comparison: stronger hill shading, fully smooth normals and heavier terrain edge treatment."],
    vinevi_no_pick_x2: ["Vinevi process · without terrain edge breakup", "The same lighting, building levels and final grade, with no Random Pick. All image coordinates remain fixed."],
    vinevi_raw_x2: ["Vinevi process · lighting only", "The separate terrain and building renders composited before levels, color grading, sharpening or edge breakup."],
    lanczos_x2: ["Original · plain Lanczos x2", "A conventional resize: preserves the painting, with no neural reconstruction."],
    anime_faithful_x2: ["Real-ESRGAN · anime-video x2", "Cleaner than x4plus on this map’s water. Some original dithering remains; small features can soften."],
    anime_light_denoise_x2: ["Real-ESRGAN · anime-video + mild denoise", "A 40% median-filter blend before upscaling. Calmer texture, with a small loss of fine detail."],
    esrgan_faithful_x2: ["Real-ESRGAN · x4plus → x2", "This trial exaggerates water dithering into grid patterns. Retained to show why the model matters."],
    esrgan_light_denoise_x2: ["Real-ESRGAN · x4plus + mild denoise", "Pre-filtering reduces some noise but does not eliminate the grid patterns in this trial."],
    blender_x2: ["Terrain capture · raw", "Exact terrain and 85 native model groups with restored textures; faceted lighting, no sprite vegetation."],
    blender_smooth_x2: ["Terrain capture · smooth lighting", "Same mesh and camera, with smooth terrain normals and brighter lighting."],
    blender_styled_x2: ["Terrain capture · filtered + relief", "Gentle color smoothing and relief derived from actual elevations. No XY warping. Vegetation is still absent."],
    installed: ["Previously installed restoration", "The installed art is included for comparison with actual geometry; this study does not change it."]
  };
  const images = {};
  const loadImage = async (key, url) => {
    const image = new Image();image.src = url;await image.decode();images[key] = image;
  };
  await Promise.all(Object.entries(data.outputs).map(([key,row]) => loadImage(key, "new_sorpigal/" + row.file+"?v="+row.sha256.slice(0,12))));
  await loadImage("geometry", "new_sorpigal/geometry_overlay.png");
  let center = [512,512], zoom = 1, cursor = null, dragging = null, blink = false;
  for (const side of ["left","right"]) {
    for (const [key,[label]] of Object.entries(variants)) $(side).add(new Option(label,key));
    $(side).onchange = draw;
  }
  $("left").value = "vinevi_x2";$("right").value = "vinevi_noise_light_x2";
  for (const [index,control] of data.controls.entries()) $("jump").add(new Option(control.label,index));
  function clampCenter() {
    const half = 512/zoom;
    center = center.map(x=>Math.max(half,Math.min(1024-half,x)));
  }
  function draw() {
    const span = 1024/zoom, x0 = center[0]-span/2, y0 = center[1]-span/2;
    for (const side of ["left","right"]) {
      const selected = $(side).value, key = blink && side === "right" ? "original_x2" : selected;
      const ctx = $(side+"Map").getContext("2d");
      ctx.imageSmoothingEnabled = key !== "original_x2";
      ctx.clearRect(0,0,1024,1024);ctx.drawImage(images[key],x0,y0,span,span,0,0,1024,1024);
      if ($("geometry").checked) ctx.drawImage(images.geometry,x0,y0,span,span,0,0,1024,1024);
      if ($("landmarks").checked) {
        ctx.font = "18px system-ui";ctx.lineWidth = 4;
        for (const control of data.controls) {
          const x = (control.pixel[0]-x0)*zoom, y = (control.pixel[1]-y0)*zoom;
          ctx.strokeStyle = "#182127";ctx.fillStyle = "#fff49b";
          ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
          ctx.strokeText(control.label,x+8,y-8);ctx.fillText(control.label,x+8,y-8);
        }
      }
      if (cursor) {
        const x = (cursor[0]-x0)*zoom, y = (cursor[1]-y0)*zoom;
        ctx.strokeStyle = "#ffffffcc";ctx.lineWidth = 1;
        ctx.beginPath();ctx.moveTo(x-14,y);ctx.lineTo(x+14,y);ctx.moveTo(x,y-14);ctx.lineTo(x,y+14);ctx.stroke();
      }
      $(side+"Note").textContent = variants[key][1];
      $(side+"File").href = "new_sorpigal/"+data.outputs[selected].file;
    }
    $("zoom").value = zoom;
    $("coordinate").textContent = cursor ?
      `World X ${Math.round(cursor[0]*64-32768)} · Y ${Math.round(32768-cursor[1]*64)}` : "Move over either map to compare locations.";
  }
  function setView(name) {
    [center,zoom] = {full:[[512,512],1],town:[[354,615],3.6],islands:[[515,256],1.9]}[name];
    cursor=null;clampCenter();draw();
  }
  for (const button of document.querySelectorAll("[data-view]")) button.onclick=()=>setView(button.dataset.view);
  $("zoom").oninput=()=>{zoom=Number($("zoom").value);clampCenter();draw();};
  for (const id of ["geometry","landmarks"]) $(id).onchange=draw;
  $("jump").onchange=()=>{if($("jump").value!==""){center=[...data.controls[Number($("jump").value)].pixel];zoom=5;clampCenter();draw();}};
  const pair=(left,right)=>{$("left").value=left;$("right").value=right;draw();};
  $("noiseLight").onclick=()=>pair("vinevi_x2","vinevi_noise_light_x2");
  $("noiseMedium").onclick=()=>pair("vinevi_x2","vinevi_noise_medium_x2");
  $("process").onclick=()=>pair("original_x2","vinevi_x2");
  $("processCompare").onclick=()=>pair("vinevi_previous_x2","vinevi_x2");
  $("upscale").onclick=()=>pair("original_x2","anime_faithful_x2");
  $("capture").onclick=()=>pair("original_x2","blender_styled_x2");
  $("compare").onclick=()=>pair("anime_faithful_x2","blender_styled_x2");
  for (const canvas of document.querySelectorAll("canvas")) {
    const position = event => {
      const bounds=canvas.getBoundingClientRect();
      return [(event.clientX-bounds.left)/bounds.width,(event.clientY-bounds.top)/bounds.height];
    };
    const worldAt = event => position(event).map((x,i)=>center[i]+(x-.5)*1024/zoom);
    canvas.onpointerdown=event=>{dragging={point:position(event),center:[...center]};canvas.setPointerCapture(event.pointerId);};
    canvas.onpointerup=()=>{dragging=null;};
    canvas.onpointercancel=()=>{dragging=null;};
    canvas.onpointerleave=()=>{if(!dragging){cursor=null;draw();}};
    canvas.onpointermove=event=>{
      if(dragging){const p=position(event);center=p.map((x,i)=>dragging.center[i]-(x-dragging.point[i])*1024/zoom);clampCenter();}
      cursor=worldAt(event);draw();
    };
    canvas.addEventListener("wheel",event=>{
      event.preventDefault();const anchor=worldAt(event),p=position(event);
      zoom=Math.max(1,Math.min(6,zoom*Math.exp(-event.deltaY*.001)));
      center=p.map((x,i)=>anchor[i]-(x-.5)*1024/zoom);clampCenter();draw();
    },{passive:false});
  }
  document.addEventListener("keydown",event=>{
    if(event.target.closest("input,select,textarea")||event.ctrlKey||event.altKey||event.metaKey)return;
    if(event.key===" "){event.preventDefault();blink=true;draw();}
    if(event.key.toLowerCase()==="l"){$("geometry").checked=!$("geometry").checked;draw();}
    if(["1","2","3"].includes(event.key))setView({1:"full",2:"town",3:"islands"}[event.key]);
  });
  document.addEventListener("keyup",event=>{if(event.key===" "){blink=false;draw();}});
  window.addEventListener("blur",()=>{blink=false;dragging=null;draw();});
  $("metrics").textContent=`All outputs: 1024×1024 · 64 world units/pixel · ${data.blender_projection.vertex_controls} model vertices checked · `+
    `camera projection error: ${data.blender_projection.max_projection_error_x2_pixels} px. Whole-frame ESRGAN translation: 0 px; local detail changes still require visual judgment.`;
  draw();document.body.dataset.ready="true";
})().catch(error=>{document.getElementById("metrics").textContent="Could not load comparison: "+error.message;console.error(error);});
