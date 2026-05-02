-- Tomb of VARN
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [41] = {1, 6},
    [42] = {2},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [49] = {6},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 12, repeating = true, intervalGameMinutes = 1.5, remainingGameMinutes = 1.5 },
    { eventId = 14, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    },
})

RegisterEvent(1, "Well of VARN", function(continueStep)
    if continueStep == 10 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(44)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 14 then
        SetValue(MapVar(17), 1)
        RemoveItem(2157) -- Captain's Code
        ClearQBit(QBit(1255)) -- Quest item bits for seer
        evt.SetDoorState(1, DoorAction.Close)
        evt.StatusText("The waters part.")
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2157) then return end -- Captain's Code
    if not IsAtLeast(MapVar(29), 1) then
        evt.StatusText("Access Denied.  All codes must be entered first.")
        SubtractValue(CurrentHealth, 25)
        evt.FaceExpression(35)
        return
    end
    evt.SimpleMessage("What is the Captain's code?")
    evt.AskQuestion(1, 10, 44, 14, 43, 43, "Answer?  ", {"kriK", "kriK"})
    return nil
end, "Well of VARN")

RegisterEvent(2, "Picture Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Picture Door")

RegisterEvent(3, "Back Door", function()
    if not HasItem(2195) then -- Back Door Key
        evt.StatusText("The door is locked")
        return
    end
    if not IsAtLeast(ActualMight, 35) then
        evt.StatusText("Door won't budge.")
        return
    end
    RemoveItem(2195) -- Back Door Key
    evt.SetDoorState(3, DoorAction.Close)
end, "Back Door")

RegisterEvent(4, "Picture Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Picture Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Picture Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Picture Door")

RegisterEvent(7, "Picture Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Picture Door")

RegisterEvent(8, "Switch", function()
    evt.SetDoorState(8, DoorAction.Trigger)
    evt.StatusText("Trap!")
    evt.DamagePlayer(7, 0, 200)
end, "Switch")

RegisterEvent(9, "Switch", function()
    evt.SetDoorState(9, DoorAction.Trigger)
    evt.StatusText("Trap!")
    evt.DamagePlayer(7, 5, 200)
end, "Switch")

RegisterEvent(10, "Picture Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Picture Door")

RegisterEvent(11, "Water Temple", function()
    if not HasItem(2193) then -- Water Temple Key
        evt.StatusText("The door is locked")
        return
    end
    RemoveItem(2193) -- Water Temple Key
    evt.SetDoorState(11, DoorAction.Close)
end, "Water Temple")

RegisterEvent(12, "Legacy event 12", function()
    if not IsAtLeast(MapVar(2), 1) then return end
    evt.ForPlayer(6)
    if not HasItem(2086) then -- Crystal Skull
        local randomStep = PickRandomOption(12, 6, {6, 9, 12, 15, 18, 21})
        if randomStep == 6 then
            evt.DamagePlayer(5, 2, 5)
            evt.StatusText("Radiation Damage!")
            return
        elseif randomStep == 9 then
            evt.DamagePlayer(5, 0, 5)
            evt.StatusText("Radiation Damage!")
            return
        elseif randomStep == 12 then
            evt.DamagePlayer(5, 1, 5)
            evt.StatusText("Radiation Damage!")
            return
        elseif randomStep == 15 then
            evt.DamagePlayer(5, 5, 5)
            evt.StatusText("Radiation Damage!")
            return
        elseif randomStep == 18 then
            evt.DamagePlayer(5, 4, 5)
            evt.StatusText("Radiation Damage!")
            return
        elseif randomStep == 21 then
            evt.DamagePlayer(5, 8, 5)
            evt.StatusText("Radiation Damage!")
            return
        end
    end
    evt.StatusText("Crystal Skull absorbs radiation damage.")
end)

RegisterEvent(13, "Cleansing Pool", function()
    SetValue(MapVar(2), 0)
end, "Cleansing Pool")

