-- Update the names exported into the entrance and sign events.
local guilds = {
    [30] = {"Guild of Fire - Grandmaster", 31},
    [32] = {"Guild of Air - Grandmaster", 33},
    [34] = {"Guild of Water - Grandmaster", 35},
    [36] = {"Guild of Earth - Grandmaster", 37},
    [38] = {"Guild of Spirit - Grandmaster", 39},
    [40] = {"Guild of Mind - Grandmaster", 41},
    [42] = {"Guild of Body - Grandmaster", 43},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
