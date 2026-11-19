-- Update the names exported into the entrance and sign events.
local guilds = {
    [23] = {"Guild of Spirit - Grandmaster", 24},
    [25] = {"Guild of Mind - Adept", 26},
    [27] = {"Guild of Body - Master", 28},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