RegisterEvent(14, "Legacy event 14", function()
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        if IsAtLeast(MapVar(5), 1) then
            evt.StatusText("Main Power failed.  Emergency power on.")
        end
        evt.SetLight(35, 0)
        evt.SetLight(43, 0)
        evt.SetLight(34, 0)
        evt.SetLight(36, 0)
        evt.SetLight(37, 0)
        evt.SetLight(33, 0)
        evt.SetLight(42, 1)
        evt.SetLight(41, 1)
        evt.SetLight(38, 1)
        evt.SetLight(40, 1)
        evt.SetLight(39, 1)
        return
    end
    SetValue(MapVar(4), 0)
    if IsAtLeast(MapVar(5), 1) then
        AddValue(MapVar(5), 1)
        evt.StatusText("Main Power restored.")
    end
    evt.SetLight(35, 1)
    evt.SetLight(43, 1)
    evt.SetLight(34, 1)
    evt.SetLight(36, 1)
    evt.SetLight(37, 1)
    evt.SetLight(33, 1)
    evt.SetLight(42, 0)
    evt.SetLight(41, 0)
    evt.SetLight(38, 0)
    evt.SetLight(40, 0)
    evt.SetLight(39, 0)
    if IsAtLeast(MapVar(5), 3) then
        SetValue(MapVar(5), 0)
    end
end)

RegisterEvent(15, "Legacy event 15", function()
    evt.SetDoorState(15, DoorAction.Close)
end)

RegisterEvent(16, "Picture Door", function()
    if not IsAtLeast(ActualMight, 25) then
        evt.StatusText("Door won't budge.")
        return
    end
    evt.SetDoorState(16, DoorAction.Close)
end, "Picture Door")

RegisterEvent(17, "Exit", function()
    evt.MoveToMap(-6647, 13018, 1761, 1536, 0, 0, 0, 0, "outb3.odm")
end, "Exit")

RegisterEvent(18, "Exit", function()
    evt.MoveToMap(-6611, 11408, 480, 1536, 0, 0, 0, 0, "outb3.odm")
end, "Exit")

RegisterEvent(19, "Picture", nil, "Picture")

RegisterEvent(20, "Legacy event 20", function()
    evt.SetDoorState(16, DoorAction.Open)
end)

RegisterEvent(21, "Cleansing Pool", function(continueStep)
    if continueStep == 5 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(48)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 9 then
        if IsAtLeast(MapVar(13), 1) and IsAtLeast(MapVar(14), 1) and IsAtLeast(MapVar(15), 1) and IsAtLeast(MapVar(16), 1) then
            SetValue(MapVar(29), 1)
        else
        end
        SetValue(MapVar(12), 1)
        evt.ForPlayer(Players.All)
        RemoveItem(2158) -- First Mate's Code
        ClearQBit(QBit(1253)) -- Quest item bits for seer
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2158) then return end -- First Mate's Code
    evt.SimpleMessage("What is the first mate's code?")
    evt.AskQuestion(21, 5, 44, 9, 33, 33, "Answer?  ", {"kcopS", "kcopS"})
    return nil
end, "Cleansing Pool")

RegisterEvent(22, "Cleansing Pool", function(continueStep)
    if continueStep == 5 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(33)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 9 then
        if IsAtLeast(MapVar(12), 1) and IsAtLeast(MapVar(14), 1) and IsAtLeast(MapVar(15), 1) and IsAtLeast(MapVar(16), 1) then
            SetValue(MapVar(29), 1)
        else
        end
        SetValue(MapVar(13), 1)
        evt.ForPlayer(Players.All)
        RemoveItem(2159) -- Navigator's Code
        ClearQBit(QBit(1256)) -- Quest item bits for seer
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2159) then return end -- Navigator's Code
    evt.SimpleMessage("What is the navigator's code?")
    evt.AskQuestion(22, 5, 44, 9, 35, 35, "Answer?  ", {"uluS", "uluS"})
    return nil
end, "Cleansing Pool")

