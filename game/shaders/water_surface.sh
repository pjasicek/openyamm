// Shared normal waves, Fresnel response and planar sampling for terrain and indoor water.
SAMPLER2D(s_waterNormal, 1);
SAMPLER2D(s_waterReflection, 2);
uniform vec4 u_waterParams;
uniform mat4 u_waterReflectionMatrix;
uniform vec4 u_cameraPosition;

vec3 waveSample(vec2 uv, float scale, vec2 speed)
{
    return texture2D(s_waterNormal, uv * scale + speed * u_waterParams.x).rgb * 2.0 - 1.0;
}

vec3 waterWaveNormal(vec2 uv, vec3 baseNormal, vec3 tangent, vec3 bitangent, float strength)
{
    vec3 waves = waveSample(uv, 0.5, vec2(0.018, -0.011)) * 0.50;
    waves += waveSample(uv, 1.1, vec2(-0.025, 0.019)) * 0.30;
    waves += waveSample(uv, 2.4, vec2(0.041, 0.031)) * 0.15;
    waves += waveSample(uv, 5.0, vec2(-0.061, 0.047)) * 0.05;
    return normalize(baseNormal - (tangent * waves.x + bitangent * waves.y) * strength);
}

float waterFlowFoam(vec2 uv, float falling)
{
    float turbulence = waveSample(uv, 2.4, vec2(0.041, 0.031)).x;
    return falling * (0.10 + 0.65 * smoothstep(-0.12, 0.12, turbulence));
}

float waterFresnel(vec3 normal, vec3 viewDirection)
{
    float grazing = 1.0 - clamp(abs(dot(normal, viewDirection)), 0.0, 1.0);
    return 0.02 + 0.98 * grazing * grazing * grazing * grazing * grazing;
}

// Callers bound normalized UV distortion to +/- 0.014, matching the capture/scissor margin.
vec3 waterReflection(vec3 worldPosition, vec2 distortion, vec3 fallback)
{
    vec3 reflected = fallback;
    if (u_waterParams.y > 0.5)
    {
        vec4 reflectionClip = mul(u_waterReflectionMatrix, vec4(worldPosition, 1.0));
        vec2 reflectionUv = reflectionClip.xy / max(reflectionClip.w, 0.0001);
        reflectionUv = reflectionUv * vec2(0.5, 0.5 * u_waterParams.z) + vec2_splat(0.5);
        // Guarded captures use a wider projection at the same pixel density.
        reflectionUv += distortion * vec2(1.0, u_waterParams.z) * u_waterParams.y;
        // Fade distortion at texture edges instead of dragging a clamped edge across the water.
        vec2 edge = min(reflectionUv, vec2_splat(1.0) - reflectionUv);
        float reflectedCoverage = smoothstep(0.0, 0.02 * u_waterParams.y, min(edge.x, edge.y));
        reflected = mix(reflected, texture2D(s_waterReflection, reflectionUv).rgb, reflectedCoverage);
    }

    return reflected;
}

#if WATER_MOVEMENT_RIPPLES
uniform vec4 u_waterRippleRings[4];
uniform vec4 u_waterRippleParams;

vec3 waterMovementNormal(vec3 worldPosition, vec3 normal, vec3 baseNormal, out float sheen)
{
    vec2 displacement = vec2_splat(0.0);
    sheen = 0.0;
    for (int i = 0; i < 4; ++i)
    {
        if (float(i) >= u_waterRippleParams.x)
        {
            break;
        }
        vec4 ring = u_waterRippleRings[i];
        vec2 delta = worldPosition.xy - ring.xy;
        float distanceSquared = dot(delta, delta);
        float inner = ring.z - 10.0;
        float outer = ring.z + 10.0;
        // Most water pixels miss the thin ring; avoid square roots outside its annulus.
        if (distanceSquared > inner * inner && distanceSquared < outer * outer)
        {
            float distance = sqrt(max(distanceSquared, 0.01));
            float profile = (distance - ring.z) / 10.0;
            float envelope = 1.0 - profile * profile;
            // A compact crest/trough pair avoids trigonometry and expensive water simulation.
            float crest = envelope * envelope * ring.w;
            displacement += delta / distance * profile * crest * 0.65;
            sheen += crest * 0.075;
        }
    }
    return normalize(normal - vec3(displacement, 0.0) * abs(baseNormal.z));
}
#endif
