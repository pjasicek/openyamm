MM6 = MM6 or {}

MM6.NicolaiNpcId = 798
MM6.NicolaiQuestQBit = 1114
MM6.NicolaiReturnQBit = 1119
MM6.NicolaiFollowerQBit = 1700
MM6.NicolaiThroneRoomHouseId = 222
MM6.NicolaiCircusHouseId = 1595
MM6.NicolaiKidnapTimerEventId = 65000
MM6.NicolaiStateOnLoadEventId = 65001
MM6.NicolaiKidnapDeadlineVariable = 0x7001
MM6.NicolaiKidnapTimerIntervalSeconds = 5 * 60
MM6.NicolaiKidnapInitialDelaySeconds = 60 * 60
MM6.NicolaiKidnapMessage =
    "The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!"
MM6.NicolaiDisappearedMessage = "It seems that Prince Nicolai disappeared while you were resting."
MM6.NicolaiReturnMessage =
    "\"Well, thanks for sneaking me out of the Castle.  Sorry about the circus thing-I hope I wasn't too much trouble to find.  I'll go in myself so no one will see that it was you who kidnapped me.  Thanks again, and goodbye.  I'll remember this, and I owe you a favor! \""

MM6.LorettaPriceMessage =
    "Well, If Loretta's got a new scheme, count me in!\nBut you better get all the other companies to sign up!"

MM6.SeerRecoverableItems = {
    {Item = 2125, QBits = {1105, 1106, 1205}}, -- The Letter
    {
        Item = 2119,
        QBits = {1110, 1206},
        ProofQBits = {1206},
    },
    {Item = 2053, QBit = 1207}, -- Hourglass of Time
    {Item = 2126, QBit = 1208}, -- Devil Plans
    {Item = 2075, QBit = 1209}, -- Dragon Claw
    {Item = 2077, QBit = 1210}, -- Crystal of Terrax
    {Item = 2128, QBit = 1211}, -- Discharge Papers
    {Item = 2054, QBit = 1212}, -- Sacred Chalice
    {Item = 2106, QBit = 1213}, -- Dragon Tower Keys
    {Item = 2122, QBit = 1214}, -- Smoking Gun
    {Item = 2170, QBit = 1215}, -- Memory Crystal Alpha
    {Item = 2171, QBit = 1216}, -- Memory Crystal Beta
    {Item = 2172, QBit = 1217}, -- Memory Crystal Delta
    {Item = 2173, QBit = 1218}, -- Memory Crystal Epsilon
    {Item = 2076, QBit = 1219}, -- Control Cube
    {Item = 2066, QBit = 1220}, -- Third Eye
    {Item = 2081, QBit = 1221}, -- Tanir's Bell
    {Item = 2200, QBit = 1222}, -- Dark Containment
    {Item = 2107, QBit = 1223}, -- Key to Gharik's Laboratory
    {Item = 2158, QBit = 1253}, -- First Mate's Code
    {Item = 2162, QBit = 1254}, -- Doctor's Code
    {Item = 2157, QBit = 1255}, -- Captain's Code
    {Item = 2159, QBit = 1256}, -- Navigator's Code
    {Item = 2161, QBit = 1257}, -- Engineer's Code
    {Item = 2160, QBit = 1258}, -- Communication Officer's Code
}

function MM6.ApplyLocalMonsterRelations(relations)
    ApplyLocalMonsterRelations(relations)
end

function MM6.RecoverLostItem()
    support.tryRecoverLostItem(MM6.SeerRecoverableItems)
end

function MM6.StartNicolaiQuest()
    AddFollowerNpc(MM6.NicolaiNpcId)
    evt.MoveNPC(MM6.NicolaiNpcId, 0)
    SetQBit(QBit(MM6.NicolaiQuestQBit))
    SetQBit(QBit(MM6.NicolaiFollowerQBit))
    SetPartyVariable(
        MM6.NicolaiKidnapDeadlineVariable,
        CurrentGameMinutes() + math.floor(MM6.NicolaiKidnapInitialDelaySeconds / 60))
    evt.SetNPCTopic(MM6.NicolaiNpcId, 0, 1332)