RegisterEvent(23, "Cleansing Pool", function(continueStep)
    if continueStep == 5 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(50)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 9 then
        if IsAtLeast(MapVar(13), 1) and IsAtLeast(MapVar(12), 1) and IsAtLeast(MapVar(15), 1) and IsAtLeast(MapVar(16), 1) then
            SetValue(MapVar(29), 1)
        else
        end
        SetValue(MapVar(14), 1)
        evt.ForPlayer(Players.All)
        RemoveItem(2160) -- Communication Officer's Code
        ClearQBit(QBit(1258)) -- Quest item bits for seer
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2160) then return end -- Communication Officer's Code
    evt.SimpleMessage("What is the communication officer's code?")
    evt.AskQuestion(23, 5, 44, 9, 37, 37, "Answer?  ", {"aruhU", "aruhU"})
    return nil
end, "Cleansing Pool")

RegisterEvent(24, "Cleansing Pool", function(continueStep)
    if continueStep == 5 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(46)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 9 then
        if IsAtLeast(MapVar(13), 1) and IsAtLeast(MapVar(14), 1) and IsAtLeast(MapVar(12), 1) and IsAtLeast(MapVar(16), 1) then
            SetValue(MapVar(29), 1)
        else
        end
        SetValue(MapVar(15), 1)
        evt.ForPlayer(Players.All)
        RemoveItem(2161) -- Engineer's Code
        ClearQBit(QBit(1257)) -- Quest item bits for seer
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2161) then return end -- Engineer's Code
    evt.SimpleMessage("What is the engineer's code?")
    evt.AskQuestion(24, 5, 44, 9, 39, 39, "Answer?  ", {"yttocS", "yttocS"})
    return nil
end, "Cleansing Pool")

RegisterEvent(25, "Cleansing Pool", function(continueStep)
    if continueStep == 5 then
        evt.StatusText("Incorrect.")
        evt.FaceExpression(13)
        SubtractValue(CurrentHealth, 5)
        return
    end
    if continueStep == 9 then
        if IsAtLeast(MapVar(13), 1) and IsAtLeast(MapVar(14), 1) and IsAtLeast(MapVar(15), 1) and IsAtLeast(MapVar(12), 1) then
            SetValue(MapVar(29), 1)
        else
        end
        SetValue(MapVar(16), 1)
        evt.ForPlayer(Players.All)
        RemoveItem(2162) -- Doctor's Code
        ClearQBit(QBit(1254)) -- Quest item bits for seer
    end
    if continueStep ~= nil then return end
    SetValue(MapVar(2), 0)
    if not HasItem(2162) then return end -- Doctor's Code
    evt.SimpleMessage("What is the doctor's code?")
    evt.AskQuestion(25, 5, 44, 9, 41, 41, "Answer?  ", {"yoccM", "yoccM"})
    return nil
end, "Cleansing Pool")

RegisterEvent(26, "Books", function()
    if IsAtLeast(MapVar(27), 1) then return end
    SetQBit(QBit(1258)) -- Quest item bits for seer
    AddValue(InventoryItem(2160), 2160) -- Communication Officer's Code
    SetValue(MapVar(27), 1)
end, "Books")

RegisterEvent(27, "Books", function()
    if IsAtLeast(MapVar(28), 1) then return end
    SetQBit(QBit(1257)) -- Quest item bits for seer
    AddValue(InventoryItem(2161), 2161) -- Engineer's Code
    SetValue(MapVar(28), 1)
end, "Books")

RegisterEvent(28, "Legacy event 28", function()
    SetValue(MapVar(5), 1)
end)

RegisterEvent(29, "Switch", function()
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
end, "Switch")

RegisterEvent(30, "Picture Door", function()
    if not IsAtLeast(ActualMight, 20) then
        evt.StatusText("Door won't budge.")
        return
    end
    evt.SetDoorState(35, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Close)
end, "Picture Door")

