-- Harmondale
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {50, 65535, 65534, 211, 240, 249, 250},
    onLeave = {},
    openedChestIds = {
    [112] = {1},
    [113] = {2},
    [114] = {3},
    [115] = {4},
    [116] = {5},
    [117] = {6},
    [118] = {7},
    [119] = {8},
    [120] = {9},
    [121] = {10},
    [122] = {11},
    [123] = {12},
    },
    textureNames = {"chb1", "chb1dl", "chb1dr", "chb1el", "chb1er", "chb1s", "chbw"},
    spriteNames = {"0", "7tree01", "7tree07", "7tree13", "7tree14", "7tree15", "7tree16", "7tree17", "7tree18", "7tree22", "7tree24", "7tree30", "tree37", "v77dec24"},
    castSpellIds = {2, 6, 15, 43},
    timers = {
    { eventId = 51, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    { eventId = 229, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(1, "Legacy event 1", nil)

RegisterEvent(2, "Castle Harmondale", nil, "Castle Harmondale")

RegisterEvent(3, "Tempered Steel", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(9) -- Tempered Steel
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Tempered Steel")

RegisterEvent(4, "Tempered Steel", nil, "Tempered Steel")

RegisterEvent(5, "The Peasant's Smithy", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(47) -- The Peasant's Smithy
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Peasant's Smithy")

RegisterEvent(6, "The Peasant's Smithy", nil, "The Peasant's Smithy")

RegisterEvent(7, "Otto's Oddities", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(85) -- Otto's Oddities
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Otto's Oddities")

RegisterEvent(8, "Otto's Oddities", nil, "Otto's Oddities")

RegisterEvent(9, "Philters and Elixirs", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(117) -- Philters and Elixirs
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Philters and Elixirs")

RegisterEvent(10, "Philters and Elixirs", nil, "Philters and Elixirs")

RegisterEvent(11, "WelNin Cathedral", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(311) -- WelNin Cathedral
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "WelNin Cathedral")

RegisterEvent(12, "WelNin Cathedral", nil, "WelNin Cathedral")

RegisterEvent(13, "Basic Principles", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1571) -- Basic Principles
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Basic Principles")

RegisterEvent(14, "Basic Principles", nil, "Basic Principles")

RegisterEvent(15, "On the House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(240) -- On the House
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "On the House")

RegisterEvent(16, "On the House", nil, "On the House")

RegisterEvent(17, "Adept Guild of Fire", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(129) -- Adept Guild of Fire
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Adept Guild of Fire")

RegisterEvent(18, "Adept Guild of Fire", nil, "Adept Guild of Fire")

RegisterEvent(19, "Adept Guild of Air", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(135) -- Adept Guild of Air
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Adept Guild of Air")

RegisterEvent(20, "Adept Guild of Air", nil, "Adept Guild of Air")

RegisterEvent(21, "Adept Guild of Spirit", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(153) -- Adept Guild of Spirit
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Adept Guild of Spirit")

RegisterEvent(22, "Adept Guild of Spirit", nil, "Adept Guild of Spirit")

RegisterEvent(23, "Adept Guild of Body", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(165) -- Adept Guild of Body
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Adept Guild of Body")

RegisterEvent(24, "Adept Guild of Body", nil, "Adept Guild of Body")

RegisterEvent(25, "Initiate Guild of Water", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(140) -- Initiate Guild of Water
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Initiate Guild of Water")

RegisterEvent(26, "Initiate Guild of Water", nil, "Initiate Guild of Water")

RegisterEvent(27, "Initiate Guild of Earth", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(146) -- Initiate Guild of Earth
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Initiate Guild of Earth")

RegisterEvent(28, "Initiate Guild of Earth", nil, "Initiate Guild of Earth")

RegisterEvent(29, "Initiate Guild of Mind", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(158) -- Initiate Guild of Mind
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Initiate Guild of Mind")

RegisterEvent(30, "Initiate Guild of Mind", nil, "Initiate Guild of Mind")

RegisterEvent(31, "The Vault", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(286) -- The Vault
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The Vault")

RegisterEvent(32, "The Vault", nil, "The Vault")

RegisterEvent(33, "Harmondale Townhall", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(203) -- Harmondale Townhall
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Harmondale Townhall")

RegisterEvent(34, "Harmondale Townhall", nil, "Harmondale Townhall")

RegisterEvent(35, "The J.V.C Corral", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(461) -- The J.V.C Corral
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "The J.V.C Corral")

RegisterEvent(36, "The J.V.C Corral", nil, "The J.V.C Corral")

RegisterEvent(37, "Arbiter", function()
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        goto step_40
    end
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark
        goto step_75
    end
    if IsQBitSet(QBit(1697)) then -- Replacement for NPCs ¹77 ver. 7
        goto step_7
    end
    if IsQBitSet(QBit(1698)) then -- Replacement for NPCs ¹78 ver. 7
        goto step_42
    end
    if IsQBitSet(QBit(646)) then -- Arbiter Messenger only happens once
        return
    end
    evt.EnterHouse(1165) -- Arbiter
    do return end
    ::step_7::
    if IsQBitSet(QBit(592)) then -- Gave plans to elfking
        goto step_15
    end
    if IsQBitSet(QBit(594)) then -- Gave false plans to elfking (betray)
        goto step_13
    end
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_11
    end
    goto step_22
    ::step_11::
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_24
    end
    goto step_22
    ::step_13::
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_19
    end
    goto step_22
    ::step_15::
    if IsQBitSet(QBit(593)) then -- Gave Loren to Catherine
        goto step_19
    end
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_24
    end
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_24
    end
    goto step_22
    ::step_19::
    if IsQBitSet(QBit(659)) then -- Gave artifact to arbiter
        goto step_26
    end
    if IsQBitSet(QBit(596)) then -- Gave artifact to humans
        goto step_22
    end
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_24
    end
    ::step_22::
    AddValue(History(9), 0)
    goto step_27
    ::step_24::
    AddValue(History(10), 0)
    goto step_27
    ::step_26::
    AddValue(History(11), 0)
    ::step_27::
    SetQBit(QBit(611)) -- Chose the path of Light
    ClearQBit(QBit(665)) -- Choose a judge to succeed Judge Grey as Arbiter in Harmondale.
    SetQBit(QBit(664)) -- Enter Celeste from the grand teleporter in the Bracada Desert, then talk to Gavin Magnus in Castle Lambent in Celeste.
    SetValue(Counter(5), 0)
    evt.SetNPCGreeting(416, 221) -- Judge Fairweather greeting: You have made the wise choice, my lords. Gavin Magnus, leader of the Wizards, would like to speak with you. Go to the Bracada Desert-- the teleporter to Celeste will function now, and use it to enter Celeste. Gavin awaits you in Castle Lambent. Time is precious; don't waste it dallying around.
    ClearQBit(QBit(1697)) -- Replacement for NPCs ¹77 ver. 7
    evt.MoveNPC(416, 1164) -- Judge Fairweather -> Arbiter
    evt.MoveNPC(417, 0) -- Judge Sleen -> removed
    evt.MoveNPC(414, 0) -- Ambassador Wright -> removed
    evt.MoveNPC(415, 0) -- Ambassador Scale -> removed
    evt.SetNPCTopic(416, 1, 894) -- Judge Fairweather topic 1: Hint
    evt.SetNPCTopic(416, 2, 889) -- Judge Fairweather topic 2: I lost it
    evt.ShowMovie("\"arbiter good\"", true)
    ::step_40::
    evt.EnterHouse(1164) -- Arbiter
    do return end
    ::step_42::
    if IsQBitSet(QBit(592)) then -- Gave plans to elfking
        goto step_50
    end
    if IsQBitSet(QBit(594)) then -- Gave false plans to elfking (betray)
        goto step_48
    end
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_46
    end
    goto step_57
    ::step_46::
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_59
    end
    goto step_57
    ::step_48::
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_54
    end
    goto step_57
    ::step_50::
    if IsQBitSet(QBit(593)) then -- Gave Loren to Catherine
        goto step_54
    end
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_59
    end
    if IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
        goto step_59
    end
    goto step_57
    ::step_54::
    if IsQBitSet(QBit(659)) then -- Gave artifact to arbiter
        goto step_61
    end
    if IsQBitSet(QBit(596)) then -- Gave artifact to humans
        goto step_57
    end
    if IsQBitSet(QBit(597)) then -- Gave artifact to elves
        goto step_59
    end
    ::step_57::
    AddValue(History(16), 0)
    goto step_62
    ::step_59::
    AddValue(History(17), 0)
    goto step_62
    ::step_61::
    AddValue(History(18), 0)
    ::step_62::
    SetQBit(QBit(612)) -- Chose the path of Dark
    ClearQBit(QBit(665)) -- Choose a judge to succeed Judge Grey as Arbiter in Harmondale.
    SetQBit(QBit(663)) -- Enter the Pit from the Hall of the Pit in the Deyja Moors, then talk to Archibald in Castle Gloaming in the Pit.
    SetValue(Counter(5), 0)
    evt.SetNPCGreeting(417, 218) -- Judge Sleen greeting: You have made the right choice, my lords. The leader of Deyja, Archibald Ironfist, would like to speak with you. From the Deyja Moors, enter the Hall of the Pit and make your way to the Pit. Archibald awaits you in Castle Gloaming in the Pit. Try not to keep him waiting.
    ClearQBit(QBit(1698)) -- Replacement for NPCs ¹78 ver. 7
    evt.MoveNPC(414, 0) -- Ambassador Wright -> removed
    evt.MoveNPC(416, 0) -- Judge Fairweather -> removed
    evt.MoveNPC(415, 0) -- Ambassador Scale -> removed
    evt.MoveNPC(417, 1166) -- Judge Sleen -> Arbiter
    evt.SetNPCTopic(417, 1, 892) -- Judge Sleen topic 1: Hint
    evt.SetNPCTopic(417, 2, 889) -- Judge Sleen topic 2: I lost it
    evt.ShowMovie("\"arbiter evil\"", true)
    ::step_75::
    evt.EnterHouse(1166) -- Arbiter
end, "Arbiter")

RegisterEvent(50, "Legacy event 50", function()
    if IsQBitSet(QBit(526)) then -- Accepted Fireball wand from Malwick
        if IsQBitSet(QBit(702)) then -- Finished with Malwick & Assc.
            if not IsQBitSet(QBit(519)) then return end -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        elseif IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
            evt.SetMonGroupBit(60, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(60, MonsterBits.Invisible, 0)
            SetValue(BankGold, 0)
            ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            if not IsQBitSet(QBit(519)) then return end -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        elseif IsQBitSet(QBit(694)) then -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            if IsAtLeast(Counter(5), 672) then
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SpeakNPC(437) -- Messenger
                evt.SetMonGroupBit(60, MonsterBits.Hostile, 1)
                evt.SetMonGroupBit(60, MonsterBits.Invisible, 0)
                SetValue(BankGold, 0)
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            if not IsQBitSet(QBit(519)) then return end -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        elseif IsQBitSet(QBit(693)) then -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            if IsAtLeast(Counter(5), 336) then
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SpeakNPC(437) -- Messenger
                evt.SetMonGroupBit(60, MonsterBits.Hostile, 1)
                evt.SetMonGroupBit(60, MonsterBits.Invisible, 0)
                SetValue(BankGold, 0)
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            if not IsQBitSet(QBit(519)) then return end -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        elseif IsQBitSet(QBit(608)) then -- Built Castle to Level 3 (good)NO LONGER USED(Riki)
            SetValue(Counter(5), 0)
            AddValue(InventoryItem(1506), 1506) -- Message from Mr. Stantley
            evt.SpeakNPC(437) -- Messenger
            SetQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            if not IsQBitSet(QBit(519)) then return end -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        elseif IsQBitSet(QBit(519)) then -- Finished Scavenger Hunt
            if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
            SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
            evt.ShowMovie("\"pcout01\"", true)
            return
        else
            return
        end
    elseif IsQBitSet(QBit(519)) then -- Finished Scavenger Hunt
        if IsQBitSet(QBit(648)) then return end -- Party doesn't come back to Out01 temple anymore
        SetQBit(QBit(648)) -- Party doesn't come back to Out01 temple anymore
        evt.ShowMovie("\"pcout01\"", true)
        return
    else
        return
    end
end)

RegisterEvent(51, "Legacy event 51", function()
    if not IsQBitSet(QBit(695)) then return end -- Failed either goto or do guild quest
    if IsQBitSet(QBit(697)) then return end -- Killed all outdoor monsters
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 60, 0, false) then return end -- actor group 60; all matching actors defeated
    evt.ForPlayer(Players.All)
    SetQBit(QBit(697)) -- Killed all outdoor monsters
    if IsQBitSet(QBit(696)) then -- Killed all castle monsters
        evt.ForPlayer(Players.All)
        SetQBit(QBit(702)) -- Finished with Malwick & Assc.
        ClearQBit(QBit(695)) -- Failed either goto or do guild quest
    end
end)

RegisterEvent(110, "Legacy event 110", function()
    if not IsQBitSet(QBit(645)) then -- Player castle timer only happens once
        SetValue(Counter(3), 0)
        SetQBit(QBit(645)) -- Player castle timer only happens once
    end
    evt.SetTexture(1, "chb1dl")
    evt.SetTexture(2, "chb1dr")
    evt.SetTexture(3, "chb1el")
    evt.SetTexture(4, "chb1er")
    evt.SetTexture(5, "chb1s")
    evt.SetTexture(6, "chb1")
    evt.SetTexture(11, "chb1el")
    evt.SetTexture(12, "chb1")
    evt.SetTexture(13, "chb1er")
    evt.SetTexture(14, "chb1s")
    evt.SetTexture(15, "chbw")
    evt.SetTexture(7, "chbw")
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(15, FacetBits.Invisible, 0)
    evt.SetSprite(1, 1, "7tree07")
    evt.SetSprite(2, 1, "7tree01")
    if IsAtLeast(History(7), 0) then return end
    AddValue(History(7), 0)
end)

RegisterEvent(111, "Legacy event 111", function()
    evt.SetFacetBit(20, FacetBits.Untouchable, 0)
    evt.SetFacetBit(20, FacetBits.Invisible, 0)
    evt.SetFacetBit(15, FacetBits.Invisible, 1)
    evt.SetFacetBit(11, FacetBits.Invisible, 1)
    evt.SetFacetBit(12, FacetBits.Invisible, 1)
    evt.SetFacetBit(13, FacetBits.Invisible, 1)
    evt.SetFacetBit(14, FacetBits.Invisible, 1)
    evt.SetFacetBit(15, FacetBits.Invisible, 1)
    evt.SetFacetBit(16, FacetBits.Invisible, 1)
end)

RegisterEvent(112, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(113, "Crate", function()
    evt.OpenChest(2)
end, "Crate")

RegisterEvent(114, "Crate", function()
    evt.OpenChest(3)
end, "Crate")

RegisterEvent(115, "Crate", function()
    evt.OpenChest(4)
end, "Crate")

RegisterEvent(116, "Crate", function()
    evt.OpenChest(5)
end, "Crate")

RegisterEvent(117, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(118, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(119, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(120, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(121, "Crate", function()
    evt.OpenChest(10)
end, "Crate")

RegisterEvent(122, "Crate", function()
    evt.OpenChest(11)
end, "Crate")

RegisterEvent(123, "Crate", function()
    evt.OpenChest(12)
end, "Crate")

RegisterEvent(150, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(52), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(52), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(51, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(151, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(53), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(53), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(52, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(152, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(54), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(54), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(53, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(153, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(55), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(55), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(54, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(154, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(56), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(56), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(55, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(155, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(57), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(57), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(56, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(156, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(58), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(58), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(57, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(157, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(59), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(59), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(58, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(211, "Legacy event 211", function()
    if IsQBitSet(QBit(646)) then -- Arbiter Messenger only happens once
        return
    elseif IsQBitSet(QBit(659)) then -- Gave artifact to arbiter
        evt.SpeakNPC(430) -- Messenger
        SetQBit(QBit(665)) -- Choose a judge to succeed Judge Grey as Arbiter in Harmondale.
        AddValue(History(8), 0)
        evt.MoveNPC(406, 0) -- Ellen Rockway -> removed
        evt.MoveNPC(407, 0) -- Alain Hani -> removed
        evt.MoveNPC(414, 1169) -- Ambassador Wright -> Throne Room
        evt.MoveNPC(415, 1169) -- Ambassador Scale -> Throne Room
        evt.MoveNPC(416, 244) -- Judge Fairweather -> Familiar Place
        evt.MoveNPC(417, 243) -- Judge Sleen -> The Snobbish Goblin
        SetQBit(QBit(646)) -- Arbiter Messenger only happens once
        return
    elseif IsQBitSet(QBit(596)) then -- Gave artifact to humans
        evt.SpeakNPC(430) -- Messenger
        SetQBit(QBit(665)) -- Choose a judge to succeed Judge Grey as Arbiter in Harmondale.
        AddValue(History(8), 0)
        evt.MoveNPC(406, 0) -- Ellen Rockway -> removed
        evt.MoveNPC(407, 0) -- Alain Hani -> removed
        evt.MoveNPC(414, 1169) -- Ambassador Wright -> Throne Room
        evt.MoveNPC(415, 1169) -- Ambassador Scale -> Throne Room
        evt.MoveNPC(416, 244) -- Judge Fairweather -> Familiar Place
        evt.MoveNPC(417, 243) -- Judge Sleen -> The Snobbish Goblin
        SetQBit(QBit(646)) -- Arbiter Messenger only happens once
        return
    elseif IsQBitSet(QBit(597)) then -- Gave artifact to elves
        evt.SpeakNPC(430) -- Messenger
        SetQBit(QBit(665)) -- Choose a judge to succeed Judge Grey as Arbiter in Harmondale.
        AddValue(History(8), 0)
        evt.MoveNPC(406, 0) -- Ellen Rockway -> removed
        evt.MoveNPC(407, 0) -- Alain Hani -> removed
        evt.MoveNPC(414, 1169) -- Ambassador Wright -> Throne Room
        evt.MoveNPC(415, 1169) -- Ambassador Scale -> Throne Room
        evt.MoveNPC(416, 244) -- Judge Fairweather -> Familiar Place
        evt.MoveNPC(417, 243) -- Judge Sleen -> The Snobbish Goblin
        SetQBit(QBit(646)) -- Arbiter Messenger only happens once
        return
    else
        return
    end
end)

RegisterEvent(212, "North to the Tularean Forest", nil, "North to the Tularean Forest")

RegisterEvent(213, "West to Erathia", nil, "West to Erathia")

RegisterEvent(214, "South to Barrow Downs", nil, "South to Barrow Downs")

RegisterEvent(215, "East", nil, "East")

RegisterEvent(216, "Harmondale", nil, "Harmondale")

RegisterEvent(217, "Well", nil, "Well")

RegisterEvent(218, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(1)) then
        AddValue(MightBonus, 10)
        SetPlayerBit(PlayerBit(1))
        evt.StatusText("+ 10 Might (Temporary)")
        SetAutonote(262) -- 10 points of temporary Might from the well in the village south of Harmondale.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(219, "Castle Harmondale", nil, "Castle Harmondale")

RegisterEvent(220, "Obelisk", function()
    if IsQBitSet(QBit(676)) then return end -- Visited Obelisk in Area 2
    evt.StatusText("pohuwwba")
    SetAutonote(309) -- Obelisk message #1: pohuwwba
    evt.ForPlayer(Players.All)
    SetQBit(QBit(676)) -- Visited Obelisk in Area 2
end, "Obelisk")

RegisterEvent(221, "Altar", function()
    if not IsQBitSet(QBit(758)) then -- Visited The Land of the giants
        evt.StatusText("You Pray")
        return
    end
    evt.MoveToMap(4221, 17840, 769, 1536, 0, 0, 0, 0)
end, "Altar")

RegisterEvent(222, "Shrine", nil, "Shrine")

RegisterEvent(223, "Drink from the Well", function()
    if not IsAtLeast(BankGold, 99) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(MapVar(21), 1) then
            evt.StatusText("Refreshing!")
            return
        else
            AddValue(Gold, 200)
            SetValue(MapVar(21), 1)
            evt.StatusText("Refreshing!")
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(227, "Drink from the Fountain", function()
    if not IsAtLeast(PoisonedYellow, 0) then
        if IsAtLeast(PoisonedRed, 0) then
            evt.StatusText("You probably shouldn't do that.")
            return
        elseif IsAtLeast(Paralyzed, 0) then
            evt.StatusText("You probably shouldn't do that.")
        else
            local randomStep = PickRandomOption(227, 4, {5, 7, 9})
            if randomStep == 5 then
                SetValue(PoisonedYellow, 0)
            elseif randomStep == 7 then
                SetValue(PoisonedRed, 0)
            elseif randomStep == 9 then
                SetValue(Paralyzed, 0)
            end
            evt.StatusText("Maybe that wasn't such a good idea.")
        end
    return
    end
    evt.StatusText("You probably shouldn't do that.")
end, "Drink from the Fountain")

RegisterEvent(228, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(2)) then
        AddValue(BaseAccuracy, 2)
        SetPlayerBit(PlayerBit(2))
        evt.StatusText("+2 Accuracy (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(229, "Legacy event 229", function()
    if IsQBitSet(QBit(760)) then return end -- Took area 2 hill fort
    local randomStep = PickRandomOption(229, 3, {3, 14, 25, 36})
    if randomStep == 3 then
        local randomStep = PickRandomOption(229, 4, {4, 6, 8, 10, 12})
        if randomStep == 4 then
            evt.CastSpell(6, 10, 3, 7368, 4920, 416, 4903, 7358, 1) -- Fireball
        elseif randomStep == 6 then
            evt.CastSpell(6, 10, 3, 7368, 4920, 416, 3820, 6694, 1) -- Fireball
        elseif randomStep == 8 then
            evt.CastSpell(6, 10, 3, 7368, 4920, 416, 5419, 7931, 1) -- Fireball
        elseif randomStep == 10 then
            evt.CastSpell(15, 10, 4, 7368, 4920, 416, 5507, 6889, 1) -- Sparks
        elseif randomStep == 12 then
            evt.CastSpell(43, 10, 3, 7336, 4952, 416, 5507, 6889, 512) -- Death Blossom
        end
    elseif randomStep == 14 then
        local randomStep = PickRandomOption(229, 15, {15, 17, 19, 21, 23})
        if randomStep == 15 then
            evt.CastSpell(6, 10, 3, 9000, 4920, 416, 11822, 8132, 0) -- Fireball
        elseif randomStep == 17 then
            evt.CastSpell(6, 10, 3, 9000, 4920, 416, 11218, 7086, 0) -- Fireball
        elseif randomStep == 19 then
            evt.CastSpell(6, 10, 3, 9000, 4920, 416, 12054, 6754, 0) -- Fireball
        elseif randomStep == 21 then
            evt.CastSpell(15, 10, 4, 9000, 4920, 416, 10772, 6539, 0) -- Sparks
        elseif randomStep == 23 then
            evt.CastSpell(43, 10, 3, 9032, 4952, 416, 10772, 6539, 512) -- Death Blossom
        end
    elseif randomStep == 25 then
        local randomStep = PickRandomOption(229, 26, {26, 28, 30, 32, 34})
        if randomStep == 26 then
            evt.CastSpell(6, 10, 3, 9000, 3280, 416, 13002, 728, 64) -- Fireball
        elseif randomStep == 28 then
            evt.CastSpell(6, 10, 3, 9000, 3280, 416, 11937, 538, 64) -- Fireball
        elseif randomStep == 30 then
            evt.CastSpell(6, 10, 3, 9000, 3280, 416, 11239, -167, 64) -- Fireball
        elseif randomStep == 32 then
            evt.CastSpell(15, 10, 3, 9000, 3280, 416, 10486, 1825, 47) -- Sparks
        elseif randomStep == 34 then
            evt.CastSpell(43, 10, 3, 9032, 3248, 416, 10486, 1825, 512) -- Death Blossom
        end
    elseif randomStep == 36 then
        local randomStep = PickRandomOption(229, 37, {37, 39, 41, 43, 45})
        if randomStep == 37 then
            evt.CastSpell(6, 10, 3, 7368, 3280, 416, 5493, 88, 1) -- Fireball
        elseif randomStep == 39 then
            evt.CastSpell(6, 10, 3, 7368, 3280, 416, 5452, 815, 1) -- Fireball
        elseif randomStep == 41 then
            evt.CastSpell(6, 10, 3, 7368, 3280, 416, 4448, 1052, 1) -- Fireball
        elseif randomStep == 43 then
            evt.CastSpell(15, 10, 3, 7368, 3280, 416, 5319, 1298, 1) -- Sparks
        elseif randomStep == 45 then
            evt.CastSpell(6, 10, 3, 7336, 3248, 416, 5319, 1298, 512) -- Fireball
        end
    end
end)

RegisterEvent(231, "Fire", function()
    local randomStep = PickRandomOption(231, 1, {1, 3, 5, 7, 9})
    if randomStep == 1 then
        evt.CastSpell(6, 10, 3, 7368, 4920, 416, 4903, 7358, 1) -- Fireball
    elseif randomStep == 3 then
        evt.CastSpell(6, 10, 3, 7368, 4920, 416, 3820, 6694, 1) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 10, 3, 7368, 4920, 416, 5419, 7931, 1) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(15, 10, 4, 7368, 4920, 416, 5507, 6889, 1) -- Sparks
    elseif randomStep == 9 then
        evt.CastSpell(43, 10, 3, 7336, 4952, 416, 5507, 6889, 512) -- Death Blossom
    end
end, "Fire")

RegisterEvent(232, "Fire", function()
    local randomStep = PickRandomOption(232, 1, {1, 3, 5, 7, 9})
    if randomStep == 1 then
        evt.CastSpell(6, 10, 3, 9000, 4920, 416, 11822, 8132, 0) -- Fireball
    elseif randomStep == 3 then
        evt.CastSpell(6, 10, 3, 9000, 4920, 416, 11218, 7086, 0) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 10, 3, 9000, 4920, 416, 12054, 6754, 0) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(15, 10, 4, 9000, 4920, 416, 10772, 6539, 0) -- Sparks
    elseif randomStep == 9 then
        evt.CastSpell(43, 10, 3, 9032, 4952, 416, 10772, 6539, 512) -- Death Blossom
    end
end, "Fire")

RegisterEvent(233, "Fire", function()
    local randomStep = PickRandomOption(233, 1, {1, 3, 5, 7, 9})
    if randomStep == 1 then
        evt.CastSpell(6, 10, 3, 9000, 3280, 416, 13002, 728, 64) -- Fireball
    elseif randomStep == 3 then
        evt.CastSpell(6, 10, 3, 9000, 3280, 416, 11937, 538, 64) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 10, 3, 9000, 3280, 416, 11239, -167, 64) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(15, 10, 3, 9000, 3280, 416, 10486, 1825, 47) -- Sparks
    elseif randomStep == 9 then
        evt.CastSpell(43, 10, 3, 9032, 3248, 416, 10486, 1825, 512) -- Death Blossom
    end
end, "Fire")

RegisterEvent(234, "Fire", function()
    local randomStep = PickRandomOption(234, 1, {1, 3, 5, 7, 9})
    if randomStep == 1 then
        evt.CastSpell(6, 10, 3, 7368, 3280, 416, 5493, 88, 1) -- Fireball
    elseif randomStep == 3 then
        evt.CastSpell(6, 10, 3, 7368, 3280, 416, 5452, 815, 1) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 10, 3, 7368, 3280, 416, 4448, 1052, 1) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(15, 10, 3, 7368, 3280, 416, 5319, 1298, 1) -- Sparks
    elseif randomStep == 9 then
        evt.CastSpell(6, 10, 3, 7336, 3248, 416, 5319, 1298, 512) -- Fireball
    end
end, "Fire")

RegisterEvent(235, "Hatch", function()
    evt.SetFacetBit(50, FacetBits.Invisible, 1)
end, "Hatch")

RegisterEvent(236, "Legacy event 236", function()
    if IsQBitSet(QBit(760)) then return end -- Took area 2 hill fort
    SetQBit(QBit(760)) -- Took area 2 hill fort
    evt.CastSpell(2, 10, 4, 6545, 10984, 4000, 6545, 5678, 111) -- Fire Bolt
    evt.CastSpell(2, 10, 4, 13458, 8781, 4000, 8805, 5257, 204) -- Fire Bolt
    evt.SummonMonsters(1, 1, 10, 5232, 1424, 0, 51, 0) -- encounter slot 1 "Goblin" tier A, count 10, pos=(5232, 1424, 0), actor group 51, no unique actor name
    evt.SummonMonsters(1, 1, 10, 10880, 784, 64, 51, 0) -- encounter slot 1 "Goblin" tier A, count 10, pos=(10880, 784, 64), actor group 51, no unique actor name
    evt.SummonMonsters(1, 1, 10, 5824, 6400, 12, 51, 0) -- encounter slot 1 "Goblin" tier A, count 10, pos=(5824, 6400, 12), actor group 51, no unique actor name
    evt.SummonMonsters(1, 1, 10, 10832, 6208, 0, 51, 0) -- encounter slot 1 "Goblin" tier A, count 10, pos=(10832, 6208, 0), actor group 51, no unique actor name
    evt.CastSpell(2, 10, 4, 8096, -3423, 4000, 7952, 3872, 320) -- Fire Bolt
    evt.CastSpell(2, 10, 4, 12240, 7312, 0, 8160, 5136, 314) -- Fire Bolt
end)

RegisterEvent(237, "Signal Fire Pit", function()
    if IsQBitSet(QBit(779)) then return end -- South Signal Fire Out02
    SetQBit(QBit(779)) -- South Signal Fire Out02
    evt.SetSprite(20, 1, "v77dec24")
    if IsQBitSet(QBit(780)) and IsQBitSet(QBit(781)) then -- North Signal Fire Out02
        SetQBit(QBit(774)) -- Time for Gobs to appear in area 2(raiding camp)
    else
    end
end, "Signal Fire Pit")

RegisterEvent(238, "Signal Fire Pit", function()
    if IsQBitSet(QBit(780)) then return end -- North Signal Fire Out02
    SetQBit(QBit(780)) -- North Signal Fire Out02
    evt.SetSprite(21, 1, "v77dec24")
    if IsQBitSet(QBit(779)) and IsQBitSet(QBit(781)) then -- South Signal Fire Out02
        SetQBit(QBit(774)) -- Time for Gobs to appear in area 2(raiding camp)
    else
    end
end, "Signal Fire Pit")

RegisterEvent(239, "Signal Fire Pit", function()
    if IsQBitSet(QBit(781)) then return end -- West Siganl Fire Out02
    SetQBit(QBit(781)) -- West Siganl Fire Out02
    evt.SetSprite(22, 1, "v77dec24")
    if IsQBitSet(QBit(780)) and IsQBitSet(QBit(779)) then -- North Signal Fire Out02
        SetQBit(QBit(774)) -- Time for Gobs to appear in area 2(raiding camp)
    else
    end
end, "Signal Fire Pit")

RegisterEvent(240, "Legacy event 240", function()
    if IsQBitSet(QBit(774)) then -- Time for Gobs to appear in area 2(raiding camp)
        evt.SetMonGroupBit(71, MonsterBits.Invisible, 0)
    end
end)

RegisterEvent(249, "Legacy event 249", function()
    if IsQBitSet(QBit(611)) then return end -- Chose the path of Light
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(250, "Legacy event 250", function()
    if evt.CheckSeason(2) then
        goto step_13
    end
    if evt.CheckSeason(3) then
        goto step_16
    end
    evt.SetSprite(5, 1, "7tree13")
    evt.SetSprite(6, 1, "7tree16")
    evt.SetSprite(7, 1, "7tree22")
    evt.SetSprite(10, 1, "0")
    goto step_29
    ::step_8::
    if evt.CheckSeason(1) then
        goto step_11
    end
    if evt.CheckSeason(0) then
        goto step_12
    end
    do return end
    ::step_11::
    goto step_28
    ::step_12::
    goto step_28
    ::step_13::
    evt.SetSprite(5, 1, "7tree14")
    evt.SetSprite(6, 1, "7tree17")
    goto step_18
    ::step_16::
    evt.SetSprite(5, 1, "7tree15")
    evt.SetSprite(6, 1, "7tree18")
    ::step_18::
    evt.SetSprite(7, 1, "7tree24")
    evt.SetSprite(10, 0, "0")
    evt.SetSprite(51, 1, "7tree30")
    evt.SetSprite(52, 1, "7tree30")
    evt.SetSprite(53, 1, "7tree30")
    evt.SetSprite(54, 1, "7tree30")
    evt.SetSprite(55, 1, "7tree30")
    evt.SetSprite(56, 1, "7tree30")
    evt.SetSprite(57, 1, "7tree30")
    evt.SetSprite(58, 1, "7tree30")
    ::step_28::
    do return end
    ::step_29::
    if IsAtLeast(MapVar(52), 1) then
        goto step_32
    end
    evt.SetSprite(51, 1, "0")
    goto step_33
    ::step_32::
    evt.SetSprite(51, 1, "0")
    ::step_33::
    if IsAtLeast(MapVar(53), 1) then
        goto step_36
    end
    evt.SetSprite(52, 1, "0")
    goto step_37
    ::step_36::
    evt.SetSprite(52, 1, "0")
    ::step_37::
    if IsAtLeast(MapVar(54), 1) then
        goto step_40
    end
    evt.SetSprite(53, 1, "0")
    goto step_41
    ::step_40::
    evt.SetSprite(53, 1, "0")
    ::step_41::
    if IsAtLeast(MapVar(55), 1) then
        goto step_44
    end
    evt.SetSprite(54, 1, "0")
    goto step_45
    ::step_44::
    evt.SetSprite(54, 1, "0")
    ::step_45::
    if IsAtLeast(MapVar(56), 1) then
        goto step_48
    end
    evt.SetSprite(55, 1, "0")
    goto step_49
    ::step_48::
    evt.SetSprite(55, 1, "0")
    ::step_49::
    if IsAtLeast(MapVar(57), 1) then
        goto step_52
    end
    evt.SetSprite(56, 1, "0")
    goto step_53
    ::step_52::
    evt.SetSprite(56, 1, "0")
    ::step_53::
    if IsAtLeast(MapVar(58), 1) then
        goto step_56
    end
    evt.SetSprite(57, 1, "0")
    goto step_57
    ::step_56::
    evt.SetSprite(57, 1, "0")
    ::step_57::
    if IsAtLeast(MapVar(59), 1) then
        goto step_60
    end
    evt.SetSprite(58, 1, "0")
    goto step_61
    ::step_60::
    evt.SetSprite(58, 1, "0")
    ::step_61::
    goto step_8
end)

RegisterEvent(251, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1101) -- Mist Manor
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(252, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1102) -- Hillsmen Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(253, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1103) -- Stillwater Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(254, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1104) -- Mark Manor
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(255, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1105) -- Bowes Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(256, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1106) -- Temper Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(257, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1107) -- Krewlen Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(258, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1108) -- Withersmythe's Home
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(260, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1121) -- Kern Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(261, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1122) -- Chadric's House
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(262, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1123) -- Weider Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(263, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1126) -- Hume Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(264, "House", function()
    if not IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        evt.EnterHouse(1127) -- Farswell Residence
        return
    end
    evt.StatusText("This Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "House")

RegisterEvent(265, "House", nil, "House")

RegisterEvent(266, "Hut", nil, "Hut")

RegisterEvent(267, "Hut", function()
    evt.EnterHouse(1124) -- Skinner's House
end, "Hut")

RegisterEvent(268, "Hut", function()
    evt.EnterHouse(1125) -- Torrent's
end, "Hut")

RegisterEvent(301, "Enter Castle Harmondale", function()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        if not IsQBitSet(QBit(644)) then -- Butler only shows up once (area 2)
            AddValue(History(5), 0)
            evt.SpeakNPC(397) -- Butler
            evt.MoveNPC(397, 240) -- Butler -> On the House
            evt.ForPlayer(Players.All)
            SetQBit(QBit(587)) -- Clean out Castle Harmondale and return to the Butler in the tavern, On the House, in Harmondale. - Given by butler at the door to the player castle.
            SetQBit(QBit(644)) -- Butler only shows up once (area 2)
            return
        end
        evt.MoveToMap(-5073, -2842, 1, 512, 0, 0, 134, 1, "\t7d29.blv")
        return
    end
    evt.MoveToMap(-5073, -2842, 1, 512, 0, 0, 126, 1, "\t7d29.blv")
end, "Enter Castle Harmondale")

RegisterEvent(302, "Enter the White Cliff Caves", function()
    evt.MoveToMap(1344, -256, -107, 1024, 0, 0, 135, 1, "7d21.blv")
end, "Enter the White Cliff Caves")

RegisterEvent(65535, "", function()
    if not IsQBitSet(QBit(610)) then return end -- Built Castle to Level 2 (rescued dwarf guy)
    if not IsQBitSet(QBit(645)) then -- Player castle timer only happens once
        SetValue(Counter(3), 0)
        SetQBit(QBit(645)) -- Player castle timer only happens once
    end
    evt.SetTexture(1, "chb1dl")
    evt.SetTexture(2, "chb1dr")
    evt.SetTexture(3, "chb1el")
    evt.SetTexture(4, "chb1er")
    evt.SetTexture(5, "chb1s")
    evt.SetTexture(6, "chb1")
    evt.SetTexture(11, "chb1el")
    evt.SetTexture(12, "chb1")
    evt.SetTexture(13, "chb1er")
    evt.SetTexture(14, "chb1s")
    evt.SetTexture(15, "chbw")
    evt.SetTexture(7, "chbw")
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(15, FacetBits.Invisible, 0)
    evt.SetSprite(1, 1, "7tree07")
    evt.SetSprite(2, 1, "7tree01")
    if IsAtLeast(History(7), 0) then return end
    AddValue(History(7), 0)
end)

RegisterEvent(65534, "", function()
    if IsQBitSet(QBit(614)) then -- Completed Proving Grounds without killing a single creature
        evt.SetFacetBit(20, FacetBits.Untouchable, 0)
        evt.SetFacetBit(20, FacetBits.Invisible, 0)
        evt.SetFacetBit(15, FacetBits.Invisible, 1)
        evt.SetFacetBit(11, FacetBits.Invisible, 1)
        evt.SetFacetBit(12, FacetBits.Invisible, 1)
        evt.SetFacetBit(13, FacetBits.Invisible, 1)
        evt.SetFacetBit(14, FacetBits.Invisible, 1)
        evt.SetFacetBit(15, FacetBits.Invisible, 1)
        evt.SetFacetBit(16, FacetBits.Invisible, 1)
        return
    elseif IsQBitSet(QBit(641)) then -- Completed Breeding Pit.
        evt.SetFacetBit(20, FacetBits.Untouchable, 0)
        evt.SetFacetBit(20, FacetBits.Invisible, 0)
        evt.SetFacetBit(15, FacetBits.Invisible, 1)
        evt.SetFacetBit(11, FacetBits.Invisible, 1)
        evt.SetFacetBit(12, FacetBits.Invisible, 1)
        evt.SetFacetBit(13, FacetBits.Invisible, 1)
        evt.SetFacetBit(14, FacetBits.Invisible, 1)
        evt.SetFacetBit(15, FacetBits.Invisible, 1)
        evt.SetFacetBit(16, FacetBits.Invisible, 1)
        return
    end
end)