end

function MM6.KidnapNicolai(showMessage, force)
    if not IsQBitSet(QBit(MM6.NicolaiQuestQBit))
        or (not force and not HasFollowerNpc(MM6.NicolaiNpcId)) then
        return
    end

    RemoveFollowerNpc(MM6.NicolaiNpcId)
    ClearQBit(QBit(MM6.NicolaiQuestQBit))
    ClearQBit(QBit(MM6.NicolaiFollowerQBit))
    SetPartyVariable(MM6.NicolaiKidnapDeadlineVariable, 0)
    evt.MoveNPC(MM6.NicolaiNpcId, MM6.NicolaiCircusHouseId)
    SetQBit(QBit(MM6.NicolaiReturnQBit))
    evt.SetNPCTopic(MM6.NicolaiNpcId, 0, 1334)

    if showMessage then
        evt.SimpleMessage(MM6.NicolaiDisappearedMessage)
    else
        evt.StatusText(MM6.NicolaiDisappearedMessage)
    end
end

function MM6.RecoverNicolaiAtCircus()
    AddFollowerNpc(MM6.NicolaiNpcId)
    SetQBit(QBit(MM6.NicolaiFollowerQBit))
    SetPartyVariable(MM6.NicolaiKidnapDeadlineVariable, 0)
    evt.SetNPCTopic(MM6.NicolaiNpcId, 0, 1335)
end

function MM6.NormalizeNicolaiState()
    local hasFollower = HasFollowerNpc(MM6.NicolaiNpcId)
    local legacyFollowerFlag = IsQBitSet(QBit(MM6.NicolaiFollowerQBit))

    if IsQBitSet(QBit(MM6.NicolaiQuestQBit)) then
        local deadline = GetPartyVariable(MM6.NicolaiKidnapDeadlineVariable)
        if deadline > 0 and CurrentGameMinutes() >= deadline then
            MM6.KidnapNicolai(false, true)
            return
        end

        if hasFollower then
            SetQBit(QBit(MM6.NicolaiFollowerQBit))
            if deadline == 0 then
                SetPartyVariable(
                    MM6.NicolaiKidnapDeadlineVariable,
                    CurrentGameMinutes() + math.floor(MM6.NicolaiKidnapInitialDelaySeconds / 60))
            end
        elseif legacyFollowerFlag then
            AddFollowerNpc(MM6.NicolaiNpcId)
            if deadline == 0 then
                SetPartyVariable(
                    MM6.NicolaiKidnapDeadlineVariable,
                    CurrentGameMinutes() + math.floor(MM6.NicolaiKidnapInitialDelaySeconds / 60))
            end
        else
            MM6.KidnapNicolai(false, true)
        end
        return
    end

    if IsQBitSet(QBit(MM6.NicolaiReturnQBit)) then
        if hasFollower then
            SetQBit(QBit(MM6.NicolaiFollowerQBit))
        elseif legacyFollowerFlag then
            AddFollowerNpc(MM6.NicolaiNpcId)
        end
    end
end

function MM6.EnterIronfistThroneRoom()
    evt.EnterHouse(MM6.NicolaiThroneRoomHouseId)
end

function MM6.ShowNicolaiKidnapDenied()
    evt.StatusText(MM6.NicolaiKidnapMessage)
    evt.SimpleMessage(MM6.NicolaiKidnapMessage)
end

