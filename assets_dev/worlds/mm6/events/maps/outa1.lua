-- Sweet Water
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {104},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    },
    textureNames = {},
    spriteNames = {"ped02"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(90, " ", function()
    if IsQBitSet(QBit(1261)) then return end -- NPC
    evt.MoveToMap(435, 3707, 1, 512, 0, 0, 165, 1, "hive.blv")
end, " ")

RegisterEvent(100, "Drink from Well.", function()
    evt.DamagePlayer(7, 2, 200)
    SetValue(Paralyzed, 0)
    evt.StatusText("Poison!")
end, "Drink from Well.")

RegisterEvent(101, "Drink from Fountain", function()
    evt.DamagePlayer(7, 2, 200)
    SetValue(Paralyzed, 0)
    evt.StatusText("Poison!")
end, "Drink from Fountain")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(MightBonus, 50) then
        SetValue(MightBonus, 50)
        SetValue(IntellectBonus, 50)
        SetValue(PersonalityBonus, 50)
        SetValue(EnduranceBonus, 50)
        SetValue(SpeedBonus, 50)
        SetValue(AccuracyBonus, 50)
        SetValue(LuckBonus, 50)
        evt.StatusText("+50 Seven Statistic temporary.")
        SetAutonote(441) -- 50 Points of temporary might, accuracy, endurance, speed, personality, intellect, and luck from the fountain southwest of the village of Sweet Water.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Pedestal", function()
    if not HasItem(2070) then return end -- Tiger Statuette
    RemoveItem(2070) -- Tiger Statuette
    evt.SetSprite(606, 1, "ped02")
    SetQBit(QBit(1246)) -- NPC
    if not IsQBitSet(QBit(1247)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> House
    end
end, "Pedestal")

RegisterEvent(104, "Legacy event 104", function()
    if IsQBitSet(QBit(1246)) then -- NPC
        evt.SetSprite(606, 1, "ped02")
    end
end)

RegisterEvent(204, "Obelisk", function()
    evt.EnterHouse(1216) -- House
end, "Obelisk")

RegisterEvent(205, " ", function()
    evt.EnterHouse(1231) -- House
end, " ")

RegisterEvent(210, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            Itotecthothesaip")
    SetQBit(QBit(1384)) -- NPC
    SetAutonote(442) -- Obelisk Message # 1: Itotecthothesaip
end, "Obelisk")

