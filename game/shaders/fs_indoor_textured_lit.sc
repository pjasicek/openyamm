$input v_texcoord0, v_worldPosition, v_texcoord1

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
        color *= vec3(1.0, pulse, pulse);
    }

    gl_FragColor = vec4(color, textureColor.a);
}
