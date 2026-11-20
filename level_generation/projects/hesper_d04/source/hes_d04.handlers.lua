-- Authored D4 events; generated bindings and actor indices come from build_d04.py.
local handlers = {}
local ACTOR_GROUPS = {ACTOR_BINDINGS, }
local SCOUR = select(1, SCOUR_BINDING, nil)
local KEPT = {[31]=true, [40]=true, [41]=true, [42]=true, [43]=true, [44]=true, [45]=true}
local function freed() return IsQBitSet(QBit(100027)) end
local function bossIndex()
    for index, group in pairs(ACTOR_GROUPS) do if group == 30 then return index end end
end
local function showCollars()
    evt.SetLight(1, freed() and 0 or 1)
    evt.SetLight(2, freed() and 0 or 1)
    evt.SetLight(3, freed() and 1 or 0)
    evt.SetTexture(170, freed() and "hkcollof" or "hkcollar")
    if freed() then evt.SetDoorState(59, DoorAction.Open) end
end
handlers[1] = function()
    evt.SetMonGroupBit(40, MonsterBits.Hostile, false)
    evt.SetMonGroupBit(42, MonsterBits.Hostile, false)
    for _, group in ipairs({90,91}) do evt.SetMonGroupBit(group, MonsterBits.Hostile, false) end
    showCollars()
    if freed() then
        for group in pairs(KEPT) do evt.SetMonGroupBit(group, MonsterBits.Invisible, true) end
    end
    if IsQBitSet(QBit(100025)) then
        evt.SetDoorState(56, DoorAction.Open)
        evt.SetSprite(150, 1, "hes_cell_lever_pulled")
        evt.SetMonGroupBit(90, MonsterBits.Invisible, true)
    end
    if IsQBitSet(QBit(100026)) then
        evt.SetDoorState(57, DoorAction.Open)
        evt.SetTexture(173, "hkconsok")
        evt.SetMonGroupBit(91, MonsterBits.Invisible, true)
    end
    if not IsQBitSet(QBit(100430)) then evt.SetActorBehavior(bossIndex(), "hesper/bosses/ghulkat") end
    SetAutonote(10120)
end
handlers[2] = function() SetAutonote(10120) end

handlers[3] = function()
    AddValue(MapVar(3), 1)
    if IsAtLeast(MapVar(3), 12) then SetValue(MapVar(3), 0) end
    for second = 0, 11 do
        if IsAtLeast(MapVar(3), second) and not IsAtLeast(MapVar(3), second+1) then
            for chute = 0, 2 do
                local phase = (second - chute*4) % 12
                evt.SetTexture(160+chute, phase < 3 and "hmchan" or "hmchanx")
                evt.SetFacetBit(160+chute, FacetBits.Lava, phase == 1 or phase == 2)
            end
        end
    end
end
handlers[10] = function()
    evt.SimpleMessage("A tally sigil: four hundred and twelve hands in the Pens; eleven spent. The Kept are counted like ore.")
end
handlers[12] = function()
    evt.SimpleMessage("A collar sigil: every collar answers the bank above.\n\nAster: The console behind those windows holds their collars.")
end
for event=30,35 do handlers[event] = function() evt.OpenChest(event-29) end end
handlers[36] = function()
    if IsAtLeast(MapVar(2),1) then evt.StatusText("The shelf is empty."); return end
    evt.ForPlayer(Players.Current)
    for _, id in ipairs({11300,11300,11302}) do AddValue(InventoryItem(id),id) end
    SetValue(MapVar(2),1)
    evt.SimpleMessage("A shelf by the gate: two Shield Cells and a Stim, taken from some Hesperian scout.")
end
handlers[50] = function()
    if not SCOUR then
        evt.StatusText("The Pit Stairs' door: the way is not yet open.")
        return
    end
    evt.MoveToMap(table.unpack(SCOUR))
end
for event=51,55 do handlers[event] = function() evt.SetDoorState(event,DoorAction.Trigger) end end
handlers[58] = function()
    evt.SetDoorState(58,DoorAction.Open)
    evt.StatusText("Behind the slag, a hollow the Drudges kept for themselves.")
