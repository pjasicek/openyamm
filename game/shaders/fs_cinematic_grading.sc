$input v_texcoord0
#include "common.sh"

SAMPLER2D(s_gradeScene, 0);
// The blurred half-resolution glow (bloom, lighting plan phase 7).
SAMPLER2D(s_gradeBloom, 2);
// x: grade strength, w: sharpening 0..1.
uniform vec4 u_gradeParams;
// x: bloom strength (0: none).
uniform vec4 u_gradeBloom;

// Contrast-adaptive sharpening (after AMD FidelityFX CAS): subtracts the four direct neighbours, weighted down
// where the neighbourhood already spans most of the range, so hard edges do not ring or brighten aliasing.
// Full strength sits between CAS's lowest and highest sharpness: its highest turns the sky's dithering into grain.
// Lower strengths fade towards none.
vec3 sharpen(vec3 centre, vec2 uv, float strength)
{
    vec2 texel = u_viewTexel.xy;
    vec3 up = texture2D(s_gradeScene, uv - vec2(0.0, texel.y)).rgb;
    vec3 down = texture2D(s_gradeScene, uv + vec2(0.0, texel.y)).rgb;
    vec3 left = texture2D(s_gradeScene, uv - vec2(texel.x, 0.0)).rgb;
    vec3 right = texture2D(s_gradeScene, uv + vec2(texel.x, 0.0)).rgb;
    vec3 low = min(centre, min(min(up, down), min(left, right)));
    vec3 high = max(centre, max(max(up, down), max(left, right)));
    vec3 headroom = sqrt(clamp(min(low, 1.0 - high) / max(high, vec3_splat(0.0001)), 0.0, 1.0));
    vec3 weight = headroom * (-0.15 * strength);
    return clamp((centre + (up + down + left + right) * weight) / (1.0 + 4.0 * weight), 0.0, 1.0);
}

// The display-referred grade: lifts shadow and midtone detail with black and white anchored, working on luminance
// so neutral stone stays neutral, and mutes orange roofs and earth more than red foliage, greens and blues less.
// Computed per pixel: a 3D LUT fetch cost more (about 11 us of the 52 us pass at 1600x900 on an RTX 3060 Ti).
vec3 gradeColor(vec3 color)
{
    float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
    float remaining = 1.0 - luminance;
    float tone = luminance + 0.16 * luminance * remaining * remaining - 0.06 * luminance * luminance * remaining;
    float chroma = max(max(color.r, color.g), color.b) - min(min(color.r, color.g), color.b);
    float inverseChroma = 1.0 / max(chroma, 0.0001);
    // Smooth hue weights; near-neutral colours fade out of the masks.
    float orange = 4.0 * max(0.0, color.r - color.g) * max(0.0, color.g - color.b) * inverseChroma * inverseChroma;
    float green = max(0.0, color.g - max(color.r, color.b)) * inverseChroma;
    float blue = max(0.0, color.b - max(color.r, color.g)) * inverseChroma;
    float hueWeight = min(chroma / 0.08, 1.0);
    float saturation = 0.92 - hueWeight * (0.25 * orange + 0.10 * green + 0.08 * blue);
    return clamp(tone + (color - luminance) * saturation, 0.0, 1.0);
}

void main()
{
    vec4 original = texture2D(s_gradeScene, v_texcoord0);
    if (u_gradeParams.x <= 0.0 && u_gradeParams.w <= 0.0 && u_gradeBloom.x <= 0.0)
    {
        gl_FragColor = original;
        return;
    }
    vec3 color = clamp(original.rgb, 0.0, 1.0);
    if (u_gradeParams.w > 0.0)
    {
        color = sharpen(color, v_texcoord0, u_gradeParams.w);
    }
    if (u_gradeParams.x > 0.0)
    {
        color = mix(color, gradeColor(color), u_gradeParams.x);
    }
    if (u_gradeBloom.x > 0.0)
    {
        // Screen blend in display space: the glow lifts what is around an emitter without clipping it.
        vec3 bloom = clamp(texture2D(s_gradeBloom, v_texcoord0).rgb * u_gradeBloom.x, 0.0, 1.0);
        color = 1.0 - (1.0 - color) * (1.0 - bloom);
    }
    gl_FragColor = vec4(color, original.a);
}
