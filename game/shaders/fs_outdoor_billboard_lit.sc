$input v_texcoord0, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_billboardAmbient;
uniform vec4 u_billboardOverrideColor;
uniform vec4 u_billboardOutlineParams;

float sampleBillboardAlpha(vec2 uv)
{
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
    {
        return 0.0;
    }

    return texture2D(s_texColor, uv).a * v_color0.a;
}

void main()
{
    vec4 textureColor =
        (v_texcoord0.x < 0.0 || v_texcoord0.x > 1.0 || v_texcoord0.y < 0.0 || v_texcoord0.y > 1.0)
            ? vec4(0.0, 0.0, 0.0, 0.0)
            : texture2D(s_texColor, v_texcoord0);
    vec3 litColor = textureColor.rgb * (u_billboardAmbient.rgb + v_color0.rgb);
    vec4 shadedColor = vec4(litColor, textureColor.a * v_color0.a);
    float baseAlpha = shadedColor.a;

    if (u_billboardOverrideColor.a > 0.001 && u_billboardOutlineParams.z > 0.001)
    {
        float outlineAlpha = 0.0;
        float enable1 = step(1.0, u_billboardOutlineParams.z + 0.001);
        float enable2 = step(2.0, u_billboardOutlineParams.z + 0.001);
        float enable3 = step(3.0, u_billboardOutlineParams.z + 0.001);
        float enable4 = step(4.0, u_billboardOutlineParams.z + 0.001);
        vec2 texel = u_billboardOutlineParams.xy;

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, 0.0)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, 0.0)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, texel.y)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, texel.y)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, -texel.y)) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, -texel.y)) * enable1);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, 0.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, 0.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 2.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 2.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, texel.y * 2.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, texel.y * 2.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, -texel.y * 2.0)) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, -texel.y * 2.0)) * enable2);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, 0.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, 0.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 3.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 3.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, texel.y * 3.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, texel.y * 3.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, -texel.y * 3.0)) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, -texel.y * 3.0)) * enable3);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, 0.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, 0.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 4.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 4.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, texel.y * 4.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, texel.y * 4.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, -texel.y * 4.0)) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, -texel.y * 4.0)) * enable4);

        if (baseAlpha <= 0.001 && outlineAlpha > 0.001)
        {
            gl_FragColor = vec4(u_billboardOverrideColor.rgb, outlineAlpha * u_billboardOverrideColor.a);
            return;
        }
    }

    gl_FragColor = shadedColor;
}
