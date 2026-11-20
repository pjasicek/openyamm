"""Exercise the actual shared viewer drawing code against the runtime billboard equations."""
import json
from pathlib import Path
import subprocess
import unittest


class ViewerPlacementTests(unittest.TestCase):
    def test_action_transition_keeps_fractional_time_and_draws_immediately(self):
        template = (Path(__file__).parent / 'mm6_peasants/viewer.html').read_text()
        ticking = template[template.index('function tick(now)'):template.index('const initial=')]
        script = r'''
const assert=require('node:assert/strict');
const controls={speed:{value:1},loop:{checked:false},action:{value:'attack'},
 native:{},enhanced:{},status:{}};
const $=id=>controls[id];
const step=(name,duration)=>({frame:name,duration_ms:duration,native_scale:1,mirrored:false});
const animation={attack:{next_action:'standing',views:{0:[step('attack',62.5)]}},
 standing:{playback:'loop',views:{0:[step('standA',62.5),step('standB',62.5)]}},
 death:{next_action:'corpse',views:{0:[step('death',62.5)]}},
 corpse:{views:{0:[]}}};
const actions=()=>animation,seq=()=>animation[controls.action.value].views[0];
let elapsed=60,last=0,playing=true,frame=0,drawn=[];
const draw=(canvas,s)=>drawn.push(s?.frame??null),requestAnimationFrame=()=>{};
'''+ticking+r'''
tick(16);
assert.equal(controls.action.value,'standing');
assert.equal(elapsed,13.5);
assert.deepEqual(drawn,['standA','standA']);
tick(66);
assert.equal(frame,1);assert.equal(elapsed,63.5);
controls.action.value='death';elapsed=60;last=66;drawn=[];
tick(82);
assert.equal(controls.action.value,'corpse');
assert.deepEqual(drawn,[null,null]);
controls.action.value='attack';controls.loop.checked=true;elapsed=60;last=82;
tick(98);
assert.equal(controls.action.value,'attack');assert.equal(elapsed,13.5);
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_family_fit_includes_largest_variant_and_mirrors(self):
        template = (Path(__file__).parent / 'mm6_peasants/viewer.html').read_text()
        fitting = template[template.index('function familyFitZoom'):template.index('function fitFamily')]
        script = r'''
const assert=require('node:assert/strict');
const manifest={logical_canvas:[700,500],logical_pivot:[350,500],pixels_per_logical_pixel:2,
 anchor:'bottom-center',frames:{pose:{crop_origin_px:[-40,20],atlas_xywh:[0,0,1480,990],
 native_offset:[0,0],source_canvas:[700,500]}},animations_by_palette:{
 'small':{walk:{views:{'0':[{frame:'pose',native_scale:.5,mirrored:false}]}}},
 'large':{walk:{views:{'0':[{frame:'pose',native_scale:3,mirrored:false}],
 '7':[{frame:'pose',native_scale:3,mirrored:true}]}}}}};
'''+fitting+r'''
// Large variant extends 370 native pixels left of the actor, mirrored to the right.
// At scale 3, 330 available viewport pixels require <= 330/1110, rounded down to .29.
assert.equal(familyFitZoom(),.29);
for(const mirrored of [false,true])for(const x of [-370,370]){
 const screen=350+x*3*.29*(mirrored?-1:1);
 assert.ok(screen>=20 && screen<=680);
}
assert.ok(530-500*3*.29>=40);
assert.ok(530+5*3*.29<=580);
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_exported_and_native_draw_coordinates(self):
        template = (Path(__file__).parent / 'mm6_peasants/viewer.html').read_text()
        drawing = template[template.index('function drawNative'):template.index('function tick')]
        script = r'''
const assert = require('node:assert/strict');
const controls = {zoom:{value:1},bg:{value:'#000000'},mask:{checked:false},
    overlay:{checked:false},crop:{checked:false},palette:{value:'1'}};
const $ = id => controls[id];
const img = () => ({complete:true,naturalWidth:370});
const manifest = {logical_canvas:[370,400], logical_pivot:[185,400],
    pixels_per_logical_pixel:2, anchor:'bottom-center',
    pages:[{variant_previews:{'1':'base.png'}}],frames:{pose:{page:0,
        source_canvas:[243,281],native_offset:[63.5,119],
        crop_origin_px:[-19,37],atlas_xywh:[17,23,487,589]}}};
let calls=[],scale,translation;
const context={fillRect(){},fillText(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},
    save(){},restore(){},translate(x,y){translation=[x,y]},scale(x,y){scale=[x,y]},
    drawImage(...args){calls.push(args.slice(1))}};
const canvas={getContext:()=>context};
'''+drawing+r'''
for(const mirrored of [false,true])for(const nativeScale of [.699997,1,2.799988]){
    const step={frame:'pose',mirrored,native_scale:nativeScale};
    calls=[];draw(canvas,step,false);
    const [sx,sy,w,h,x,y,dw,dh]=calls[0];
    assert.deepEqual([sx,sy,w,h],[17,23,487,589]);
    const sign=mirrored?-1:1;
    assert.deepEqual(scale,[sign*nativeScale,nativeScale]);
    // SpriteAtlasCache.cpp loads logical size and texture offsets; the
    // SpriteAtlasCache.h billboard helper mirrors its horizontal center.
    const textureWidth=487/2, textureHeight=589/2;
    const offsetX=(-19+487*.5)/2-185, offsetY=400-(37+589)/2;
    const centerX=sign*offsetX*nativeScale;
    const centerY=-(textureHeight*.5+offsetY)*nativeScale;
    assert.ok(Math.abs((x+dw*.5)*scale[0]-centerX)<1e-9);
    assert.ok(Math.abs((y+dh*.5)*scale[1]-centerY)<1e-9);
    assert.equal(dw,textureWidth);assert.equal(dh,textureHeight);
    calls=[];draw(canvas,step,true);
    assert.deepEqual(calls[0],[63,119,243,281,-121.5,-281,243,281]);
    assert.deepEqual(scale,[sign*nativeScale,nativeScale]);
}
controls.overlay.checked=true;calls=[];
draw(canvas,{frame:'pose',native_scale:1,mirrored:false},false);
assert.equal(calls.length,2);
console.log('Runtime-equivalent centers, native half-pixels, scale, mirrors and overlay passed');
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
