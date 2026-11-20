MM7 = MM7 or {}

MM7.RescuedDwarfNpcIds = {399, 400, 401, 402, 403, 404, 405}
MM7.LorenNpcId = 410
MM7.FakeLorenNpcId = 411
MM7.JudgeFairweatherNpcId = 416
MM7.JudgeSleenNpcId = 417
MM7.GolemNpcId = 395
MM7.ArcomageDeckItemId = 1453
MM7.ScavengerAdvertisementItemId = 774
MM7.WetsuitItemId = 1406
MM7.WetsuitPortraitId = 30

MM7.HouseServiceType = {
    Tavern = 4,
}

MM7.HouseMenu = {
    Root = 0,
}

function MM7.FilterTavernTopicsWithoutArcomage(context)
    if context.houseServiceType ~= MM7.HouseServiceType.Tavern or context.menuId ~= MM7.HouseMenu.Root then
        return
    end

    evt.SetHookHouseTopics({
        HouseAction.TavernRentRoom,
        HouseAction.TavernBuyFood,
        HouseAction.OpenLearnSkillsMenu,
        HouseAction.OpenTeacherLedgerMenu,
    })
end

function MM7.RemoveGolemFollowerIfConstructed()
    if IsQBitSet(QBit(585)) or IsQBitSet(QBit(586)) then
        RemoveFollowerNpc(MM7.GolemNpcId)
    end
end

function MM7.MakeCastleHarmondaleRestFreeIfRebuilt(context)
    if context == nil then
        return
    end

    if IsQBitSet(QBit(610)) then -- Built Castle to Level 2
        evt.SetHookRestFoodCost(0)
    end
end

function MM7.ActivateCastleHarmondaleMercenaries()
    evt.SetMonGroupBit(60, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(60, MonsterBits.Invisible, 0)
    SetValue(BankGold, 0)
    ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks.
    ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley.
end

function MM7.HideCastleHarmondaleMercenaries()
    evt.SetMonGroupBit(60, MonsterBits.Hostile, 0)
    evt.SetMonGroupBit(60, MonsterBits.Invisible, 1)
end

function MM7.HideCastleHarmondaleGoblinsIfRebuilt()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2
        return
    end

    evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
    evt.SetMonGroupBit(56, MonsterBits.Invisible, 1)
end

function MM7.UpdateCastleHarmondaleMercenariesOnLoad()
    if IsQBitSet(QBit(526))
        and IsQBitSet(QBit(695))
        and not IsQBitSet(QBit(696))
        and not IsQBitSet(QBit(702)) then
        MM7.ActivateCastleHarmondaleMercenaries()
        return
    end

    MM7.HideCastleHarmondaleMercenaries()
end

function MM7.MarkCastleHarmondaleMercenariesKilledIfClear()
    if not IsQBitSet(QBit(695)) then
        return
    end

    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 60, 0, false) then
        return
    end

    SetQBit(QBit(696)) -- Killed all castle monsters

    if IsQBitSet(QBit(697)) then -- Killed all outdoor monsters
        SetQBit(QBit(702)) -- Finished with Malwick & Assc.
        ClearQBit(QBit(695)) -- Failed either goto or do guild quest
    end
end

function MM7.IsEnemyDetectorActive()
    local yellow, red = evt.GetEnemyDetectorState()
    return yellow or red
end

function MM7.EnterCastleLambentThroneRoom()
    if IsQBitSet(QBit(612)) -- Chose the path of Dark
        or not IsQBitSet(QBit(611)) -- Chose the path of Light
        or MM7.IsEnemyDetectorActive() then
        evt.StatusText("The Door is Locked")
        return
    end

    evt.EnterHouse(220) -- Throne Room
end

function MM7.EnterCastleGloamingThroneRoom()
    if IsQBitSet(QBit(611)) -- Chose the path of Light
        or not IsQBitSet(QBit(612)) -- Chose the path of Dark
        or MM7.IsEnemyDetectorActive() then
        evt.StatusText("The Door is Locked")
        return
    end

    if IsQBitSet(QBit(710)) then -- Archibald in Clanker's Lab now
        evt.EnterHouse(221) -- Throne Room
        return
    end

    evt.EnterHouse(219) -- Throne Room
end

function MM7.DistanceToPartySquared(x, y)
    local partyX, partyY = evt.GetPartyPosition()
    local dx = x - partyX
    local dy = y - partyY
    return dx * dx + dy * dy
end

