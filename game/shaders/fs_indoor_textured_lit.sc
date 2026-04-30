$input v_texcoord0, v_worldPosition, v_texcoord1, v_screenspace

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;
uniform vec4 u_secretPulseParams;

vec3 getIndoorLighting()
{
    vec3 lighting = u_indoorLightParams.yzw;

    for (int i = 0; i < 12; ++i)
    {
        if (float(i) >= u_indoorLightParams.x)
        {
            break;
        }

        vec3 toLight = u_indoorLightPositions[i].xyz - v_worldPosition;
        float radius = max(u_indoorLightPositions[i].w, 1.0);
        float distanceSquared = dot(toLight, toLight);
        float inverseRadiusSquared = 1.0 / (radius * radius);
        float attenuation = 1.0 - clamp(distanceSquared * inverseRadiusSquared, 0.0, 1.0);
        attenuation *= attenuation;
        lighting += u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w * attenuation);
    }

    return clamp(lighting, vec3(0.0), vec3(2.0));
}

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);

    if (textureColor.a <= 0.001)
    {
        discard;
    }

    vec3 color = textureColor.rgb * getIndoorLighting();

    if (v_texcoord1.x > 0.5 && u_secretPulseParams.x > 0.5)
    {
        float pulse = 0.5 + 0.5 * sin(u_secretPulseParams.y * 4.0);
        vec3 secretTint = color * vec3(1.0, pulse, pulse);
        float edgeMask = floor(v_screenspace + 0.5);
        float boundaryFade = 1.0;

        if (mod(edgeMask, 2.0) >= 1.0)
        {
            float edgeWidth = max(fwidth(v_texcoord1.y) * 8.0, 0.004);
            boundaryFade = min(boundaryFade, smoothstep(edgeWidth, edgeWidth * 2.5, v_texcoord1.y));
        }

        if (mod(floor(edgeMask / 2.0), 2.0) >= 1.0)
        {
            float edgeWidth = max(fwidth(v_texcoord1.z) * 8.0, 0.004);
            boundaryFade = min(boundaryFade, smoothstep(edgeWidth, edgeWidth * 2.5, v_texcoord1.z));
        }

        if (mod(floor(edgeMask / 4.0), 2.0) >= 1.0)
        {
            float edgeWidth = max(fwidth(v_texcoord1.w) * 8.0, 0.004);
            boundaryFade = min(boundaryFade, smoothstep(edgeWidth, edgeWidth * 2.5, v_texcoord1.w));
        }

        color = mix(color, secretTint, boundaryFade);
    }

    gl_FragColor = vec4(color, textureColor.a);
}
