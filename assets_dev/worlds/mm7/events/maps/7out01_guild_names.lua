-- Update the names exported into the entrance and sign events.
local guilds = {
    [16] = {"Guild of Fire - Initiate", 17},
    [18] = {"Guild of Air - Initiate", 19},
    [20] = {"Guild of Spirit - Initiate", 21},
    [22] = {"Guild of Body - Initiate", 23},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
