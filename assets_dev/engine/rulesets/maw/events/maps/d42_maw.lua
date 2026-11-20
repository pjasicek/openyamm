-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The Endless Arena's waves (zzMaw_Arena.lua, MAPS_CONTENT.md §4.7). A level is three monster families; each comes in
-- six waves, from many weak monsters to one C-tier boss, the next when the last is down or after a while. Corpses
-- carry nothing. Clearing the level pays its number x 20000 gold and moves the checkpoint.
local SpawnPoints = {
    {3850, 9350}, {4600, 9350}, {5500, 8600}, {6500, 7600}, {6500, 6600}, {6500, 5600}, {6500, 3600},
    {2200, 8600}, {1200, 7600}, {1200, 6600}, {1200, 5600}, {1200, 4600}, {1200, 3600}, {3100, 9350},
}
-- Tier weights (A, B, C) and monster counts of the six waves of a family.
local Waves = {
    {80, 20, 0, 8, 10}, {65, 25, 10, 6, 8}, {50, 30, 20, 4, 6}, {35, 35, 30, 3, 4}, {20, 40, 40, 2, 4},
    {0, 0, 100, 1, 1},
}

local function arenaVar(name)
    return evt.GetGlobalVar(name, 0)
end

RegisterMapTimerEvent(60001, 150, function()
    local level = arenaVar("MawArenaLevel")
    if level <= 0 then
        return
    end
    -- The party's summons and other allies never hold up a level (zzMaw_Arena.lua:221-229).
    local cleared = evt.CheckMonstersKilled(ActorKillCheck.Hostile, 0, 0, false)
    if arenaVar("MawArenaWavesLeft") <= 0 then
        if cleared then
            evt.SetGlobalVar("MawArenaLevel", 0)
            evt.SetGlobalVar("MawArenaBest", math.max(arenaVar("MawArenaBest"), level))
            AddValue(Gold, level * 20000)
            evt.SetNPCTopic(313, 1, 10030)
            evt.SimpleMessage(tr("Level {level} completed!", {level = level}))
        end
        return
    end
    local wait = arenaVar("MawArenaWait")
    if wait > 0 and not cleared then
        evt.SetGlobalVar("MawArenaWait", wait - 1)
        return
    end
    local step = arenaVar("MawArenaStep")
    local wave = Waves[step]
    local family = evt.ArenaMonster(arenaVar("MawArenaWave"))
    for _ = 1, math.random(wave[4], wave[5]) do
        local point = SpawnPoints[math.random(1, #SpawnPoints)]
        evt.SummonMonstersById{monster = family, x = point[1], y = point[2], z = 1, count = 1,
            tiers = {wave[1], wave[2], wave[3]}, radius = 256, group = 2, speed = 350, boss = step == 6}
    end
    evt.SetGlobalVar("MawArenaWait", 1)
    if step == 6 then
        evt.SetGlobalVar("MawArenaStep", 1)
        evt.SetGlobalVar("MawArenaWave", arenaVar("MawArenaWave") + 1)
        evt.SetGlobalVar("MawArenaWavesLeft", arenaVar("MawArenaWavesLeft") - 1)
        evt.SetGlobalVar("MawArenaWait", 12)
    else
        evt.SetGlobalVar("MawArenaStep", step + 1)
    end
    local done = (3 - arenaVar("MawArenaWavesLeft")) + (arenaVar("MawArenaStep") - 1) / 6
    evt.SetGlobalVar("MawArenaProgress", math.floor(done / 3 * 100 + 0.5))
end, "MAW Endless Arena")

-- Leaving the Arena mid-level ends the run; the Arena Master offers the Endless Arena again (zzMaw_Arena.lua:60-76).
RegisterMapOnLeaveEvent(60002, "MAW Endless Arena left", function()
    if arenaVar("MawArenaLevel") > 0 then
        evt.SetGlobalVar("MawArenaLevel", 0)
        evt.SetGlobalVar("MawArenaProgress", 0)
        evt.SetNPCTopic(313, 1, 10030)
    end
end)
