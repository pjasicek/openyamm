export const add = (a, b) => a.map((v, i) => v + b[i]);
export const sub = (a, b) => a.map((v, i) => v - b[i]);
export const mul = (a, s) => a.map(v => v * s);
export const dot = (a, b) => a.reduce((v, x, i) => v + x * b[i], 0);
export const length = a => Math.hypot(...a);
export const unit = (a, fallback = [0, 1, 0]) => length(a) > 1e-8 ? mul(a, 1 / length(a)) : [...fallback];
export const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
export const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const identity = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
export function matrixMultiply(a, b)
{
    const r = Array(16).fill(0);
    for (let c = 0; c < 4; ++c)
        for (let y = 0; y < 4; ++y)
            for (let k = 0; k < 4; ++k) r[c*4+y] += a[k*4+y] * b[c*4+k];
    return r;
}
export function transform(m, p, w = 1)
{
    return [0, 1, 2].map(i => m[i]*p[0] + m[4+i]*p[1] + m[8+i]*p[2] + m[12+i]*w);
}
export function quaternionMatrix(q, position = [0, 0, 0], scale = 1)
{
    const [x, y, z, w] = q;
    return [(1-2*y*y-2*z*z)*scale, (2*x*y+2*w*z)*scale, (2*x*z-2*w*y)*scale, 0,
        (2*x*y-2*w*z)*scale, (1-2*x*x-2*z*z)*scale, (2*y*z+2*w*x)*scale, 0,
        (2*x*z+2*w*y)*scale, (2*y*z-2*w*x)*scale, (1-2*x*x-2*y*y)*scale, 0,
        ...position, 1];
}
export function slerp(a, b, t)
{
    let cosine = dot(a, b);
    if (cosine < 0) { b = mul(b, -1); cosine = -cosine; }
    if (cosine > 0.9995) return unit(mix(a, b, t), [0, 0, 0, 1]);
    const angle = Math.acos(clamp(cosine, -1, 1));
    return add(mul(a, Math.sin((1-t)*angle)/Math.sin(angle)), mul(b, Math.sin(t*angle)/Math.sin(angle)));
}
export function axisRotate(v, rotation)
{
    const angle = length(rotation);
    if (angle < 1e-9) return [...v];
    const n = mul(rotation, 1 / angle), c = Math.cos(angle), s = Math.sin(angle);
    return add(add(mul(v, c), mul(cross(n, v), s)), mul(n, dot(n, v)*(1-c)));
}
export function directionMatrix(direction = [0, 0, 1], position = [0, 0, 0], scale = 1)
{
    const forward = unit(direction, [0, 0, 1]);
    const right = unit(cross(Math.abs(forward[1]) > .99 ? [1, 0, 0] : [0, 1, 0], forward));
    const up = cross(forward, right);
    return [...mul(right, scale), 0, ...mul(up, scale), 0, ...mul(forward, scale), 0, ...position, 1];
}
export function perspective(fov, aspect, near, far)
{
    const f = 1 / Math.tan(fov / 2);
    return [f/aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far+near)/(near-far), -1,
        0, 0, 2*far*near/(near-far), 0];
}
export function lookAt(eye, target)
{
    const z = unit(sub(eye, target)), x = unit(cross([0, 1, 0], z)), y = cross(z, x);
    return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
        -dot(x, eye), -dot(y, eye), -dot(z, eye), 1];
}
