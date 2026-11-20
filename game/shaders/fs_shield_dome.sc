$input v_worldPosition, v_worldNormal

#include "common.sh"

// Additive force-field shell (ShieldDomeRenderer): a fresnel rim, drifting energy noise, a glowing line where the
// shell meets the ground and ripples from projectile hits. Both faces draw; the far wall shows dimmer through the
// near one.
uniform vec4 u_shieldColor;   // rgb tint, overall strength (intensity x fade)
uniform vec4 u_shieldParams;  // rim power, noise amount, time in seconds, unused
uniform vec4 u_shieldCenter;  // centre xyz, radius
uniform vec4 u_shieldCamera;  // camera position xyz, ground height under the shell
uniform vec4 u_shieldHits[4]; // unit direction from the centre to a hit, age in seconds (negative: unused)

#include "shield_common.sh"

void main()
{
    vec3 direction = normalize(v_worldNormal);
    vec3 toCamera = normalize(u_shieldCamera.xyz - v_worldPosition);
    float facing = dot(direction, toCamera);
    float rim = pow(1.0 - abs(facing), u_shieldParams.x);
    float time = u_shieldParams.z;

    float noise = valueNoise(direction * 3.5 + vec3(0.0, 0.0, time * 0.45)) * 0.6
        + valueNoise(direction * 8.0 - vec3(time * 0.6, time * 0.2, 0.0)) * 0.4;
    float energy = mix(1.0, 0.35 + 1.5 * smoothstep(0.42, 0.78, noise), u_shieldParams.y);

    // Where the shell enters the ground: a stand-in for a depth-buffer intersection glow.
    float contact = 1.0 - smoothstep(0.0, 40.0, abs(v_worldPosition.z - u_shieldCamera.w));
    float aboveGround = step(u_shieldCamera.w - 4.0, v_worldPosition.z);

    float hit = 0.0;
    for (int index = 0; index < 4; ++index)
    {
        vec4 impact = u_shieldHits[index];
        if (impact.w >= 0.0)
        {
            float arc = acos(clamp(dot(direction, impact.xyz), -1.0, 1.0)) * u_shieldCenter.w;
            float ringRadius = impact.w * 450.0;
            float ringWidth = 18.0 + impact.w * 40.0;
            float ring = exp(-((arc - ringRadius) * (arc - ringRadius)) / (ringWidth * ringWidth));
            float flash = exp(-(arc * arc) / 2500.0) * max(0.0, 1.0 - impact.w * 6.0);
            hit += (0.7 * ring + flash) * max(0.0, 1.0 - impact.w / 0.7);
        }
    }
    hit = min(hit, 1.2);

    float faceGain = facing >= 0.0 ? 1.0 : 0.45;
    float strength = (0.06 * energy + 1.15 * rim * energy) * faceGain + 0.9 * contact + 0.8 * hit;
    strength *= aboveGround * u_shieldColor.w;
    // Hot spots lean towards white without blowing out.
    vec3 color = u_shieldColor.rgb * min(strength, 1.6) + vec3_splat(clamp(strength - 1.0, 0.0, 1.0) * 0.25);
    gl_FragColor = vec4(color, 1.0);
}
