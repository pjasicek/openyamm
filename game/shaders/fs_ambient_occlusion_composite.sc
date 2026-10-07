$input v_texcoord0
#include "common.sh"
#include "ambient_occlusion.sh"
SAMPLER2D(s_ao, 1);

void main()
{
    float depth = texture2D(s_aoDepth, v_texcoord0).r;
    float distance = -aoViewPosition(v_texcoord0, depth).z;
    vec2 pixel = v_texcoord0 / u_aoTexel.zw - 0.5;
    vec2 base = (floor(pixel) + 0.5) * u_aoTexel.zw;
    vec2 fraction = fract(pixel);
    float total = 0.0;
    float weights = 0.0;
    for (int y = 0; y < 2; ++y)
    {
        for (int x = 0; x < 2; ++x)
        {
            vec2 offset = vec2(float(x), float(y));
            vec2 sampleValue = texture2D(s_ao, base + offset * u_aoTexel.zw).rg;
            vec2 blend = mix(1.0 - fraction, fraction, offset);
            float weight = blend.x * blend.y * aoDepthWeight(distance, sampleValue.y);
            total += sampleValue.x * weight;
            weights += weight;
        }
    }
    float visibility = weights > 0.0001 && depth < 0.999999 ? total / weights : 1.0;
    // ponytail: SDR composite attenuates all solid lighting, not just indirect light.
    // Approximate gamma-2.2 attenuation avoids another full-resolution colour copy;
    // use an indirect-light buffer if a future HDR lighting pipeline needs physical AO.
    float factor = pow(mix(1.0, visibility, u_aoParams.z), 1.0 / 2.2);
    gl_FragColor = vec4(vec3(factor), 1.0);
}
