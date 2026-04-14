$input v_texcoord0, v_texcoord1, v_worldPosition, v_depth

#include "common.sh"

uniform vec4 u_previewColorA;
uniform vec4 u_previewColorB;
uniform vec4 u_previewColorC;
uniform vec4 u_previewColorD;
uniform vec4 u_previewParams0;
uniform vec4 u_previewParams1;
uniform vec4 u_previewObjectOrigin;

float gridLineMask(vec2 uv, float thickness)
{
    vec2 gridDistance = min(fract(uv), 1.0 - fract(uv));
    float edgeDistance = min(gridDistance.x, gridDistance.y);
    return 1.0 - smoothstep(0.0, max(thickness, 0.0001), edgeDistance);
}

vec3 applyEditorLighting(vec3 baseColor, vec3 normal)
{
    vec3 lightDirection = normalize(vec3(-0.35, 0.55, 0.76));
    float lightWrap = u_previewParams0.z;
    float ndotl = clamp(dot(normal, lightDirection), -1.0, 1.0);
    float wrapped = clamp((ndotl + lightWrap) / (1.0 + lightWrap), 0.0, 1.0);
    float shadowStrength = clamp(u_previewParams0.y, 0.0, 1.0);
    float lightFactor = mix(1.0 - shadowStrength, 1.0, wrapped);
    return baseColor * lightFactor;
}

vec4 shadeClay()
{
    vec3 normal = normalize(v_texcoord1.xyz);
    vec3 localWorld = v_worldPosition - u_previewObjectOrigin.xyz;
    float slope = 1.0 - clamp(abs(normal.z), 0.0, 1.0);
    float slopeAccent = clamp(u_previewParams0.x, 0.0, 1.0);
    float localHeightTint = clamp((localWorld.z + 2048.0) / 4096.0, 0.0, 1.0);
    vec3 baseColor = u_previewColorA.rgb * mix(0.98, 1.02, localHeightTint);
    vec3 litColor = applyEditorLighting(baseColor, normal);
    vec3 slopeColor = litColor * mix(1.0, 0.82, slope * slopeAccent);
    return vec4(clamp(slopeColor, vec3(0.0), vec3(1.0)), u_previewColorA.a);
}

vec4 shadeGrid(float mode)
{
    vec3 normal = normalize(v_texcoord1.xyz);
    float cellSize = max(u_previewParams0.x, 1.0);
    float majorInterval = max(u_previewParams0.y, 1.0);
    float minorThickness = clamp(u_previewParams0.z, 0.0005, 0.49);
    float majorThickness = clamp(u_previewParams0.w, minorThickness, 0.49);
    vec2 cellUv = v_texcoord0 / cellSize;
    vec2 majorUv = cellUv / majorInterval;
    float checker = mod(floor(cellUv.x) + floor(cellUv.y), 2.0);
    vec3 baseColor = mix(u_previewColorA.rgb, u_previewColorB.rgb, checker);
    float minorMask = gridLineMask(cellUv, minorThickness);
    float majorMask = gridLineMask(majorUv, majorThickness);
    vec3 color = mix(baseColor, u_previewColorC.rgb, minorMask);
    color = mix(color, u_previewColorD.rgb, majorMask);

    if (mode > 1.5)
    {
        float stripe = step(0.5, fract((cellUv.x + cellUv.y) * 0.5));
        color = mix(color, u_previewColorD.rgb, stripe * 0.35);
    }

    return vec4(clamp(applyEditorLighting(color, normal), vec3(0.0), vec3(1.0)), 1.0);
}

void main()
{
    float mode = u_previewParams1.x;

    if (mode < 0.5)
    {
        gl_FragColor = shadeClay();
        return;
    }

    gl_FragColor = shadeGrid(mode);
}
