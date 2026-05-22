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
