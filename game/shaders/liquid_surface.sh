// Lava and tar for the liquid shaders (fs_water, fs_indoor_water); water lives in water_surface.sh.
// v_texcoord1.z selects the liquid: 0 water, 1 tar, 2 lava. Outdoor time (u_waterParams.x) wraps at 1000 seconds,
// so every rate below repeats a whole number of times in 1000 seconds.
// Liquid pattern (engine/liquids/lava_pattern.png, tools/liquids.py): its G channel is the smooth tileable noise the
// lava streaks and the tar's dusty patches sample.
SAMPLER2D(s_liquidPattern, 5);

float liquidHash(vec2 position)
{
    vec3 hash = fract(vec3(position.xyx) * 0.1031);
    hash += dot(hash, hash.yzx + 33.33);
    return fract((hash.x + hash.y) * hash.z);
}

// The pattern's G noise stretched to 0-1 (it spans about 0.21-0.78).
float lavaNoise(vec2 uv)
{
    return clamp((texture2D(s_liquidPattern, uv).g - 0.21) * 1.75, 0.0, 1.0);
}

// Heat 0-1 of a lava surface: molten rock throughout, as the original MM lava. Slow, meandering streaks run along
// the flow (dark red troughs, orange crests); the hottest veins, rare flares and shores run yellow-orange.
// uv: the surface in pattern units; flowOffset: how far a flowing face's authored flow has carried it, in pattern
// units (from an unwrapped clock); worldXy places the flares.
float lavaHeat(vec2 uv, vec2 flowOffset, vec2 worldXy, bool flares, float time)
{
    // Still lava creeps along a diagonal like the original frames; flowing lava follows its face's direction.
    vec2 drift = flowOffset + vec2(0.006, -0.004) * time;
    // A large, slowly changing warp makes the streaks meander instead of running straight.
    vec2 warp = vec2(lavaNoise(uv * 0.35 + vec2(0.002, -0.003) * time),
        lavaNoise(uv * 0.3 + vec2(0.37, 0.71) - vec2(0.003, 0.001) * time)) - vec2_splat(0.5);
    vec2 base = uv + warp * 0.45 + drift;
    // Streaks: noise stretched along the diagonal (pattern space), two octaves sliding at different speeds.
    vec2 along = vec2(0.83, -0.55);
    vec2 across = vec2(0.55, 0.83);
    vec2 streakUv = vec2(dot(base, along) * 0.8, dot(base, across) * 3.2);
    float streaks = lavaNoise(streakUv + vec2(0.005, 0.0) * time) * 0.65
        + lavaNoise(streakUv * 2.1 + vec2(0.37, 0.11) - vec2(0.008, 0.0) * time) * 0.35;
    // Broad, breathing regions of hotter and cooler rock.
    float regions = lavaNoise(base * 0.6 + vec2(0.0, 0.002) * time);
    float pulse = 0.5 + 0.5 * sin(6.2831853 * (time / 10.0 + regions));
    float heat = 0.08 + 0.68 * smoothstep(0.25, 0.8, streaks) + 0.16 * regions + 0.08 * pulse;
    // Thin hot veins where the two streak octaves agree on a crest.
    heat += 0.25 * smoothstep(0.72, 0.9, streaks) * regions;

    if (flares)
    {
        // Rare flares: a spot in a 260-unit cell swells bright, then cools back over its 8-second cycle.
        vec2 grid = worldXy / 260.0;
        vec2 cell = floor(grid);
        float cycle = time / 8.0 + liquidHash(cell);
        float age = fract(cycle);
        vec2 event = cell + floor(cycle) * vec2(1.37, 2.11);
        if (liquidHash(event + 0.5) < 0.2)
        {
            vec2 centre = vec2(liquidHash(event + 3.1), liquidHash(event + 5.7)) * 0.5 + 0.25;
            float distance = length(fract(grid) - centre) * 260.0;
            float radius = mix(18.0, 46.0, liquidHash(event + 7.3)) * (0.7 + 0.6 * age);
            float envelope = smoothstep(0.0, 0.08, age) * (1.0 - age) * (1.0 - age);
            heat = max(heat, envelope * (1.0 - smoothstep(0.0, radius, distance)));
        }
    }
    return clamp(heat, 0.0, 1.0);
}

