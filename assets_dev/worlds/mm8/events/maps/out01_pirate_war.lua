-- The pirate and lizardman war on Dagger Wound (event 463, every ten minutes until the Pirate Leader falls): each
-- wiped group comes back. The original repeats this forever, so a party could stand at the pirates' landing and farm
-- gold and experience without end. Here the pirates land at most PirateWaveLimit times; the count is the map variable
-- PirateWaves, which goes back to zero when the map refills. MAW games replace this event with their own (out01_maw.lua).
-- The original event summons the first point of group 10 at y -66192 and of group 13 at y 55504, far past the map's
-- edge (+-22528), where they can never be reached; they spawn at -6192 and 5504, beside the group's other points.
local PirateWaveLimit = 10

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
    if evt.GetMapVar("PirateWaves", 0) >= PirateWaveLimit then
        return
    end
    for _, wave in ipairs(Waves) do
        if evt.CheckMonstersKilled(ActorKillCheck.Group, wave.group, 0, true) then
            for _, point in ipairs(wave.points) do
                evt.SummonMonsters(wave.slot, 2, 3, point[1], point[2], point[3], wave.group, 0)
            end
            if wave.pirates then
                evt.SetMapVar("PirateWaves", evt.GetMapVar("PirateWaves", 0) + 1)
            end
        end
    end
end)