function MM7.UpdateDeyjaOutdoorState()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, IsQBitSet(QBit(611)) and 1 or 0)
end

function MM7.SummonDeyjaAmbushIfNeeded(context)
    if context == nil or context.npcId ~= 461 or IsQBitSet(QBit(761)) then
        return
    end

    local partyX, partyY, partyZ = evt.GetPartyPosition()
    evt.SummonMonsters(3, 3, 5, partyX, partyY, partyZ + 400, 59, 0)
    evt.SetMonGroupBit(59, MonsterBits.Hostile, 1)
end

function MM7.SummonMalwickAmbush(force)
    if not force and IsQBitSet(QBit(761)) then
        return
    end

    local partyX, partyY, partyZ = evt.GetPartyPosition()
    evt.SummonMonsters(3, 3, 5, partyX, partyY, partyZ + 400, 59, 0)
    evt.SetMonGroupBit(59, MonsterBits.Hostile, 1)
end

function MM7.MarkAntagarichEndgameComplete()
    SetQBit(QBit(783))
end

-- MMerge's dragon hatchling (Global_mm7_mmmerge.lua, MAW's Global_maw.lua) keeps its state under MMerge's CrossContinents
-- names, which saves carry.
function MM7.CrossVar(name)
    return "MMerge.CrossContinents." .. name
end

function MM7.GetCrossVar(name, defaultValue)
    return evt.GetGlobalVar(MM7.CrossVar(name), defaultValue or 0)
end

function MM7.SetCrossVar(name, value)
    evt.SetGlobalVar(MM7.CrossVar(name), value or 0)
end

function MM7.AnyQBit(qbits)
    for _, qbitId in ipairs(qbits or {}) do
        if IsQBitSet(QBit(qbitId)) then
            return true
        end
    end

    return false
end

function MM7.SetQBits(qbits)
    for _, qbitId in ipairs(qbits or {}) do
        SetQBit(QBit(qbitId))
    end
end

function MM7.ClearQBits(qbits)
    for _, qbitId in ipairs(qbits or {}) do
        ClearQBit(QBit(qbitId))
    end
end

function MM7.HasPartyItem(itemId)
    return HasItemAnywhere(itemId)
end

function MM7.TakePartyItem(itemId)
    evt.ForPlayer(Players.All)
    RemoveItem(itemId)
    evt.ForPlayer(Players.Current)
end

function MM7.GivePartyItem(itemId)
    AddValue(InventoryItem(itemId), itemId)
end

function MM7.AddPartyGold(gold)
    if gold ~= nil and gold ~= 0 then
        AddValue(Gold, gold)
    end
end

function MM7.AddPartyReputation(value)
    if value ~= nil and value ~= 0 then
        AddValue(ReputationInCurrentLocation, value)
    end
end

function MM7.PromotionMessage(text)
    if text ~= nil and text ~= "" then
        evt.SimpleMessage(text)
    end
end

function MM7.CompletePromotion(data)
    local firstTime = not MM7.AnyQBit(data.qbits)

    if firstTime and data.condition ~= nil and not data.condition() then
        MM7.PromotionMessage(data.refuseMessage)
        return 0
    end

    MM7.PromotionMessage(firstTime and data.firstMessage or (data.repeatMessage or data.firstMessage))

    local result = PromotePlayers({
        from = data.from,
        to = data.to,
        promotedRewards = {Experience = data.promotedExperience or 0},
        nonPromotedRewards = firstTime and {Experience = data.nonPromotedExperience or 0} or nil,
    })

    if firstTime then
        MM7.SetQBits(data.qbits)
        MM7.AddPartyGold(data.gold)
        MM7.AddPartyReputation(data.reputation)
    end

    return firstTime and 1 or 2, result
end

function MM7.CheckPromotionSide(thisSideBit, oppositeSideBit, thisMessage, oppositeMessage, neitherMessage)
    if IsQBitSet(QBit(thisSideBit)) then
        MM7.PromotionMessage(thisMessage)
        return true
    end

    if IsQBitSet(QBit(oppositeSideBit)) then
        MM7.PromotionMessage(oppositeMessage)
        return false
    end

    MM7.PromotionMessage(neitherMessage)
    return false
end

-- out09's flower07 at (-2008, -13448), link number 20; its click event 170 opens the obelisk chest. The map file
-- flags it invisible.
local EvenmornObeliskTreasureCog = 20

