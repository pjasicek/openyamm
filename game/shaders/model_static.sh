// Static model placements (decorations): instance data holds the affine matrix rows (i_data0..2), the placement
// light (i_data3) and the point light plus LOD crossfade (i_data4).
// [0] time seconds, wind amplitude (model units), model height (model units), billboard flag
// [1] texture scroll u, v per second, flipbook columns, rows; [2] flipbook frames per second, flutter amplitude,
// emission pulse amplitude and period (seconds)
uniform vec4 u_modelStatic[3];

mat4 modelStaticMatrix()
{
    return mtxFromRows(i_data0, i_data1, i_data2, vec4(0.0, 0.0, 0.0, 1.0));
}

// Per-placement phase from its position, so neighbouring decorations do not animate in step.
float modelStaticPhase()
{
    return fract(sin(dot(vec2(i_data0.w, i_data1.w), vec2(0.0129898, 0.078233))) * 43758.5453);
}

// Animated texture coordinates: scrolling, or the current flipbook frame.
vec2 modelStaticTexcoord(vec2 texcoord)
{
    texcoord += u_modelStatic[1].xy * u_modelStatic[0].x;
    if (u_modelStatic[1].z > 0.5)
    {
        float frames = u_modelStatic[1].z * u_modelStatic[1].w;
        float frame = floor(mod(u_modelStatic[0].x * u_modelStatic[2].x + modelStaticPhase() * frames, frames));
        vec2 cell = vec2(mod(frame, u_modelStatic[1].z), floor(frame / u_modelStatic[1].z));
        texcoord = (cell + texcoord) / u_modelStatic[1].zw;
    }
    return texcoord;
}

// Emission scale of a pulsing material (1 without a pulse), out of step between placements.
float modelStaticPulse()
{
    if (u_modelStatic[2].z <= 0.0)
    {
        return 1.0;
    }
    return 1.0 + u_modelStatic[2].z * sin(6.2831853 * (u_modelStatic[0].x / u_modelStatic[2].w + modelStaticPhase()));
}

// Cloth flutter (vertex colour alpha = how free the vertex is; a wave travels along texture coordinate u).
vec3 modelStaticFlutter(vec3 position, vec3 normal, vec2 texcoord, float freedom)
{
    float wave = sin(u_modelStatic[0].x * 7.0 - texcoord.x * 9.0 + modelStaticPhase() * 6.2831853)
        + 0.35 * sin(u_modelStatic[0].x * 11.3 - texcoord.x * 15.0);
    return position + normal * (u_modelStatic[2].y * freedom * wave);
}

vec3 modelStaticPosition(vec3 position, vec3 cameraPosition)
{
    mat4 model = modelStaticMatrix();
    vec3 origin = vec3(i_data0.w, i_data1.w, i_data2.w);
    vec3 world = mul(model, vec4(position, 1.0)).xyz;
    float scale = length(mul(model, vec4(1.0, 0.0, 0.0, 0.0)).xyz);
    if (u_modelStatic[0].w > 0.5)
    {
        // Impostor quad in the model's across/up plane: turn it about the vertical axis toward the camera.
        vec3 across = mul(model, vec4(1.0, 0.0, 0.0, 0.0)).xyz / max(scale, 0.0001);
        vec3 offset = world - origin;
        vec2 toCamera = cameraPosition.xy - origin.xy;
        toCamera *= inversesqrt(max(dot(toCamera, toCamera), 0.0001));
        world = origin + vec3(-toCamera.y, toCamera.x, 0.0) * dot(offset, across) + vec3(0.0, 0.0, offset.z);
    }
    if (u_modelStatic[0].y > 0.0)
    {
        // Sway grows with height squared; a slow bend plus a faster flutter that varies across the crown.
        float height = clamp((world.z - origin.z) / max(u_modelStatic[0].z * scale, 0.0001), 0.0, 1.5);
        // The phase follows the placement's position, so gusts roll across a stand of trees.
        float phase = u_modelStatic[0].x * 1.1 + dot(origin.xy, vec2(0.0021, 0.0013));
        vec2 bend = vec2(sin(phase), cos(phase * 0.83)) * 0.7;
        float flutterPhase = u_modelStatic[0].x * 3.3 + dot(world.xy, vec2(0.011, 0.013));
        vec2 flutter = vec2(sin(flutterPhase), cos(flutterPhase * 1.27)) * 0.3;
        world.xy += (bend + flutter) * u_modelStatic[0].y * scale * height * height;
    }
    return world;
}

vec3 modelStaticNormal(vec3 normal, vec3 cameraPosition)
{
    if (u_modelStatic[0].w > 0.5)
    {
        vec2 toCamera = cameraPosition.xy - vec2(i_data0.w, i_data1.w);
        toCamera *= inversesqrt(max(dot(toCamera, toCamera), 0.0001));
        return vec3(toCamera, 0.0);
    }
    return normalize(mul(modelStaticMatrix(), vec4(normal, 0.0)).xyz);
}
