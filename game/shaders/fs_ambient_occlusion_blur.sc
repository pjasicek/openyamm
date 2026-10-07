$input v_texcoord0
#include "common.sh"
#include "ambient_occlusion.sh"
SAMPLER2D(s_ao, 1);

void main()
{
    vec2 center = texture2D(s_ao, v_texcoord0).rg;
    float total = 0.0;
    float weights = 0.0;
    for (int y = -1; y <= 1; ++y)
    {
        for (int x = -1; x <= 1; ++x)
        {
            vec2 sampleValue = texture2D(s_ao, v_texcoord0 + vec2(float(x), float(y)) * u_aoTexel.zw).rg;
            float weight = exp(-float(x * x + y * y) * 0.5) * aoDepthWeight(center.y, sampleValue.y);
            total += sampleValue.x * weight;
            weights += weight;
        }
    }
    gl_FragColor = vec4(total / max(weights, 0.0001), center.y, 0.0, 1.0);
}
