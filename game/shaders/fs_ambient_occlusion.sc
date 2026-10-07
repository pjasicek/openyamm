$input v_texcoord0
#include "common.sh"
#include "ambient_occlusion.sh"
uniform mat4 u_aoProjection;

void main()
{
    vec2 uv = v_texcoord0;
    float depth = texture2D(s_aoDepth, uv).r;
    vec3 position = aoViewPosition(uv, depth);
    float distance = -position.z;
    if (depth >= 0.999999 || distance > u_aoParams.w)
    {
        gl_FragColor = vec4(1.0, min(distance, 60000.0), 0.0, 1.0);
        return;
    }
    vec2 dx = vec2(u_aoTexel.x * 2.0, 0.0);
    vec2 dy = vec2(0.0, u_aoTexel.y * 2.0);
    vec3 left = aoViewPosition(uv - dx, texture2D(s_aoDepth, uv - dx).r);
    vec3 right = aoViewPosition(uv + dx, texture2D(s_aoDepth, uv + dx).r);
    vec3 down = aoViewPosition(uv - dy, texture2D(s_aoDepth, uv - dy).r);
    vec3 up = aoViewPosition(uv + dy, texture2D(s_aoDepth, uv + dy).r);
    // Choose the neighbour on the same surface at silhouette discontinuities.
    vec3 tangentX = abs(left.z - position.z) < abs(right.z - position.z) ? position - left : right - position;
    vec3 tangentY = abs(down.z - position.z) < abs(up.z - position.z) ? position - down : up - position;
    vec3 normal = cross(tangentX, tangentY);
    normal /= sqrt(max(dot(normal, normal), 0.000001));
    normal *= dot(normal, -position) < 0.0 ? -1.0 : 1.0;
    float rotation = fract(sin(dot(floor(uv / u_aoTexel.zw), vec2(12.9898, 78.233))) * 43758.5453) * 6.2831853;
    vec2 radiusUv = vec2(u_aoProjection[0][0], u_aoProjection[1][1])
        * (0.5 * u_aoParams.x / max(distance, 1.0));
    radiusUv = min(radiusUv, vec2(0.12, 0.12));
    float occlusion = 0.0;
    for (int direction = 0; direction < 8; ++direction)
    {
        float angle = rotation + float(direction) * 0.78539816;
        vec2 ray = vec2(cos(angle), sin(angle));
        for (int step = 0; step < 2; ++step)
        {
            vec2 sampleUv = uv + ray * radiusUv * (0.4 + float(step) * 0.5);
            if (any(lessThan(sampleUv, vec2(0.0, 0.0))) || any(greaterThan(sampleUv, vec2(1.0, 1.0))))
            {
                continue;
            }
            float sampleDepth = texture2D(s_aoDepth, sampleUv).r;
            vec3 delta = aoViewPosition(sampleUv, sampleDepth) - position;
            float lengthSquared = dot(delta, delta);
            float falloff = max(0.0, 1.0 - lengthSquared / (u_aoParams.x * u_aoParams.x));
            float facing = max(0.0, dot(normal, delta) / sqrt(max(lengthSquared, 0.01)) - u_aoParams.y);
            occlusion += facing * falloff * falloff;
        }
    }
    gl_FragColor = vec4(1.0 - min(0.65, occlusion * 0.25), distance, 0.0, 1.0);
}
