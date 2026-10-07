#ifndef OPENYAMM_AMBIENT_OCCLUSION_SH
#define OPENYAMM_AMBIENT_OCCLUSION_SH

SAMPLER2D(s_aoDepth, 0);
uniform mat4 u_aoInverseProjection;
uniform vec4 u_aoDepthParams;
uniform vec4 u_aoParams;
uniform vec4 u_aoTexel;

vec3 aoViewPosition(vec2 uv, float depth)
{
    vec2 xy = uv * 2.0 - 1.0;
    xy.y *= u_aoDepthParams.z;
    vec4 position = mul(u_aoInverseProjection, vec4(xy,
        depth * u_aoDepthParams.x + u_aoDepthParams.y, 1.0));
    return position.xyz / position.w;
}

float aoDepthWeight(float center, float neighbor)
{
    float delta = abs(center - neighbor) / max(1.0, center * 0.002);
    return exp(-delta * delta);
}

#endif
