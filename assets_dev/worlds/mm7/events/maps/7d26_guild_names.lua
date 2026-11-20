-- Update the names exported into the entrance and sign events.
local guilds = {
    [425] = {"Guild of Earth - Grandmaster", 426},
    [427] = {"Guild of Dark - Grandmaster", 428},
}

for entranceId, guild in pairs(guilds) do
    local name, signId = guild[1], guild[2]
    RegisterEvent(entranceId, name, nil, name)
    evt.meta.map.contextActions[entranceId].targetName = name
    if signId then
        RegisterEvent(signId, name, nil, name)
    end
end
