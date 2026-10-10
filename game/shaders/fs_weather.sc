$input v_texcoord0, v_texcoord1, v_color0

#include "common.sh"

// [2] for the curtain: y scroll phase (0-1), z columns, w repeats.
uniform vec4 u_weather[6];

float weatherHash(float value)
{
    float hash = fract(value * 0.1031);
    hash *= hash + 33.33;
    hash *= hash + hash;
    return fract(hash);
}

void main()
{
#if WEATHER_CURTAIN
    // Distant sheets of rain: thin falling streaks in hashed columns, leaning with the wind.
    float x = v_texcoord0.x * u_weather[2].z;
    float column = floor(x);
    float lane = 1.0 - abs(fract(x) - 0.5) * 2.0;
    float y = v_texcoord0.y * u_weather[2].w + u_weather[2].y + weatherHash(column + 17.31);
    float segment = fract(y);
    float streak = smoothstep(0.0, 0.08, segment) * (1.0 - smoothstep(0.2, 0.55, segment));
    float present = step(0.3, weatherHash(column + 41.7));
    float alpha = v_color0.a * smoothstep(0.55, 1.0, lane) * streak * present;
#elif WEATHER_SPLASH
    // A flattened ring where the drop hit, widening as it fades, and droplets thrown up on short arcs.
    float age = v_texcoord1.x;
    vec2 point = v_texcoord0;
    float ringDistance = length(vec2(point.x, point.y * 4.0)) - mix(0.2, 1.0, age);
    float ring = exp(-ringDistance * ringDistance * 40.0) * (1.0 - step(0.3, point.y));
    float drops = 0.0;

    for (int index = 0; index < 4; ++index)
    {
        float side = (float(index) - 1.5) / 1.5;
        float lift = 0.7 + 0.3 * fract(v_texcoord1.y * 7.0 + float(index) * 0.37);
        vec2 droplet = vec2(side * 0.8 * age, (2.2 * age - 2.4 * age * age) * lift);
        vec2 offset = point - droplet;
        drops += exp(-dot(offset, offset) * 120.0);
    }

    float alpha = v_color0.a * (ring * 0.8 + drops) * (1.0 - age);
#elif WEATHER_SNOW
    // A soft flake around its short motion: v_texcoord1.x is the motion length in flake radii, y its rotation.
    // Six faint lobes break up the disc on near, large flakes; distant ones are a pixel or two and read as dots.
    float coreLength = v_texcoord1.x;
    float along = v_texcoord0.x * (coreLength + 2.0) - 1.0;
    vec2 point = vec2(along - clamp(along, 0.0, coreLength), v_texcoord0.y);
    float radius = length(point);
    float lobes = 1.0 + 0.2 * cos(6.0 * atan2(point.y, point.x) + v_texcoord1.y);
    float alpha = v_color0.a * (1.0 - smoothstep(0.25, 1.0, radius / (0.85 * lobes)));
#else
    // Thin across the streak, brightest at the falling head and fading toward the tail.
    float across = 1.0 - v_texcoord0.y * v_texcoord0.y;
    float alpha = v_color0.a * across * smoothstep(0.0, 0.6, v_texcoord0.x);
#endif

    gl_FragColor = vec4(v_color0.rgb * alpha, alpha);
}
