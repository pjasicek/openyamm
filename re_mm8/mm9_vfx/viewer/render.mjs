import {add, sub, mul, unit, cross, dot, clamp, identity, transform, matrixMultiply,
    perspective, lookAt, directionMatrix} from './math.mjs';
import {assetName, modelPose} from './simulation.mjs';

export class Renderer
{
    constructor(canvas)
    {
        this.canvas = canvas;
        this.gl = canvas.getContext('webgl2', {alpha: false, antialias: true, preserveDrawingBuffer: true});
        if (!this.gl) throw new Error('WebGL 2 is unavailable. Open this viewer in Chrome or Firefox with graphics enabled.');
        const gl = this.gl;
        const vertex = `#version 300 es
            in vec3 position; in vec2 uv; in vec4 color;
            uniform mat4 vp; out vec2 texcoord; out vec4 tint;
            void main() { gl_Position = vp*vec4(position,1.0); texcoord=uv; tint=color; }`;
        const fragment = `#version 300 es
            precision highp float;
            in vec2 texcoord; in vec4 tint; uniform sampler2D source; uniform bool textureAlpha;
            out vec4 outputColor;
            void main() { vec4 pixel = texture(source,texcoord);
                if(!textureAlpha) pixel.a = 1.0;
                outputColor = pixel*tint; if(outputColor.a<0.002) discard; }`;
        const compile = (kind, text) =>
        {
            const shader = gl.createShader(kind);
            gl.shaderSource(shader, text); gl.compileShader(shader);
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
            return shader;
        };
        this.program = gl.createProgram();
        gl.attachShader(this.program, compile(gl.VERTEX_SHADER, vertex));
        gl.attachShader(this.program, compile(gl.FRAGMENT_SHADER, fragment));
        gl.linkProgram(this.program);
        if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(this.program));
        gl.useProgram(this.program);
        this.vp = gl.getUniformLocation(this.program, 'vp');
        this.textureAlpha = gl.getUniformLocation(this.program, 'textureAlpha');
        this.buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
        for (const [name, count, offset] of [['position', 3, 0], ['uv', 2, 12], ['color', 4, 20]])
        {
            const location = gl.getAttribLocation(this.program, name);
            gl.enableVertexAttribArray(location);
            gl.vertexAttribPointer(location, count, gl.FLOAT, false, 36, offset);
        }
        this.white = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, this.white);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
            new Uint8Array([255, 255, 255, 255]));
        this.textures = new Map();
        this.yaw = .35; this.pitch = .15; this.distance = 480; this.target = [0, 65, 0];
        this.installCamera();
    }
    async loadTexture(name)
    {
        if (this.textures.has(name)) return this.textures.get(name);
        const gl = this.gl;
        const response = await fetch('/api/texture?name='+encodeURIComponent(name));
        if (!response.ok) throw new Error(`Texture unavailable: ${name}`);
        const bitmap = await createImageBitmap(await response.blob(), {premultiplyAlpha: 'none', colorSpaceConversion: 'none'});
        const texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bitmap);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
        const result = {texture, width: bitmap.width, height: bitmap.height};
        bitmap.close();
        this.textures.set(name, result);
        return result;
    }
    installCamera()
    {
        let drag = null;
        this.canvas.oncontextmenu = event => event.preventDefault();
        this.canvas.onpointerdown = event =>
        {
            drag = {x: event.clientX, y: event.clientY, pan: event.button !== 0 || event.shiftKey};
            this.canvas.setPointerCapture(event.pointerId);
        };
        this.canvas.onpointerup = () => { drag = null; };
        this.canvas.onpointermove = event =>
        {
            if (!drag) return;
            const dx = event.clientX-drag.x, dy = event.clientY-drag.y;
            if (drag.pan)
            {
                this.target[0] -= dx*this.distance*.0015*Math.cos(this.yaw);
                this.target[2] += dx*this.distance*.0015*Math.sin(this.yaw);
                this.target[1] += dy*this.distance*.0015;
            }
            else { this.yaw -= dx*.008; this.pitch = clamp(this.pitch+dy*.008, -1.4, 1.4); }
            drag.x = event.clientX; drag.y = event.clientY;
        };
        this.canvas.addEventListener('wheel', event =>
        {
            event.preventDefault(); this.distance = clamp(this.distance*Math.exp(event.deltaY*.001), 15, 8000);
        }, {passive: false});
    }
    resetCamera() { this.yaw = .35; this.pitch = .15; this.distance = 480; this.target = [0, 65, 0]; }
    draw(vertices, texture = this.white, blend = false, primitive = this.gl.TRIANGLES, textureAlpha = true)
    {
        if (!vertices.length) return;
        const gl = this.gl;
        gl.uniform1i(this.textureAlpha, textureAlpha);
        if (blend)
        {
            gl.enable(gl.BLEND);
            gl.blendFunc(blend === 'multiply' ? gl.DST_COLOR : blend === 'add' ? gl.ONE : gl.SRC_ALPHA,
                blend === 'multiply' ? gl.ZERO : ['add', 'authoredAdd'].includes(blend) ? gl.ONE : gl.ONE_MINUS_SRC_ALPHA);
        }
        else gl.disable(gl.BLEND);
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STREAM_DRAW);
        gl.drawArrays(primitive, 0, vertices.length/9);
        ++this.drawCalls;
    }
    mesh(model, pose, matrix, color, texture, helper = false)
    {
        if (!model || !pose) return;
        const vertices = [];
        for (const piece of model.pieces)
        {
            const points = piece.vertices.map(v =>
            {
                if (!v.weights.length) return transform(matrix, v.position);
                let p = [0, 0, 0];
                for (const [node, weight] of v.weights)
                    p = add(p, mul(transform(pose.skin[node], v.position), weight));
                return transform(matrix, p);
            });
            for (const face of piece.faces)
            {
                if (helper)
                {
                    for (let i = 0; i < 3; ++i)
                        for (const corner of [face[i], face[(i+1)%3]])
                            vertices.push(...points[corner[2]], 0, 0, ...color);
                }
                else for (const [u, v, index] of face) vertices.push(...points[index], u, v, ...color);
            }
        }
        this.draw(vertices, texture ?? this.white, color[3] < .999 ? 'normal' : false,
            helper ? this.gl.LINES : this.gl.TRIANGLES, false);
    }
    render(sim, sprites, options = {})
    {
        const gl = this.gl, canvas = this.canvas, ratio = Math.min(devicePixelRatio, 2);
        const width = Math.round(canvas.clientWidth*ratio), height = Math.round(canvas.clientHeight*ratio);
        if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
        gl.viewport(0, 0, width, height);
        const backgrounds = {slate: [.055, .069, .085], black: [0, 0, 0], stone: [.22, .20, .17]};
        gl.clearColor(...(backgrounds[options.background] ?? backgrounds.slate), 1);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL); gl.depthMask(true); gl.disable(gl.CULL_FACE);
        gl.useProgram(this.program);
        this.drawCalls = 0;
        const eye = add(this.target, [Math.sin(this.yaw)*Math.cos(this.pitch)*this.distance,
            Math.sin(this.pitch)*this.distance, Math.cos(this.yaw)*Math.cos(this.pitch)*this.distance]);
        const view = lookAt(eye, this.target);
        gl.uniformMatrix4fv(this.vp, false, matrixMultiply(perspective(Math.PI/3, width/height, 1, 20000), view));
        const right = [view[0], view[4], view[8]], up = [view[1], view[5], view[9]];
        if (options.grid)
        {
            const lines = [], gray = [.19, .23, .27, 1];
            const segment = (a, b, color) => lines.push(...a, 0, 0, ...color, ...b, 0, 0, ...color);
            for (let v = -500; v <= 500; v += 50)
            {
                segment([v, -1, -500], [v, -1, 500], gray);
                segment([-500, -1, v], [500, -1, v], gray);
            }
            segment([0, 0, 0], [100, 0, 0], [.6, .22, .19, 1]);
            segment([0, 0, 0], [0, 100, 0], [.2, .55, .32, 1]);
            segment([0, 0, 0], [0, 0, 100], [.25, .4, .7, 1]);
            this.draw(lines, this.white, false, gl.LINES);
        }
        if (!sim) return;
        if (options.monk && sim.target)
            this.mesh(sim.target, sim.targetPose, sim.targetMatrix, [1, 1, 1, 1],
                this.textures.get('skins/monk1.dtx')?.texture);
        for (const c of sim.components)
            if (c.active && c.type === 'Model' && c.model)
            {
                const skin = this.textures.get(assetName(c.p.Skin));
                if (skin || options.helpers)
                {
                    gl.depthMask(c.color[3] >= .999);
                    this.mesh(c.model, c.pose, c.matrix, c.color, skin?.texture, !skin);
                }
            }
        gl.depthMask(false);
        const quads = [];
        for (const c of sim.components)
        {
            if (!c.active || !['SpriteSystem', 'Sprite'].includes(c.type)) continue;
            const sprite = sprites[assetName(c.p.Sprite)];
            if (!sprite) continue;
            const particles = c.type === 'SpriteSystem' ? c.particles
                : [{position: c.position, color: c.color, scale: c.scale, animationMs: (sim.time-c.born)*1000}];
            for (const p of particles)
            {
                const frame = Math.floor(p.animationMs/sprite.frame_ms) % sprite.frames.length;
                const tex = this.textures.get(sprite.frames[frame]);
                if (!tex || p.color[3] <= 0) continue;
                let x = right, y = up;
                const facing = c.type === 'Sprite' ? Number(Boolean(c.p.Facing)) : (c.p.Facing ?? 0);
                if (facing)
                {
                    const basis = directionMatrix(facing === 3 ? c.p.FacingDir : c.p.PlaneDir ?? c.p.Normal);
                    x = basis.slice(0, 3); y = basis.slice(4, 7);
                }
                if (c.p.PlaneRight) { x = unit(c.p.PlaneRight); y = unit(c.p.PlaneUp); }
                // Authored descriptors specify full logical extents; native FXF uses texture half extents.
                const halfX = p.scale*(sprite.logicalWidth ? sprite.logicalWidth/2 : tex.width)*(c.p.StretchU ?? 1);
                const halfY = p.scale*(sprite.logicalHeight ? sprite.logicalHeight/2 : tex.height)*(c.p.StretchV ?? 1);
                quads.push({p, x: mul(x, halfX), y: mul(y, halfY), tex,
                    blend: c.p.Blend ? ({alpha: 'normal', additive: 'authoredAdd', multiply: 'multiply'}[c.p.Blend])
                        : c.type === 'Sprite' || c.p.AType === 1 ? 'add' : 'normal',
                    depth: -transform(view, p.position)[2]});
            }
        }
        quads.sort((a, b) => b.depth-a.depth);
        let vertices = [], texture = null, blend = null;
        for (const q of quads)
        {
            if (texture !== q.tex.texture || blend !== q.blend)
            {
                this.draw(vertices, texture, blend); vertices = []; texture = q.tex.texture; blend = q.blend;
            }
            const corners = [sub(sub(q.p.position, q.x), q.y), add(sub(q.p.position, q.y), q.x),
                add(add(q.p.position, q.x), q.y), add(sub(q.p.position, q.x), q.y)];
            const uv = [[0, 1], [1, 1], [1, 0], [0, 0]];
            for (const i of [0, 1, 2, 0, 2, 3]) vertices.push(...corners[i], ...uv[i], ...q.p.color);
        }
        this.draw(vertices, texture, blend);
        gl.depthMask(true);
    }
}