function MM7.UpdateEvenmornObeliskTreasure()
    local allObelisksFound = true

    for qbitId = 676, 689 do
        allObelisksFound = allObelisksFound and IsQBitSet(QBit(qbitId))
    end

    -- Shown only during the midnight hour once every obelisk is read (MMerge out09.lua). IsAtLeast tests the hour
    -- for equality.
    local visible = allObelisksFound and IsAtLeast(Hour, 0)
    evt.SetSprite(EvenmornObeliskTreasureCog, visible and 1 or 0)
end

function MM7.SummonTulareanArtifactBattle()
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
    evt.SetFacetBit(1, FacetBits.Invisible, 0)
    evt.SummonMonsters(2, 2, 3, -15752, 21272, 3273, 51, 0)
    evt.SummonMonsters(2, 2, 5, -14000, 18576, 4250, 51, 0)
    evt.SummonMonsters(2, 2, 10, -16016, 19280, 3284, 51, 0)
    evt.SummonMonsters(3, 2, 3, -15752, 21272, 3273, 50, 0)
    evt.SummonMonsters(3, 2, 9, -14000, 18576, 4250, 50, 0)
    evt.SummonMonsters(3, 2, 10, -16016, 19280, 3284, 50, 0)
end

function MM7.UpdateTulareanArtifactBattle()
    if IsQBitSet(QBit(646)) then -- Judge Grey died
        return
    end

    if not IsQBitSet(QBit(649)) then -- Artifact Messenger only happens once
        if not IsQBitSet(QBit(600)) then -- Talked to Catherine
            return
        end

        if IsQBitSet(QBit(589)) or IsQBitSet(QBit(590)) then
            return
        end

        evt.SpeakNPC(412) -- Messenger
        AddValue(InventoryItem(1502), 1502) -- Message from Erathia
        SetQBit(QBit(649)) -- Artifact Messenger only happens once
        SetQBit(QBit(591)) -- Retrieve Gryphonheart's Trumpet
        SetValue(MapVar(11), 0)
    end

    if not IsQBitSet(QBit(591)) then
        return
    end

    -- Keep the artifact chest derived from the active quest state. This also repairs saves made before outdoor
    -- facet attributes were included in travel/save snapshots.
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
    evt.SetFacetBit(1, FacetBits.Invisible, 0)

    if IsAtLeast(MapVar(11), 1) then
        return
    end

    SetValue(MapVar(11), 1)
    MM7.SummonTulareanArtifactBattle()
end

function MM7.EnterClankersLaboratory()
    if IsQBitSet(QBit(710)) then -- Archibald in Clanker's Lab now
        evt.MoveNPC(427, 395)
        evt.EnterHouse(395) -- Clanker's Laboratory
        return
    end

    evt.MoveToMap(0, -709, 1, 512, 0, 0, 395, 9, "7d12.blv")
end

function MM7.RemoveJudgeFollowers()
    RemoveFollowerNpc(MM7.JudgeFairweatherNpcId)
    RemoveFollowerNpc(MM7.JudgeSleenNpcId)
end

function MM7.EnterCastleHarmondaleOutdoor()
    if IsQBitSet(QBit(519)) then -- Visited Emerald Island
        if IsQBitSet(QBit(610)) or IsQBitSet(QBit(644)) then
            if IsQBitSet(QBit(610)) then
                evt.MoveToMap(-5073, -2842, 1, 512, 0, 0, 382, 9, "7d29.blv")
            else
                evt.MoveToMap(-5073, -2842, 1, 512, 0, 0, 390, 9, "7d29.blv")
            end
            return
        end

        SetQBit(QBit(644)) -- Butler only shows up once.
        SetQBit(QBit(587)) -- Clean out Castle Harmondale.
        AddValue(History(3), 0)
        evt.MoveNPC(397, 240)
        evt.SpeakNPC(397)
        return
    end

    evt.FaceAnimation(FaceAnimation.DoorLocked)
end

