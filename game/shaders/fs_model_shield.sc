$input v_worldPosition, v_worldNormal

#include "common.sh"

// Additive energy shield over a creature (ModelShieldShell, vs_model_shield), in the look of the ward dome
// (fs_shield_dome): a fresnel rim over drifting energy noise and rising bands, flicker as the pool runs low, ripples
// from recent hits, a sweep up from the feet as it comes back up and a bright shatter into dissolving cells as it
// breaks. Both faces draw without depth writes.
uniform vec4 u_shieldShell[8];

#include "shield_common.sh"

void main()
{
    vec3 normal = normalize(v_worldNormal);
    vec3 toCamera = normalize(u_shieldShell[3].xyz - v_worldPosition);
    float facing = dot(normal, toCamera);
    float time = u_shieldShell[1].x;
    float breakAge = u_shieldShell[1].y;
    float raiseAge = u_shieldShell[1].z;
    float fraction = u_shieldShell[1].w;
    float height = max(u_shieldShell[2].y, 1.0);
    float bodyPhase = clamp((v_worldPosition.z - u_shieldShell[2].x) / height, 0.0, 1.0);

    vec3 p = v_worldPosition * 0.035;
    float noise = valueNoise(p + vec3(0.0, 0.0, time * 0.7)) * 0.6
        + valueNoise(p * 2.6 - vec3(time * 0.9, time * 0.35, 0.0)) * 0.4;
    float energy = 0.3 + 1.5 * smoothstep(0.45, 0.8, noise);
    float rim = pow(1.0 - abs(facing), 2.0);
    float bands = 0.75 + 0.25 * sin(v_worldPosition.z * 0.22 - time * 5.0);
    // A failing shield flickers: dark beats, more of them the lower the pool.
    float beat = hash13(vec3(floor(time * 18.0), 7.0, 3.0));
    float flicker = beat < (1.0 - fraction) * 0.35 ? 0.35 : 1.0;
    float faceGain = facing >= 0.0 ? 1.0 : 0.5;
    float strength = (0.08 + 1.1 * rim) * energy * bands * flicker * faceGain;

    float hit = 0.0;
    for (int index = 0; index < 4; ++index)
    {
        vec4 impact = u_shieldShell[4 + index];
        if (impact.w >= 0.0)
        {
            float distanceToHit = length(v_worldPosition - impact.xyz);
            float ringRadius = impact.w * 240.0;
            float ringWidth = 8.0 + impact.w * 30.0;
            float ring = exp(-((distanceToHit - ringRadius) * (distanceToHit - ringRadius)) / (ringWidth * ringWidth));
            float flash = exp(-(distanceToHit * distanceToHit) / 3600.0) * max(0.0, 1.0 - impact.w * 4.0);
            hit += (1.1 * ring + 2.0 * flash) * max(0.0, 1.0 - impact.w / 0.7);
        }
    }
    strength += min(hit, 2.5);

    if (raiseAge >= 0.0 && raiseAge < 0.5)
    {
        // Coming back up: the shell climbs from the feet behind a bright edge.
        float front = raiseAge / 0.5 * 1.15;
        float edge = exp(-((bodyPhase - front) * (bodyPhase - front)) / 0.004);
        strength = strength * step(bodyPhase, front) + 1.8 * edge;
    }

    if (breakAge >= 0.0)
    {
        // Shattering: a white flash, then cells of the shell burn away from their edges as it swells.
        float flash = max(0.0, 1.0 - breakAge / 0.15);
        float progress = clamp((breakAge - 0.05) / 0.6, 0.0, 1.0);
        float cells = valueNoise(v_worldPosition * 0.06 + vec3(3.1, 1.7, 0.0)) * 0.7
            + valueNoise(v_worldPosition * 0.18) * 0.3;
        if (cells < progress)
        {
            discard;
        }
        float edge = 1.0 - smoothstep(0.0, 0.08, cells - progress);
        strength = (0.6 + rim) * (1.0 - progress) + 2.2 * edge * (1.0 - progress * 0.5) + 2.5 * flash;
    }

    strength *= u_shieldShell[0].w;
    if (u_shieldShell[2].z > 0.0)
    {
        // Bloom pass: the glowing share only.
        strength *= u_shieldShell[2].z;
    }
    // Hot spots lean towards white without blowing out.
    vec3 color = u_shieldShell[0].rgb * min(strength, 1.8) + vec3_splat(clamp(strength - 1.0, 0.0, 1.5) * 0.3);
    gl_FragColor = vec4(color, 1.0);
}
