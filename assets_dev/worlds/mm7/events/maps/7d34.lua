-- The Red Dwarf Mines
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 196, 197, 198},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"c2b"},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    { eventId = 51, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(570)) then -- Destroyed critter generator in dungeon. Warrior Mage promo quest.
        SetValue(MapVar(2), 1)
    end
    if IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        evt.SetSprite(1, 0, "0")
        evt.SetSprite(2, 0, "0")
        evt.SetSprite(3, 0, "0")
        evt.SetSprite(4, 0, "0")
        evt.SetSprite(5, 0, "0")
        evt.SetSprite(6, 0, "0")
        evt.SetSprite(7, 0, "0")
    end
end)

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(Counter(4), 1) then return end
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(151, "Legacy event 151", function()
    if IsAtLeast(Counter(4), 1) then return end
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(176, "Mine Car", function()
    evt.OpenChest(1)
end, "Mine Car")

RegisterEvent(177, "Mine Car", function()
    evt.OpenChest(2)
end, "Mine Car")

RegisterEvent(178, "Mine Car", function()
    evt.OpenChest(3)
end, "Mine Car")

RegisterEvent(179, "Mine Car", function()
    evt.OpenChest(4)
end, "Mine Car")

RegisterEvent(180, "Mine Car", function()
    evt.OpenChest(5)
end, "Mine Car")

RegisterEvent(181, "Mine Car", function()
    evt.OpenChest(6)
end, "Mine Car")

RegisterEvent(182, "Mine Car", function()
    evt.OpenChest(7)
end, "Mine Car")

RegisterEvent(183, "Mine Car", function()
    evt.OpenChest(8)
end, "Mine Car")

RegisterEvent(184, "Mine Car", function()
    evt.OpenChest(9)
end, "Mine Car")

RegisterEvent(185, "Mine Car", function()
    evt.OpenChest(10)
end, "Mine Car")

RegisterEvent(186, "Mine Car", function()
    evt.OpenChest(11)
end, "Mine Car")

RegisterEvent(187, "Mine Car", function()
    evt.OpenChest(12)
end, "Mine Car")

RegisterEvent(188, "Mine Car", function()
    evt.OpenChest(13)
end, "Mine Car")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Ore Vein", function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    end
    SetValue(MapVar(16), 1)
    evt.SetTexture(1, "c2b")
end, "Ore Vein")

RegisterEvent(197, "Ore Vein", function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    end
    SetValue(MapVar(17), 1)
    evt.SetTexture(5, "c2b")
end, "Ore Vein")

RegisterEvent(198, "Ore Vein", function()
    if IsAtLeast(MapVar(18), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(18), 1)
    evt.SetTexture(6, "c2b")
end, "Ore Vein")

RegisterEvent(376, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(1, 0, "0")
        SetQBit(QBit(1689)) -- Replacement for NPCs ¹61 ver. 7
        evt.SpeakNPC(400) -- Jaycen Keldin
    end
end, "Statue")

RegisterEvent(377, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(2, 0, "0")
        SetQBit(QBit(1690)) -- Replacement for NPCs ¹62 ver. 7
        evt.SpeakNPC(401) -- Yarrow Keldin
    end
end, "Statue")

RegisterEvent(378, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(3, 0, "0")
        SetQBit(QBit(1691)) -- Replacement for NPCs ¹63 ver. 7
        evt.SpeakNPC(402) -- Fausil Keldin
    end
end, "Statue")

RegisterEvent(379, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(4, 0, "0")
        SetQBit(QBit(1692)) -- Replacement for NPCs ¹64 ver. 7
        evt.SpeakNPC(403) -- Red Keldin
    end
end, "Statue")

RegisterEvent(380, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(5, 0, "0")
        SetQBit(QBit(1693)) -- Replacement for NPCs ¹65 ver. 7
        evt.SpeakNPC(404) -- Thom Keldin
    end
end, "Statue")

RegisterEvent(381, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(6, 0, "0")
        SetQBit(QBit(1694)) -- Replacement for NPCs ¹66 ver. 7
        evt.SpeakNPC(405) -- Arvin Keldin
    end
end, "Statue")

RegisterEvent(382, "Statue", function()
    evt.ForPlayer(Players.All)
    if HasItem(1431) then -- Elixir
        evt.SetSprite(7, 0, "0")
        SetQBit(QBit(1688)) -- Replacement for NPCs ¹60 ver. 7
        evt.SpeakNPC(399) -- Drathen Keldin
    end
end, "Statue")

RegisterEvent(383, "Legacy event 383", function()
    if not IsQBitSet(QBit(543)) then return end -- Sabotage the lift in the Red Dwarf Mines in the Bracada Desert then return to Steagal Snick in Avlee.
    if IsQBitSet(QBit(570)) then return end -- Destroyed critter generator in dungeon. Warrior Mage promo quest.
    evt.ForPlayer(Players.All)
    if HasItem(1451) then -- Worn Belt
        SetQBit(QBit(570)) -- Destroyed critter generator in dungeon. Warrior Mage promo quest.
        RemoveItem(1451) -- Worn Belt
        ClearQBit(QBit(728)) -- Worn Belt - I lost it
        SetValue(Counter(4), 0)
        evt.FaceAnimation(FaceAnimation.LeaveDungeon)
    end
end)

RegisterEvent(501, "Leave the Red Dwarf Mines", function()
    evt.MoveToMap(20980, 14802, 1, 1536, 0, 0, 0, 0, "7out06.odm")
end, "Leave the Red Dwarf Mines")