function MM7.UpdateHarmondaleInvasion()
    if IsQBitSet(QBit(611)) or IsQBitSet(QBit(612)) then
        SetQBit(QBit(608))
    end

    if not (IsQBitSet(QBit(693)) or IsQBitSet(QBit(694))) then
        return
    end

    if IsQBitSet(QBit(702)) or IsQBitSet(QBit(695)) then
        return
    end

    local invasionTime = evt.GetMapVar("InvasionTime", 0)
    if invasionTime == 0 then
        invasionTime = CurrentGameMinutes() + 14 * 24 * 60
        evt.SetMapVar("InvasionTime", invasionTime)
    end

    if invasionTime >= CurrentGameMinutes() then
        return
    end

    SetQBit(QBit(695))
    evt.SetMonGroupBit(60, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(60, MonsterBits.Invisible, 0)
    SetValue(BankGold, 0)
    evt.SpeakNPC(437)
end

function MM7.GiveScavengerAdvertisementIfNear(x, y, requireNoAdvertisementItem)
    if evt.GetMapVar("GotAdvertisement", 0) ~= 0 or IsQBitSet(QBit(519)) then
        return
    end

    if requireNoAdvertisementItem and HasItemAnywhere(MM7.ScavengerAdvertisementItemId) then
        return
    end

    local enemyYellow, enemyRed = evt.GetEnemyDetectorState()
    if isFlying() or enemyYellow or enemyRed then
        return
    end

    if MM7.DistanceToPartySquared(x, y) >= 4000 * 4000 then
        return
    end

    evt.SetMapVar("GotAdvertisement", 1)
    AddValue(InventoryItem(MM7.ScavengerAdvertisementItemId), MM7.ScavengerAdvertisementItemId)
    evt.SetNPCGreeting(649, 332)
    evt.SpeakNPC(649)
end

function MM7.UpdateJudgeGreyDeath()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2.
        return
    end

    local rebuiltDate = evt.GetGlobalVar("HarmondaleRebuiltDate", 0)
    if rebuiltDate == 0 then
        rebuiltDate = CurrentGameMinutes()
        evt.SetGlobalVar("HarmondaleRebuiltDate", rebuiltDate)
    end

    if IsQBitSet(QBit(646)) then -- Arbiter Messenger only happens once.
        return
    end

    local sixMonths = 6 * 28 * 24 * 60
    if not (IsQBitSet(QBit(659))
        or IsQBitSet(QBit(596))
        or IsQBitSet(QBit(597))
        or CurrentGameMinutes() > rebuiltDate + sixMonths) then
        return
    end

    evt.SpeakNPC(430)
    SetQBit(QBit(665))
    AddValue(History(6), 0)
    evt.MoveNPC(406, 0)
    evt.MoveNPC(407, 0)
    evt.MoveNPC(414, 1169)
    evt.MoveNPC(415, 1169)
    evt.MoveNPC(416, 244)
    evt.MoveNPC(417, 243)
    SetQBit(QBit(646))
end

-- A member is suited for the Shoals wearing a Wetsuit, or carrying one when their paperdoll cannot wear armour:
-- otherwise a dragon in the party would lock the Shoals away.
function MM7.PartyMemberSuitedForShoals(memberIndex)
    if evt.PartyMemberHasEquippedItem(memberIndex, MM7.WetsuitItemId) then
        return true
    end

    return not evt.PartyMemberCanWearArmor(memberIndex)
        and evt.PartyMemberItemCount(memberIndex, MM7.WetsuitItemId) > 0
end

function MM7.AllPartyMembersHaveWetsuit()
    local count = evt.GetPartyMemberCount()

    for memberIndex = 0, count - 1 do
        if not MM7.PartyMemberSuitedForShoals(memberIndex) then
            return false
        end
    end

    return true
end

function MM7.BlockShoalsTravelWithoutWetsuits(context)
    if context == nil or context.boundaryEdge ~= 3 then -- West edge.
        return
    end

    if string.lower(context.destinationMapName or "") ~= "7out15.odm" then
        return
    end

    local hasLincolnQuest = IsQBitSet(QBit(642)) or IsQBitSet(QBit(643)) or IsQBitSet(QBit(783))
    if not hasLincolnQuest then
        evt.SetHookBlocked(true, nil)
        return
    end

    if MM7.AllPartyMembersHaveWetsuit() then
        return
    end

    evt.SetHookBlocked(true, "You must all be wearing your wetsuits!")
end

function MM7.BlockShoalsUnderwaterAction(context)
    if context == nil then
        return
    end

    if context.actionId == 133 or context.actionId == 105
        or (context.heldItemId == MM7.WetsuitItemId and context.actionId ~= 120 and context.actionId ~= 12) then
        evt.PlaySound(27)
        evt.SetHookBlocked(true, "You can't do that here.")
    end
end

function MM7.ApplyShoalsPartyPortraits()
    -- Older OpenYAMM saves may already be on Shoals with the temporary wetsuit portrait forced.
    MM7.RestoreShoalsPartyPortraits()
end

function MM7.RestoreShoalsPartyPortraits()
    local count = evt.GetPartyMemberCount()

    for memberIndex = 0, count - 1 do
        local varName = "ShoalsOriginalPortrait" .. tostring(memberIndex)
        local storedPortrait = evt.GetMapVar(varName, 0)
        if storedPortrait > 0 then
            evt.SetPartyMemberPortraitId(memberIndex, storedPortrait - 1)
        end
        evt.SetMapVar(varName, 0)
    end
end

function MM7.KillUnsuitedShoalsPartyMembers()
    local _, _, partyZ = evt.GetPartyPosition()
    if partyZ > 3900 and evt.GetCurrentScreen() == 0 then
        return
    end

    local count = evt.GetPartyMemberCount()

    for memberIndex = 0, count - 1 do
        if not MM7.PartyMemberSuitedForShoals(memberIndex) then
            evt.ForPlayer(memberIndex)
            if not IsAtLeast(Dead, 0) then
                SetValue(CurrentHealth, 0)
                SetValue(Dead, 0)
            end
        end
    end

    evt.ForPlayer(Players.Current)
end

function MM7.LeaveShoalsIfAboveWater()
    local _, _, partyZ = evt.GetPartyPosition()
    if partyZ <= 3900 or evt.GetCurrentScreen() ~= 0 then
        evt.SetMapVar("ShoalsWasAboveWater", 1)
        return
    end

    if evt.GetMapVar("ShoalsWasAboveWater", 1) == 0 then
        return
    end

    evt.SetMapVar("ShoalsWasAboveWater", 0)
    evt.MoveToMap(-18584, -16562, 1, 290, 0, 0, 0, 8, "out14.odm")
end

function MM7.RemoveRescuedDwarfFollowers()
    if not IsQBitSet(QBit(610)) then -- Built Castle to Level 2
        return
    end

    for _, npcId in ipairs(MM7.RescuedDwarfNpcIds) do
        RemoveFollowerNpc(npcId)
    end
end

function MM7.RemoveLorenFollowersIfResolved()
    if not IsQBitSet(QBit(1695)) then
        RemoveFollowerNpc(MM7.LorenNpcId)
    end

    if not IsQBitSet(QBit(1696)) then
        RemoveFollowerNpc(MM7.FakeLorenNpcId)
    end
end

function MM7.AddLorenFollowerIfActive()
    if IsQBitSet(QBit(1695)) then
        AddFollowerNpc(MM7.LorenNpcId)
    end
end

MM7.SeerRecoverableItems = {
    {Item = 1426, QBit = 724}, -- Vase
    {Item = 1342, QBit = 725}, -- Lady Carmine's Dagger
    {Item = 1504, QBit = 726}, -- Scroll of Waves
    {Item = 1503, QBit = 727}, -- Cipher
    {Item = 1451, QBit = 728}, -- Worn Belt
    {Item = 1402, QBit = 729}, -- Heart of the Wood
    {Item = 1485, QBit = 730}, -- Map to Evenmorn
    {Item = 1443, QBit = 731}, -- Golem Head
    {Item = 1442, QBit = 732}, -- Abbey Normal Golem Head
    {Item = 1446, QBit = 733}, -- Golem Right Arm
    {Item = 1447, QBit = 734}, -- Golem Left Arm
    {Item = 1445, QBit = 735}, -- Golem Right Leg
    {Item = 1444, QBit = 736}, -- Golem Left Leg
    {Item = 1441, QBit = 737}, -- Golem Torso
    {Item = 1289, QBit = 738}, -- Book of Divine Intervention
    {Item = 1449, QBit = 739}, -- Dragon Egg
    {Item = 1428, QBit = 740}, -- Dwarf Bones
    {Item = 1417, QBit = 741}, -- Lich Jar (Empty)
    {Item = 1431, QBit = 742}, -- Elixir
    {Item = 1404, QBit = 743}, -- Lich Jar Case
    {Item = 1478, QBit = 744}, -- Altar Piece (Good)
    {Item = 1479, QBit = 745}, -- Altar Piece (Evil)
    {Item = 1477, QBit = 746}, -- Control Cube
    {Item = 1406, QBit = 747}, -- Wetsuit
    {Item = 1407, QBit = 748}, -- Oscillation Overthruster
    {Item = 1403, QBit = 749}, -- Lich Jar
}

function MM7.RecoverLostItem()
    support.tryRecoverLostItem(MM7.SeerRecoverableItems)
end

RegisterGlobalEvent(889, "I lost it", function()
    MM7.RecoverLostItem()
end)