function MM6.ReturnNicolai()
    MM6.NormalizeNicolaiState()

    if IsQBitSet(QBit(MM6.NicolaiQuestQBit)) then
        if HasFollowerNpc(MM6.NicolaiNpcId) then
            MM6.EnterIronfistThroneRoom()
            return
        end

        MM6.ShowNicolaiKidnapDenied()
        return
    end

    if IsQBitSet(QBit(MM6.NicolaiReturnQBit)) then
        if HasFollowerNpc(MM6.NicolaiNpcId) then
            evt.MoveNPC(MM6.NicolaiNpcId, MM6.NicolaiThroneRoomHouseId)
            ClearQBit(QBit(MM6.NicolaiFollowerQBit))
            ClearQBit(QBit(MM6.NicolaiReturnQBit))
            SetPartyVariable(MM6.NicolaiKidnapDeadlineVariable, 0)
            RemoveFollowerNpc(MM6.NicolaiNpcId)
            evt.SimpleMessage(MM6.NicolaiReturnMessage)
            evt.ForPlayer(Players.All)
            AddValue(Experience, 7500)
            evt.SetNPCTopic(MM6.NicolaiNpcId, 0, 1337)
            MM6.EnterIronfistThroneRoom()
            return
        end

        MM6.ShowNicolaiKidnapDenied()
        return
    end

    MM6.EnterIronfistThroneRoom()
end

function MM6.RegisterNicolaiKidnapTimer()
    RegisterMapTimerEvent(
        MM6.NicolaiKidnapTimerEventId,
        MM6.NicolaiKidnapTimerIntervalSeconds,
        function()
            MM6.KidnapNicolai(false)
        end,
        "Nicolai Kidnap",
        nil,
        MM6.NicolaiKidnapInitialDelaySeconds)
end

function MM6.RegisterNicolaiStateOnLoad()
    RegisterMapOnLoadEvent(MM6.NicolaiStateOnLoadEventId, "Nicolai State", function()
        MM6.NormalizeNicolaiState()
    end)
end

function MM6.ApplyDragonTowerState(qbitId, modelIndex, faceIndex)
    if IsQBitSet(QBit(qbitId)) then
        evt.SetOutdoorModelFacetTexture(modelIndex, faceIndex, "t1swbu")
    end
end

function MM6.TryDisableDragonTower(qbitId, modelIndex, faceIndex)
    MM6.ApplyDragonTowerState(qbitId, modelIndex, faceIndex)
    if IsQBitSet(QBit(qbitId)) then
        return
    end

    if HasItem(2106) or HasItem(486) then
        SetQBit(QBit(qbitId))
        evt.SetOutdoorModelFacetTexture(modelIndex, faceIndex, "t1swbu")
    end
end

function MM6.RegisterDragonTowerTimer(eventId, x, y, z, qbitId)
    RegisterMapTimerEvent(eventId, 5 * 60, function()
        if IsQBitSet(QBit(qbitId)) then
            return
        end

        if support.isFlying() and not support.isInvisible() then
            evt.CastSpell(6, 5, 3, x, y, z, 0, 0, 0)
        end
    end, "Dragon Tower")
end

function MM6.CheckLorettaPrices(houseId, qbitId)
    if IsQBitSet(QBit(1140)) and not IsQBitSet(QBit(qbitId)) and evt.IsHouseOpen(houseId) then
        evt.SimpleMessage(MM6.LorettaPriceMessage)
        SetQBit(QBit(qbitId))

        for bit = 1515, 1523 do
            if not IsQBitSet(QBit(bit)) then
                return
            end
        end

        AddValue(Experience, 1)
        SetQBit(QBit(1141))
        return
    end

    evt.EnterHouse(houseId)
end

function MM6.AddQuestFollower(npcId)
    AddFollowerNpc(npcId)
end

function MM6.RemoveQuestFollower(npcId)
    RemoveFollowerNpc(npcId)
end

function MM6.RemoveQuestFollowerUnless(qbitId, npcId)
    if not IsQBitSet(QBit(qbitId)) then
        RemoveFollowerNpc(npcId)
    end
end

function MM6.SellCollectorItem(itemId, autonoteId, gold, reputation, soldMessage, missingMessage)
    if autonoteId ~= nil and autonoteId ~= 0 then
        SetAutonote(autonoteId)
    end
    evt.ForPlayer(Players.All)

    if HasItem(itemId) then
        RemoveItem(itemId)
        AddValue(Gold, gold)

        if reputation ~= nil and reputation ~= 0 then
            AddValue(ReputationInCurrentLocation, reputation)
        end

        evt.SimpleMessage(soldMessage)
        return
    end

    evt.SimpleMessage(missingMessage)