RegisterEvent(31, "Flame Door", function()
    if not HasItem(2194) then -- Flame Door Key
        evt.StatusText("The door is locked")
        return
    end
    if not IsAtLeast(ActualMight, 25) then
        evt.StatusText("Door won't budge.")
        return
    end
    RemoveItem(2194) -- Flame Door Key
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Close)
end, "Flame Door")

RegisterEvent(32, "Switch", function()
    evt.SetDoorState(33, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Trigger)
end, "Switch")

RegisterEvent(33, "Legacy event 33", function()
    evt.MoveToMap(-9344, -192, 8034, 1, 0, 0, 0, 0)
    evt.SetDoorState(33, DoorAction.Open)
end)

RegisterEvent(35, "Control Room Entry", function()
    if IsAtLeast(MapVar(17), 1) then
        evt.SetDoorState(39, DoorAction.Close)
        evt.SetDoorState(40, DoorAction.Close)
    end
end, "Control Room Entry")

RegisterEvent(41, "Chest", function()
    if not IsAtLeast(MapVar(30), 1) then
        if IsQBitSet(QBit(1066)) then -- Bruce
            evt.OpenChest(6)
        elseif HasItem(2197) then -- VARN Chest Key
            RemoveItem(2197) -- VARN Chest Key
            SetValue(MapVar(30), 1)
            evt.OpenChest(1)
            SetQBit(QBit(1066)) -- Bruce
            SetQBit(QBit(1219)) -- Quest item bits for seer
        else
            evt.StatusText("The chest is locked")
        end
        return
    end
    evt.OpenChest(1)
    SetQBit(QBit(1066)) -- Bruce
    SetQBit(QBit(1219)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(2)
    SetQBit(QBit(1253)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(43, "Chest", function()
    if not IsAtLeast(MapVar(51), 1) then
        if not HasItem(2196) then -- Bibliotheca Chest Key
            evt.StatusText("The chest is locked")
            return
        end
        RemoveItem(2196) -- Bibliotheca Chest Key
        SetValue(MapVar(51), 1)
    end
    evt.OpenChest(3)
    SetQBit(QBit(1254)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(4)
    SetQBit(QBit(1255)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(5)
    SetQBit(QBit(1256)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(46, "Plaque", function()
    evt.SimpleMessage("Warning!  Sensor array controls are strictly off limits to unauthorized personnel!  Use of the Sign of Sight is restricted to communications technicians only!  A mild electric shock will be transmitted to violators.")
end, "Plaque")

RegisterEvent(47, "Plaque", function()
    evt.SimpleMessage("Warning!  Cargo lift controls are strictly off limits to unauthorized personnel!  Use of the Sign of the Scarab is restricted to supply officers only!  A mild electric shock will be transmitted to violators.")
end, "Plaque")

RegisterEvent(48, "Plaque", function()
    evt.SimpleMessage("The entrance to the central pyramid lies to the South.")
end, "Plaque")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(51, "Legacy event 51", function()
    SetValue(MapVar(2), 1)
end)

RegisterEvent(52, "Plaque", function()
    evt.SimpleMessage("Only the one bearing the key may speak the code.")
end, "Plaque")

RegisterEvent(53, "Plaque", function()
    evt.SimpleMessage("The Well of VARN must be keyed last.")
end, "Plaque")

RegisterEvent(54, "Plaque", function()
    evt.SimpleMessage("Warning!  Power Fluctuations!  Alert Engineering immediately!")
end, "Plaque")

RegisterEvent(55, "Plaque", function()
    evt.SimpleMessage("\"In case of energy leak, bathe in one of the medicated pools placed for your safety and convenience.\"")
end, "Plaque")

RegisterEvent(56, "Legacy event 56", function()
    SetValue(MapVar(2), 0)
end)

RegisterEvent(57, "Legacy event 57", function()
    SetValue(MapVar(5), 0)
end)

RegisterEvent(60, "Bookcase", function()
    if IsAtLeast(MapVar(31), 1) then return end
    SetValue(MapVar(31), 1)
    AddValue(InventoryItem(1912), 1912) -- Meteor Shower
end, "Bookcase")

RegisterEvent(61, "Bookcase", function()
    if IsAtLeast(MapVar(32), 1) then return end
    SetValue(MapVar(32), 1)
    AddValue(InventoryItem(1913), 1913) -- Inferno
end, "Bookcase")

RegisterEvent(62, "Bookcase", function()
    if IsAtLeast(MapVar(33), 1) then return end
    SetValue(MapVar(33), 1)
    AddValue(InventoryItem(1914), 1914) -- Incinerate
end, "Bookcase")

RegisterEvent(63, "Bookcase", function()
    if IsAtLeast(MapVar(34), 1) then return end
    SetValue(MapVar(34), 1)
    AddValue(InventoryItem(1925), 1925) -- Implosion
end, "Bookcase")

RegisterEvent(64, "Bookcase", function()
    if IsAtLeast(MapVar(35), 1) then return end
    SetValue(MapVar(35), 1)
    AddValue(InventoryItem(1926), 1926) -- Fly
end, "Bookcase")

RegisterEvent(65, "Bookcase", function()
    if IsAtLeast(MapVar(36), 1) then return end
    SetValue(MapVar(36), 1)
    AddValue(InventoryItem(1927), 1927) -- Starburst
end, "Bookcase")

RegisterEvent(66, "Bookcase", function()
    if IsAtLeast(MapVar(37), 1) then return end
    SetValue(MapVar(37), 1)
    AddValue(InventoryItem(1938), 1938) -- Town Portal
end, "Bookcase")

RegisterEvent(67, "Bookcase", function()
    if IsAtLeast(MapVar(38), 1) then return end
    SetValue(MapVar(38), 1)
    AddValue(InventoryItem(1939), 1939) -- Ice Blast
end, "Bookcase")

RegisterEvent(68, "Bookcase", function()
    if IsAtLeast(MapVar(39), 1) then return end
    SetValue(MapVar(39), 1)
    AddValue(InventoryItem(1940), 1940) -- Lloyd's Beacon
end, "Bookcase")

RegisterEvent(69, "Bookcase", function()
    if IsAtLeast(MapVar(40), 1) then return end
    SetValue(MapVar(40), 1)
    AddValue(InventoryItem(1951), 1951) -- Telekinesis
end, "Bookcase")

RegisterEvent(70, "Bookcase", function()
    if IsAtLeast(MapVar(41), 1) then return end
    SetValue(MapVar(41), 1)
    AddValue(InventoryItem(1952), 1952) -- Death Blossom
end, "Bookcase")

RegisterEvent(71, "Bookcase", function()
    if IsAtLeast(MapVar(42), 1) then return end
    SetValue(MapVar(42), 1)
    AddValue(InventoryItem(1953), 1953) -- Mass Distortion
end, "Bookcase")

RegisterEvent(72, "Tapestry", function()
    evt.SimpleMessage("\"With painstaking care, you are able to decipher the message of the hieroglyphs:                                                                                                                                                     Though the Crossing of the Void be a long and arduous journey, the land you find at the end will be sweet and unspoiled by ancestors or the Enemy.  Take heart that your children's children will live in a perfect world free of war, free of famine, and free of fear.  Remember your sacred duty to care for the Ship on her long Voyage and ensure her safe arrival in the Promised Land.  Tend well the Guardian and house it securely away from the ship lest both be lost in a single misfortune.\"")
end, "Tapestry")

RegisterEvent(73, "Tapestry", function()
    evt.SimpleMessage("\"With painstaking care, you are able to decipher the message of the hieroglyphs, intermixed with diagrams of devils:                                                                                          Remember our Enemy, children, and never underestimate the danger they pose.  Though you will never see one during your journey, you must be forever vigilant against invasion from the Void once the Voyage has ended.  Mighty beyond words, the Enemy is nonetheless vulnerable after a Crossing, for their numbers are small and their defenses weak.  Use the energy weapons carried on the Ship to defeat them, and never, ever engage the Enemy with lesser weapons, or you will surely perish.\"")
end, "Tapestry")