end
handlers[70] = function(step)
    if freed() then evt.StatusText("The bank stands open; every socket is dark."); return end
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(const.Skills.Hacking,const.SkillCheck.Novice,1) and not HasItem(11483) then
        evt.StatusText("A bank of collar sockets, each lit violet-red. A hacker could release them, or the Overseer's key.")
        return
    end
    if step == 2 then return end
    if step ~= 1 then
        AskChoiceWithAnswerSteps(70,0,"Release every collar?",{{Answer="Yes",Step=1},{Answer="No",Step=2}})
        return
    end
    SetQBit(QBit(100027))
    evt.SetMonGroupBit(40,MonsterBits.Hostile,false)
    evt.SetMonGroupBit(42,MonsterBits.Hostile,false)
    showCollars()
    if not IsQBitSet(QBit(100720)) then
        AddValue(ReputationInCurrentLocation,-2)
        SetQBit(QBit(100720))
    end
    SetAutonote(10122)
    evt.SimpleMessage("Every socket goes dark at once. Below, a roar goes up from the Pens."
        .. (IsQBitSet(QBit(100430)) and "" or "\n\nGhulkat: No! Back! Back in your collars!"))
end
handlers[72] = function()
    evt.SetDoorState(56,DoorAction.Open)
    evt.SetSprite(150,1,"hes_cell_lever_pulled")
    if IsQBitSet(QBit(100025)) then return end
    SetQBit(QBit(100025))
    evt.SimpleMessage("Tamsin: Out. I know the way home; don't wait for me. Get Ilse out of the Surgery too. She kept half of us alive in here.")
end
handlers[73] = function()
    evt.SetDoorState(57,DoorAction.Open)
    evt.SetTexture(173,"hkconsok")
    if IsQBitSet(QBit(100026)) then return end
    SetQBit(QBit(100026))
    evt.SimpleMessage("Doctor Ilse: I will walk to the Undervault on my own feet. I've been looking forward to it. Spare the collared ones; they are our people.")
end
handlers[74] = function() evt.SetDoorState(60,DoorAction.Trigger) end
handlers[75] = handlers[74]
handlers[76] = function() evt.SetDoorState(61,DoorAction.Trigger) end
handlers[81] = function()
    local group = ACTOR_GROUPS[evt.GetHookContext().actorIndex]
    if not freed() and (group == 40 or group == 42) then evt.SetMonGroupBit(group,MonsterBits.Hostile,true) end
end
handlers[150] = function()
    if IsAtLeast(MapVar(4),1) or IsQBitSet(QBit(100430)) then return end
    SetValue(MapVar(4),1)
    evt.StatusText("Ghulkat: More meat for the Pens. Forward!")
    evt.PlaySoundName("vo_ghulkat_sight")   -- voiced (design/kreegan_world/audio/BOSS_LINES.md), non-positional
    evt.SetActorBehavior(bossIndex(),"hesper/bosses/ghulkat")
end
handlers[151] = function()
    if ACTOR_GROUPS[evt.GetHookContext().actorIndex] ~= 30 or IsQBitSet(QBit(100430)) then return end
    SetQBit(QBit(100430))
    SetAutonote(10121)
    evt.SummonItem(11024,2900,-700,-512,0,1,false)
    evt.SummonItem(11483,3000,-700,-512,0,1,false)
    -- SummonItem has no gold-amount argument; keep the guaranteed reward instead of a random pile.
    AddValue(Gold,10000)
    evt.StatusText("Ghulkat's belt purse: 10 000 gold.")
end
handlers[152] = function()
    if freed() or IsAtLeast(MapVar(1),1) or not KEPT[ACTOR_GROUPS[evt.GetHookContext().actorIndex]] then return end
    SetValue(MapVar(1),1)
    evt.StatusText("A collar dims. The Hesperians will hear of this.")
end
-- One real second is 30 game seconds. Registration owns the lifecycle lists once, outside the load handler.
SetMapMetadata({onLoad={},onLeave={},timers={}})
for _, event in ipairs({56,57}) do
    RegisterEvent(event,"Occupied cage",function() end,"Someone moves behind the bars.")
end
RegisterMapTimerEvent(3,30,handlers[3],"Slag chutes")
RegisterMonsterDamageHook(81,"Wake resting Kept",handlers[81])
RegisterMonsterKilledHook(151,"Ghulkat's death",handlers[151])
RegisterMonsterKilledHook(152,"A collar dims",handlers[152])

-- GetCurrentMapName returns the display title; use this dungeon's H2 treasure level explicitly.
HesperPickups.setup({treasure = 5,
    canisters = {}, vats = {701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712},
    satchels = {}, bundles = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767},
})