end

function MM6.EnsureChestItem(chestId, itemId, gridX, gridY)
    evt.EnsureChestItem(chestId, itemId, gridX or 0, gridY or 0)
end

function MM6.ApplyFrozenHighlandsWinterState()
    if HasAward(Award(62)) or IsQBitSet(QBit(1199)) then
        evt.SetSnow(0, false)
        return
    end

    evt.SetOutdoorSky("sky04")
    evt.SetOutdoorFog(100, 1000)
    evt.SetRain(0, false)
    evt.SetSnow(0, true)
end

function MM6.RevealSilvertongue()
    evt.ForPlayer(Players.All)
    if HasItem(2122) and not IsQBitSet(QBit(1192)) then
        evt.ShowMovie("citytrtr", false)
        evt.MoveNPC(1089, 0)
        RemoveItem(2122)
        AddValue(655595, 10)
        SetQBit(QBit(1192))
        ClearQBit(QBit(1214))
        ClearQBit(QBit(1225))
        ClearQBit(QBit(1224))
        SetAward(Award(63))
        evt.SetNPCTopic(789, 0, 1416)

        if HasAward(Award(57))
            and HasAward(Award(58))
            and HasAward(Award(59))
            and HasAward(Award(60))
            and HasAward(Award(61))
            and HasAward(Award(62)) then
            SetQBit(QBit(1191))
        end
    end

    if IsQBitSet(QBit(1192)) then
        ClearQBit(QBit(1225))
    end

    evt.EnterHouse(209)
end

function MM6.RepairStoneTemple()
    if IsQBitSet(QBit(1132)) then
        evt.EnterHouse(326)
        return
    end

    if IsQBitSet(QBit(1131)) then
        if HasItem(2054) then
            RemoveItem(2054)
            ClearQBit(QBit(1212))
            SetQBit(QBit(1132))
            evt.EnterHouse(326)
            evt.SimpleMessage(
                "You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.")
        else
            evt.EnterHouse(1442)
        end
        return
    end

    if IsQBitSet(QBit(1130)) then
        evt.EnterHouse(1442)
        return
    end

    if HasFollowerProfession(63) and HasFollowerProfession(64) then
        evt.SimpleMessage("The stone cutter and carpenter begin rebuilding the temple.")
        SetQBit(QBit(1130))
        RemoveFollowerProfession(63)
        RemoveFollowerProfession(64)
        return
    end

    evt.EnterHouse(1442)
end

function MM6.OpenDimensionDoor()
    if CrossContinents ~= nil
        and CrossContinents.TryDimensionDoorContact ~= nil
        and CrossContinents.TryDimensionDoorContact() then
        return
    end

    evt.OpenDimensionDoor()
end

function MM6.RunNewSorpigalVolcanoSequence()
    evt.PlaySound(18090)

    for i = 1, 6 do
        evt.CastSpell(
            6,
            4,
            10,
            -14074,
            16106,
            1250,
            math.random(-14124, -14024),
            math.random(16056, 16156),
            1500)
    end

    evt.CastSpell(
        43, 4, 10, -14320, 16272, 1400, math.random(-14420, -14220), math.random(16172, 16372), 2400)
    evt.CastSpell(
        43, 4, 10, -14096, 15648, 1400, math.random(-14200, -14000), math.random(15548, 15748), 2400)
    evt.CastSpell(
        43, 4, 10, -13856, 16448, 1400, math.random(-13956, -13756), math.random(16348, 16548), 2400)

    for i = 1, 6 do
        local x = math.random(-20549, -7225)
        local y = math.random(11879, 18122)
        evt.CastSpell(9, 4, 10, x, y, 5084, x, y, 3000)
    end
end

MM6.RegisterNicolaiStateOnLoad()
MM6.RegisterNicolaiKidnapTimer()
