-- Update the names exported into the entrance and sign events.
local guilds = {
    [17] = {"Guild of Fire - Adept", 18},
    [19] = {"Guild of Air - Adept", 20},
    [21] = {"Guild of Spirit - Adept", 22},
    [23] = {"Guild of Body - Adept", 24},
    [25] = {"Guild of Water - Initiate", 26},
    [27] = {"Guild of Earth - Initiate", 28},
    [29] = {"Guild of Mind - Initiate", 30},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
