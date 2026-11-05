-- MMMerge supplement: Dimension Door, Stone-to-Flesh spell statues, and merged duplicate gems.

local GemExchangeEntries = {
    {186, 656},
    {997, 656},
    {994, 656},
    {2056, 656},
    {185, 271},
    {998, 271},
    {2059, 271},
    {184, -2000},
    {2065, -2000},
    {991, -2000},
    {183, 655},
    {2064, 655},
    {990, 655},
    {2061, 655},
    {182, 0},
    {2058, 0},
    {989, 0},
    {181, 183},
    {2060, 183},
    {180, 250},
    {2102, 250},
    {179, 181},
    {178, 132},
    {177, 179},
}

ReplaceMapEvent(132, "Statue", function()
    MM8.UnstoneStatue(20, 42, true)
end, "Statue")
SetMapContextAction(132, { kind = "stone_to_flesh", source = "spell", targetName = "Statue" })

for eventId = 133, 136 do
    local statueEventId = eventId
    local spriteId = statueEventId - 112

    ReplaceMapEvent(eventId, "Statue", function()
        MM8.UnstoneStatue(spriteId, 46, false)
    end, "Statue")
    SetMapContextAction(eventId, { kind = "stone_to_flesh", source = "spell", targetName = "Statue" })
end

ReplaceMapEvent(455, "Tree", function()
    MM8.TryExchangeGem(GemExchangeEntries)
end, "Tree")

RegisterEvent(500, "Dimension Door", function()
    MM8.OpenDimensionDoor()
end, "Dimension Door")

RegisterMapOnLoadEvent(901, "MMMerge Dimension Door tile reset", function()
    MM8.SetMapFlag("DimensionDoorTileActive", false)
end)

RegisterMapTimerEvent(902, 1, function()
    MM8.OpenDimensionDoorOnTile(43, 98, "DimensionDoorTileActive")
end, "MMMerge Dimension Door tile")

-- The Unicorn King (actor 0, unique name 7) walks Murmurwoods only on June 24 from 9 to 17 o'clock, as the original
-- executable hardcodes (MM8-Rel.exe 0x48059e, 0x47b4f1); the rest of the year it is hidden and inert. A slain one
-- stays.
-- Map-local, so no other map pays for it: the timer compares the date and touches the actor only when its visibility
-- has to change, at most twice a day.
local UnicornKingActor = 0
local UnicornKingSlain = "UnicornKingSlain"
local unicornKingShown = nil

local function UnicornKingDayActive()
    local minutes = math.floor(CurrentGameMinutes())
    local dayOfYear = math.floor(minutes / MM8.MinutesPerDay) % (12 * 28)
    local hour = math.floor(minutes / 60) % 24
    return math.floor(dayOfYear / 28) == 5 and dayOfYear % 28 == 23 and hour >= 9 and hour <= 17
end

local function UpdateUnicornKing(force)
    local shown = UnicornKingDayActive()

    if shown == unicornKingShown and not force then
        return
    end

    unicornKingShown = shown

    -- The death is remembered here: CheckMonstersKilled counts a hidden actor as slain.
    if MM8.GetMapFlag(UnicornKingSlain) then
        return
    end

    evt.SetMonsterBit(UnicornKingActor, ActorAttribute.Invisible, not shown)
end

RegisterMapOnLoadEvent(903, "Unicorn King appearance", function()
    UpdateUnicornKing(true)
end)

RegisterMapTimerEvent(904, 300, function()
    UpdateUnicornKing(false)
end, "Unicorn King appearance")

RegisterMonsterKilledHook(65040, "Unicorn King slain", function(context)
    if context.actorIndex == UnicornKingActor then
        MM8.SetMapFlag(UnicornKingSlain, true)
    end
end)

-- A refill brings the Unicorn King back with the map's other monsters.
RegisterMapRefillHook(65041, "Unicorn King refill", function()
    MM8.SetMapFlag(UnicornKingSlain, false)
    unicornKingShown = nil
end)
