-- MMMerge map supplement: reactor/queen ending flow.

local function isReactorMonster(monsterId)
    return monsterId == 647 or monsterId == 648
end

local function reactorKilled()
    return evt.GetMapVar("HiveReactorKilled", 0) ~= 0
end

local function queenKilled()
    return evt.GetMapVar("HiveQueenKilled", 0) ~= 0
end

local function partyHasRitualOfTheVoid()
    evt.ForPlayer(Players.All)
    return HasItem(2164)
end

local function badEnd()
    evt.ShowMovie("mm6end2", false)
    evt.PlaySound(130)
    evt.ReturnToMainMenu()
end

local function goodEnd()
    SetQBit(QBit(784))
    if CrossContinents ~= nil and CrossContinents.MarkContinentFinished ~= nil then
        CrossContinents.MarkContinentFinished(3)
    end
    ClearQBit(QBit(1222))
    evt.ForPlayer(Players.All)
    RemoveItem(2164) -- Ritual of the Void
    SetAward(Award(78))
    evt.ShowMovie("mm6end1", false)
end

local function summonReactorAmbush()
    evt.SummonMonsters(2, 3, 1, 4352, 20096, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 6016, 21504, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 2816, 22016, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 4352, 24704, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 2944, 23552, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 6144, 23424, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 2688, 19840, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 1920, 21760, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 6144, 19840, -2256, 0, 0)
    evt.SummonMonsters(2, 3, 1, 7168, 21760, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 2584, 25728, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 5248, 25728, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 1792, 23168, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 2688, 25216, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 7296, 23040, -2256, 0, 0)
    evt.SummonMonsters(1, 3, 1, 6144, 25088, -2256, 0, 0)
end

local function openReactorDoors()
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
    evt.SetDoorState(53, DoorAction.Close)
end

local function restorePartyAfterReactor()
    evt.ForPlayer(Players.All)
    SetValue(MajorCondition, 0)
    AddValue(HasFullHP, 0)
    AddValue(HasFullSP, 0)
end

RegisterMonsterDamageHook(65010, "Hive reactor physical damage override", function(context)
    if isReactorMonster(context.monsterId) and context.damageType == const.Damage.Physical then
        evt.SetHookDamage(math.random(2, 40))
    end
end)

RegisterMonsterKilledHook(65011, "Hive reactor and queen kill flow", function(context)
    if reactorKilled() and context.monsterId == 646 then
        evt.SetMapVar("HiveQueenKilled", 1)
        SetQBit(QBit(1226))
        return
    end

    if not isReactorMonster(context.monsterId) then
        return
    end

    if partyHasRitualOfTheVoid() then
        evt.SetMapVar("HiveReactorKilled", 1)
        summonReactorAmbush()
        openReactorDoors()
        evt.MoveToMap(
            3328 + math.random(-120, 120),
            25920 + math.random(-120, 120),
            -2256,
            512,
            0,
            0,
            0,
            0)
        restorePartyAfterReactor()
    else
        badEnd()
    end
end)

RegisterMapOnLeaveEvent(65012, "Hive ending", function()
    if reactorKilled() then
        if queenKilled() and partyHasRitualOfTheVoid() then
            goodEnd()
        else
            badEnd()
        end
    end
end)

ReplaceMapEvent(60, "Exit", function()
    if IsQBitSet(QBit(1226)) then
        evt.MoveToMap(0, 0, 0, 0, 0, 0, 0, 0, "oute3.odm")
    else
        evt.StatusText("The door is locked")
    end
end, "Exit")
SetMapContextAction(60, {kind = "leave_dungeon", source = "authored", targetMap = "oute3.odm", targetName = "Exit"})
