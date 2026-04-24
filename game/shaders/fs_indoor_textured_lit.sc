$input v_texcoord0, v_worldPosition

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_indoorLightPositions[40];
uniform vec4 u_indoorLightColors[40];
uniform vec4 u_indoorLightParams;

vec3 getIndoorLighting()
{
    vec3 lighting = vec3(u_indoorLightParams.y);

    for (int i = 0; i < 40; ++i)
    {
        if (float(i) >= u_indoorLightParams.x)
        {
            continue;
        }

        vec3 toLight = u_indoorLightPositions[i].xyz - v_worldPosition;
        float radius = max(u_indoorLightPositions[i].w, 1.0);
        float dist = length(toLight);
        float ratio = clamp(dist / radius, 0.0, 1.0);
        float attenuation = 1.0 - ratio * ratio;
        attenuation *= attenuation;
        lighting += u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w * attenuation * u_indoorLightParams.z);
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

    gl_FragColor = vec4(textureColor.rgb * getIndoorLighting(), textureColor.a);
}
