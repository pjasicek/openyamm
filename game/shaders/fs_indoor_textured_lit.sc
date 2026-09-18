$input v_texcoord0, v_worldPosition, v_worldNormal, v_texcoord1, v_screenspace, v_flowInfo, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;
uniform vec4 u_secretPulseParams;
uniform vec4 u_indoorSkyParams;
uniform vec4 u_indoorSkyProjectionParams;
uniform vec4 u_cameraPosition;

#define MATERIAL_INDOOR_RESPONSE 1
#include "material_lighting.sh"

vec3 getIndoorLighting(vec3 worldPosition, vec3 vertexLighting)
{
    vec3 lighting = u_indoorLightParams.yzw + vertexLighting * 2.0;

    for (int i = 0; i < 12; ++i)
    {
        if (float(i) >= u_indoorLightParams.x)
        {
            break;
        }

        vec3 toLight = u_indoorLightPositions[i].xyz - worldPosition;
        float radius = max(u_indoorLightPositions[i].w, 1.0);
        float distanceSquared = dot(toLight, toLight);
        float inverseRadiusSquared = 1.0 / (radius * radius);
        float attenuation = 1.0 - clamp(distanceSquared * inverseRadiusSquared, 0.0, 1.0);
        attenuation *= attenuation;
        lighting += u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w * attenuation);
    }

    return clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0));
}

void main()
{
    vec2 texcoord = v_texcoord0;

    if (v_flowInfo.w < -1.5)
    {
        float screenY = u_viewRect.w - gl_FragCoord.y;
        float xDistance = (u_indoorSkyProjectionParams.x - gl_FragCoord.x) * u_indoorSkyProjectionParams.z;
        float yDistance = (u_indoorSkyProjectionParams.y - screenY) * u_indoorSkyProjectionParams.z;
        float cosYaw = cos(u_indoorSkyParams.z);
        float sinYaw = sin(u_indoorSkyParams.z);
        float oePitch = -u_indoorSkyParams.w;
        float cosPitch = cos(oePitch);
        float sinPitch = sin(oePitch);
        float skyLeft = (-sinYaw * xDistance) + (cosYaw * sinPitch * yDistance) + (cosYaw * cosPitch);
        float skyFront = (cosYaw * xDistance) + (sinYaw * sinPitch * yDistance) + (sinYaw * cosPitch);
        float v18x = -sin((-oePitch) + u_indoorSkyProjectionParams.w);
        float v18z = -cos(oePitch + u_indoorSkyProjectionParams.w);
        float topProjection = min(v18x + v18z * yDistance, -0.0000001);
        float skyDepth = -512.0 / topProjection;
        float scrollPixels = (1000.0 / 64.0) * 0.25 * u_secretPulseParams.y;
        texcoord.xy = vec2(
            (scrollPixels + skyLeft * skyDepth / 16.0) * v_flowInfo.x,
            (scrollPixels + skyFront * skyDepth / 16.0) * v_flowInfo.y);
    }
    else
    {
        texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

        if (v_flowInfo.w < -0.5)
        {
            texcoord.xy += u_indoorSkyParams.xy;
        }
    }

    if (v_flowInfo.z > 0.5 || v_flowInfo.w > 0.5)
    {
        float pongPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
        float swirlPhase = mod(u_secretPulseParams.y, 5.0) * 6.2831853 / 5.0;
        float ripplePhase = mod(u_secretPulseParams.y, 2.0) * 6.2831853 / 2.0;

        vec2 delta = vec2(0.0, 0.0);
        delta.x += pongPhase * 0.01 * sin(texcoord.x * 6.2831853);
        delta.y += pongPhase * 0.01 * sin(texcoord.y * 6.2831853);
        delta.x += 0.01 * sin(swirlPhase + texcoord.y * 6.2831853);
        delta.y += 0.01 * cos(swirlPhase + texcoord.x * 6.2831853);
        delta.x -= 0.005 * cos(ripplePhase + (texcoord.y + delta.y) * 6.2831853 * 24.0);
        texcoord += delta;
    }

    vec4 textureColor = texture2D(s_texColor, texcoord);

    if (textureColor.a <= 0.001)
    {
        discard;
    }

    vec3 color = textureColor.rgb * getIndoorLighting(v_worldPosition, v_color0.rgb);

    // Bounded artistic sheen and emissive before the secret tint. Indoor sky is an
    // excluded presentation surface even if it shares a texture with an authored material.
    if (v_flowInfo.w >= -1.5)
    {
        color += indoorMaterialFaceResponse(v_worldPosition, v_worldNormal);
    }

    if (v_texcoord1.x > 0.5 && u_secretPulseParams.x > 0.5)
    {
        float pulse = 0.5 + 0.5 * sin(u_secretPulseParams.y * 4.0);
        vec3 secretTint = color * vec3(1.0, pulse, pulse);
        color = secretTint;
    }

    gl_FragColor = vec4(color, textureColor.a);
}
