-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The pirate and lizardman war (event 463, every ten minutes until the Pirate Leader falls): each wiped group comes
-- back. Road to Insanity and Beyond Madness stop the war once the pirates have come back 25 times
-- (Maps/out01.lua:15-22; PHASE9_SCOPE P9.I8); the count is the map variable MawPiratesSpawned.
-- The original event summons the first point of group 10 at y -66192 and of group 13 at y 55504, far past the map's
-- edge (+-22528), where they can never be reached, so the map is never cleared; MAW pulled them back to its edge every
-- two seconds (checkOutOfBound). Here they spawn at -6192 and 5504, beside the group's other points.
local Waves = {
    {group = 10, slot = 2, pirates = true,
        points = {{776, -6192, 0}, {0, -5608, 0}, {-656, -5696, 23}, {-1280, -5720, 0}}},
    {group = 11, slot = 2, pirates = true,
        points = {{-2744, 4864, 176}, {-2984, 4208, 561}, {-3624, 4280, 400}, {-3504, 4992, 74}}},
    {group = 12, slot = 1, points = {{5208, -736, 46}, {3120, 800, 226}, {3480, -2656, 88}, {2080, -2248, 539}}},
    {group = 13, slot = 1, points = {{-896, 5504, 384}, {-104, 5328, 384}, {-880, 4464, 510}, {-1256, 5296, 241}}},
}

RegisterMapTimerEvent(463, 600, function()
    if IsQBitSet(QBit(6)) then return end -- Pirate Leader in Dagger Wound Pirate Outpost killed
    local mode = evt.RulesetInfo().challengeMode
    local insanity = mode == "road_to_insanity" or mode == "beyond_madness"
    if insanity and evt.GetMapVar("MawPiratesSpawned", 0) > 25 then
        return
    end
    for _, wave in ipairs(Waves) do
        if evt.CheckMonstersKilled(ActorKillCheck.Group, wave.group, 0, true) then
            for _, point in ipairs(wave.points) do
                evt.SummonMonsters(wave.slot, 2, 3, point[1], point[2], point[3], wave.group, 0)
            end
            if wave.pirates then
                evt.SetMapVar("MawPiratesSpawned", evt.GetMapVar("MawPiratesSpawned", 0) + 1)
            end
        end
    end
end)

-- Saves made before that fix keep the pirates and lizardmen it stranded beyond the edge: they come back to their
-- group's corrected point when the map is loaded.
local MapEdge = 22528
RegisterMapOnLoadEvent(902, "MAW: stranded war party back on the island", function()
    local actorIndex = 0
    while true do
        local x, y = evt.GetMapActorPosition(actorIndex)
        if x == nil then
            break
        end
        if not evt.IsMapActorDead(actorIndex) and (math.abs(x) > MapEdge or math.abs(y) > MapEdge) then
            local point = y < 0 and Waves[1].points[1] or Waves[4].points[1]
            evt.SetMapActorPosition(actorIndex, point[1] + (actorIndex % 4) * 96, point[2], point[3])
        end
        actorIndex = actorIndex + 1
    end
end)
