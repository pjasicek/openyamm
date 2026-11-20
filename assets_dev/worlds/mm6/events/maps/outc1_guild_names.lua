-- Update the names exported into the entrance and sign events.
local guilds = {
    [19] = {"Guild of Dark - Initiate", 20},
    [21] = {"Guild of the Elements - Master", 22},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
