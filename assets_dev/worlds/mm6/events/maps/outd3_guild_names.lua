-- Update the names exported into the entrance and sign events.
local guilds = {
    [14] = {"Guild of Fire - Initiate", 15},
    [52] = {"Guild of Spirit - Initiate", 53},
    [54] = {"Guild of Mind - Initiate", 55},
    [56] = {"Guild of Body - Initiate", 57},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
