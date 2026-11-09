-- D8's authored event source. Geometry cogs 180-184 are the beds; 185 is the hall's heat plates.
local handlers = {}
local LAVA = 0x40000000
local DEAD, CLEARED = 100450, 100451
local valveChannels = {1, 2, 3, 4, 5, 4, 5}
SetMapMetadata({onLoad = {2}, onLeave = {}, timers = {}})

local function channel(index, frozen)
    evt.SetFacetBit(179 + index, LAVA, not frozen)
    evt.SetTexture(179 + index, frozen and "hmchanx" or "hmchan")
    evt.SetLight(10 + index, not frozen)
    for valve, target in ipairs(valveChannels) do
        if target == index then
            evt.SetSprite(159 + valve, 1, frozen and "hes_valve_sooted_turned" or "hes_valve_sooted")
            evt.SetSprite(259 + valve, 1, frozen and "hes_valve_body_open" or "hes_valve_body")
        end
    end
end

local function stoke(warning, burning)
    evt.SetTexture(185, warning and "hmplatehot" or "hmplate")
    evt.SetFacetBit(185, LAVA, burning)
end

local function bossBehavior()
    evt.SetActorBehavior(BOSS_ACTOR, "hesper/bosses/forgemaster")
end

handlers[1] = function()
    for index = 1, 5 do
        SetValue(MapVar(6 + index), 0)
        channel(index, false)
    end
    SetValue(MapVar(6), 0)
    stoke(false, false)
    evt.SetMonGroupBit(34, MonsterBits.Hostile, true)
    for index = 1, 3 do
        if IsQBitSet(QBit(CLEARED)) or evt.GetMapVar("d8.diverter" .. index) == 1 then
            evt.SetDoorState(61 + index, DoorAction.Open)
            evt.SetSprite(169 + index, 1, "hes_diverter_thrown")
        end
    end
    if IsQBitSet(QBit(DEAD)) then
        evt.SetDoorState(67, DoorAction.Open)
        evt.SetMonGroupBit(31, MonsterBits.Invisible, true)
    else
        bossBehavior()
    end
end

handlers[2] = function() SetAutonote(10130) end
handlers[4] = function()
    for index = 1, 5 do
        local variable = MapVar(6 + index)
        if IsAtLeast(variable, 1) then
            AddValue(variable, 1)
            if IsAtLeast(variable, 21) then
                channel(index, false)
                SetValue(variable, 0)
                evt.StatusText("The channel glows again.")
            elseif IsAtLeast(variable, 18) and not IsAtLeast(variable, 19) then
                evt.StatusText("The coolant sputters.")
            end
        end
    end
end

handlers[9] = function()
    if not IsAtLeast(MapVar(6), 1) or IsQBitSet(QBit(DEAD)) then return end
    AddValue(MapVar(6), 1)
    if IsAtLeast(MapVar(6), 36) then
        stoke(false, false)
        SetValue(MapVar(6), 6)
    elseif IsAtLeast(MapVar(6), 30) then
        stoke(true, true)
    elseif IsAtLeast(MapVar(6), 28) then
        stoke(true, false)
        if not IsAtLeast(MapVar(6), 29) then evt.StatusText("Burn!") end
    end
end

handlers[10] = function() evt.StatusText("A foundry sigil: from their machines, our blades.") end
handlers[11] = function() evt.StatusText("A belt sigil: one belt, one crate. Each belt has its own diverter.") end
for event, chest in pairs({[30]=1, [32]=2, [33]=3, [31]=4, [34]=5, [35]=6, [38]=7, [39]=8}) do
    handlers[event] = function() evt.OpenChest(chest) end
end
for event, variable in pairs({[36]=2, [37]=3}) do
    handlers[event] = function()
        if IsAtLeast(MapVar(variable), 1) then evt.StatusText("The shelf is empty.") return end
        for _, item in ipairs({11300, 11300, 11302, 11304}) do AddValue(InventoryItem(item), item) end
        SetValue(MapVar(variable), 1)
        evt.StatusText("A shelf of a Lancer's kit: two Shield Cells, a Stim and a Breach Charge.")
    end
end

handlers[50] = select(1, SCOUR_EXIT, nil)

