-- Update the names exported into the entrance and sign events.
local guilds = {
    [23] = {"Guild of Fire - Master", 24},
    [25] = {"Guild of Air - Master", 26},
    [27] = {"Guild of Water - Adept", 28},
    [29] = {"Guild of Earth - Adept", 30},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