// Crust plates on indoor lava (liquids.yml `crust`, the share of the surface they cover): the cells of a still
// jittered grid (the melt moves under them); a cell whose hash falls under the share is a dark plate. Returns x: 1
// inside a plate's cell, y: how much of the point its rock covers (0 at the seam round it, where the melt glows).
vec2 lavaCrustCover(vec2 uv, float crust)
{
    vec2 grid = uv * 3.0;
    vec2 cell = floor(grid);
    vec2 local = grid - cell;
    float nearest = 8.0;
    float second = 8.0;
    vec2 nearestCell = cell;
    for (int y = -1; y <= 1; ++y)
    {
        for (int x = -1; x <= 1; ++x)
        {
            vec2 neighbour = cell + vec2(float(x), float(y));
            vec2 centre = vec2(float(x), float(y))
                + vec2(liquidHash(neighbour), liquidHash(neighbour + 7.31)) * 0.8 + 0.1;
            float distance = length(centre - local);
            if (distance < nearest)
            {
                second = nearest;
                nearest = distance;
                nearestCell = neighbour;
            }
            else if (distance < second)
            {
                second = distance;
            }
        }
    }
    float plate = step(liquidHash(nearestCell + 3.7), crust);
    return vec2(plate, plate * smoothstep(0.05, 0.16, second - nearest));
}

// Self-lit lava colour, the original palette carried on: dark red (cool troughs) through the glow (the liquid's
// colour, orange) to yellow-orange in the hottest veins and flares.
// The same ramp in shades of the liquid's own colour (liquids.yml `tint`, indoor faces): dark troughs of the colour,
// the colour itself, and veins that run toward white instead of orange-yellow.
vec3 lavaTintedColor(float heat, vec3 glow)
{
    vec3 color = mix(glow * 0.22, glow * 0.48, smoothstep(0.1, 0.4, heat));
    color = mix(color, glow, smoothstep(0.38, 0.75, heat));
    return mix(color, mix(glow, vec3_splat(1.0), 0.45), smoothstep(0.82, 1.0, heat));
}

vec3 lavaColor(float heat, vec3 glow)
{
    vec3 color = mix(vec3(0.36, 0.04, 0.01), vec3(0.62, 0.13, 0.02), smoothstep(0.1, 0.4, heat));
    color = mix(color, glow, smoothstep(0.38, 0.75, heat));
    return mix(color, vec3(1.0, 0.56, 0.12), smoothstep(0.82, 1.0, heat));
}

// Tar bubbles: in a 220-unit cell, now and then a gas bubble slowly lifts the skin into a smooth dome, pops into a
// crater and sends out a ring that settles, over a 9-second cycle. Returns the surface slope (xy) and how much of the
// stretched, glossier bubble skin covers the point (z).
vec3 tarBubble(vec2 worldXy, float time)
{
    const float cellSize = 220.0;
    vec2 grid = worldXy / cellSize;
    vec2 cell = floor(grid);
    float cycle = time / 9.0 + liquidHash(cell);
    float age = fract(cycle);
    vec2 event = cell + floor(cycle) * vec2(1.37, 2.11);
    if (liquidHash(event + 0.5) >= 0.3)
    {
        return vec3_splat(0.0);
    }
    // Keep the whole bubble and its ring inside the cell.
    vec2 offset = (fract(grid) - (vec2(liquidHash(event + 3.1), liquidHash(event + 5.7)) * 0.3 + 0.35)) * cellSize;
    float distance = length(offset);
    vec2 direction = offset / max(distance, 0.001);
    float size = mix(25.0, 50.0, liquidHash(event + 9.2));
    if (age < 0.7)
    {
        // Swelling dome h = height * (1 - (d / radius)^2)^2: it rises slowly and grows a little.
        float swell = age / 0.7;
        float radius = size * (0.55 + 0.45 * swell);
        float height = size * 0.5 * swell * swell;
        float q = distance * distance / (radius * radius);
        if (q >= 1.0)
        {
            return vec3_splat(0.0);
        }
        float slope = -4.0 * height * distance * (1.0 - q) / (radius * radius);
        return vec3(direction * slope, (1.0 - q) * smoothstep(0.1, 0.4, swell));
    }
    // Popped: a crater that fills back in, and a ring spreading to three times the bubble and flattening.
    float settle = (age - 0.7) / 0.3;
    float fade = (1.0 - settle) * (1.0 - settle);
    float slope = 0.0;
    float q = distance * distance / (size * size);
    if (q < 1.0)
    {
        slope += 4.0 * size * 0.25 * fade * distance * (1.0 - q) / (size * size);
    }
    float profile = (distance - size * (1.0 + 2.0 * settle)) / 6.0;
    slope += profile * exp(-profile * profile) * fade * 1.2;
    return vec3(direction * slope, 0.0);
}