local function hacks(mastery)
    evt.ForPlayer(Players.All)
    return evt.CheckSkill(const.Skills.Hacking, mastery, 1)
end

local function freeze(index)
    if not hacks(const.SkillCheck.Novice) then
        evt.StatusText("The coolant valve's lock is a Kreegan cipher. A hacker could turn it.")
    elseif IsAtLeast(MapVar(6 + index), 1) then
        evt.StatusText("Coolant is already running.")
    else
        channel(index, true)
        SetValue(MapVar(6 + index), 1)
        evt.StatusText("Coolant floods the channel. The slag goes dark and hard: for a little while.")
    end
end
for event, index in pairs({[70]=1, [71]=2, [72]=3, [80]=4, [81]=5, [82]=4, [83]=5}) do
    handlers[event] = function() freeze(index) end
end

for index = 1, 3 do
    handlers[73 + index] = function()
        if IsQBitSet(QBit(CLEARED)) or evt.GetMapVar("d8.diverter" .. index) == 1 then
            evt.StatusText("The diverter is already thrown.")
            return
        end
        -- The count alone cannot preserve which partial diverters were thrown across a reload.
        evt.SetMapVar("d8.diverter" .. index, 1)
        evt.SetSprite(169 + index, 1, "hes_diverter_thrown")
        evt.SetDoorState(61 + index, DoorAction.Open)
        AddValue(MapVar(4), 1)
        if IsAtLeast(MapVar(4), 3) then
            SetQBit(QBit(CLEARED))
            SetAutonote(10131)
            evt.StatusText("The main belt runs clear.")
        else
            evt.StatusText("The diverter drops; a crate tumbles off the jam into its chute.")
        end
    end
end
handlers[77] = function()
    if hacks(const.SkillCheck.Master) then
        evt.SetMonGroupBit(34, MonsterBits.Hostile, false)
        evt.StatusText("The guns swing aside and stand down.")
    else
        evt.StatusText("Kreegan turret controls. A Master hacker could stand the range's guns down.")
    end
end

handlers[150] = function()
    if IsQBitSet(QBit(DEAD)) then return end
    if not IsAtLeast(MapVar(12), 1) then
        SetValue(MapVar(12), 1)
        evt.StatusText("The Forgemaster: Soft hands in my Foundry. I will press you into plate.")
        evt.PlaySoundName("vo_forgemaster_sight")   -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
    end
    if not IsAtLeast(MapVar(6), 1) then SetValue(MapVar(6), 1) end
end
handlers[151] = function()
    if IsQBitSet(QBit(DEAD)) or not evt.CheckMonstersKilled(ActorKillCheck.Group, 31, 0, false) then return end
    SetQBit(QBit(DEAD))
    evt.SummonItem(11423, 4200, 11200, 0, 0, 1, false)
    evt.SummonItem(11332, 4200, 11200, 0, 0, 1, false)
    evt.SetDoorState(67, DoorAction.Open)
    SetValue(MapVar(6), 0)
    stoke(false, false)
    SetAutonote(10132)
end
handlers[153] = function()
    evt.SetDoorState(95, DoorAction.Open)
    SetValue(MapVar(6), 0)
    stoke(false, false)
end
for _, door in ipairs({60, 61, 65, 66, 68, 69, 90, 91, 92, 93, 94}) do
    handlers[100 + door] = function()
        evt.SetDoorState(door, DoorAction.Open)
        if door == 66 then evt.StatusText("Behind the crust, a colony foundryman's locker, and the foundryman.") end
    end
end
handlers[167] = function() evt.StatusText("Sealed with the Forgemaster's sigil.") end

-- Hesper's normal clock advances 30 game seconds per real second (as out1's drone timer).
RegisterEvent(2, "The Foundry", handlers[2])
RegisterMapTimerEvent(4, 30, handlers[4], "Coolant", "", 30)
RegisterMapTimerEvent(9, 30, handlers[9], "Stoking", "", 30)
RegisterMonsterKilledHook(151, "The Forgemaster", handlers[151])

-- GetCurrentMapName returns the display title; use this dungeon's H3 treasure level explicitly.
HesperPickups.setup({treasure = 6,
    canisters = {}, vats = {701, 702, 703, 704, 705, 706, 707, 708, 709, 710},
    satchels = {}, bundles = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770},
})
