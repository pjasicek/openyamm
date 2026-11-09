-- Authored D3 events. Numeric map variables 1-6 follow the build document.
local handlers = {}
local KRAV = {KRAV_ACTOR, }
local BARRACKS = {BARRACKS_ACTORS, }
local EXIT = {SCOUR_EXIT, }
SetMapMetadata({onLoad = {}, onLeave = {6}, timers = {}})

local function bit(id) return IsQBitSet(QBit(id)) end
local function value(id)
    -- EVT exposes numeric map bytes through comparisons, not GetMapVar's named-variable table.
    local n = 0
    for bitIndex = 7, 0, -1 do
        local candidate = n + 2 ^ bitIndex
        if IsAtLeast(MapVar(id), candidate) then n = candidate end
    end
    return n
end
local function set(id, n) SetValue(MapVar(id), n) end
local function hacker(mastery)
    -- Party-wide Hacking is the integrator's accepted rule.
    return evt.CheckSkill(const.Skills.Hacking, mastery or const.SkillCheck.Novice, 1)
end
local function hidden(group, state) evt.SetMonGroupBit(group, MonsterBits.Invisible, state) end
local function hostile(group, state) evt.SetMonGroupBit(group, MonsterBits.Hostile, state) end

local function pylonOff()
    evt.SetLight(1, false)
    evt.SetTexture(70, "hkpylonx")
end

handlers[2] = function()
    if evt.GetMapVar("d3_initialized") == 1 then return end
    evt.SetMapVar("d3_initialized", 1)
    for _, group in ipairs({32, 33, 34, 40, 41}) do hidden(group, true) end
    SetAutonote(10110)
end

handlers[1] = function()
    handlers[2]()
    set(1, 0)
    set(4, 0)
    for _, group in ipairs({10, 11, 21, 22, 23, 24, 25, 26, 27, 30, 31}) do hostile(group, true) end
    hostile(20, bit(100403))
    evt.SetLight(2, false)
    if bit(100402) then pylonOff() end
    if bit(100403) then
        evt.SetSprite(140, 1, "hes_drop_pod_open")
        evt.SetSprite(141, 1, "hes_drop_pod_open")
    end
    if bit(100408) then
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetTexture(73, "hkconsok")
    end
    if bit(100409) then
        evt.SetLight(3, false)
        evt.SetTexture(76, "hkloomx")
    end
    for k = 0, value(2) - 1 do
        evt.SetFacetBit(132 + k, FacetBits.Invisible + FacetBits.Untouchable, true)
    end
    if bit(100024) then
        evt.SetDoorState(54, DoorAction.Open)
        for group = 32 + value(2), 34 do hidden(group, true) end
    elseif value(6) == 1 then
        evt.SetActorBehavior(KRAV[1], "hesper/bosses/krav")
    end
end

handlers[6] = function() set(1, 0) end

handlers[3] = function()
    if not bit(100402) then evt.PlaySoundName("d03_pylon", 3800, 2300, -220) end
    if value(1) == 0 or bit(100403) then return end
    set(1, value(1) + 1)
    if value(1) >= 4 and not (bit(100401) and bit(100402)) and not bit(100409) then handlers[153]() end
end
handlers[4] = function()
    if value(4) == 0 then return end
    set(4, value(4) + 1)
    if value(4) >= 21 then handlers[154]() end
end
handlers[5] = function()
    if value(6) ~= 1 or bit(100024) or value(2) >= 3 then return end
    set(5, value(5) + 1)
    if value(5) == 19 then
        evt.SetTexture(132 + value(2), "hkvein")
        evt.PlaySoundName("d03_cage", 150, 2700 + 600 * value(2), 160)
    end
    if value(5) >= 20 then
        handlers[152]()
        set(5, 0)
    end
end
handlers[7] = function() evt.PlaySoundName("d03_crusher", 2450, -600, -1400) end

local texts = {
    [10] = 'Aster: "The watch sigil means see, and call. That pylon sees the open ground. Keep to the heaps."',
    [11] = "A squad sigil: we rest, we rise. Tread softly.",
    [12] = "An Overseer's sigil, freshly cut: Krav, who keeps this Yard.",
}
for event, text in pairs(texts) do handlers[event] = function() evt.SimpleMessage(text) end end
for event = 30, 35 do
    local chest = event - 29
    handlers[event] = function() evt.OpenChest(chest) end
end
handlers[36] = function()
    -- As D1's shelf cache: native contents persist if the player leaves without taking everything.
    evt.OpenChest(0)
    set(3, 1)
    evt.StatusText("A resin shelf by the stair: two Shield Cells and a Stim, a Trooper's kit.")
end
handlers[50] = function()
    if not EXIT[1] then
        evt.StatusText("The Outer Gate: the way is not yet open.")
        return
    end
    evt.MoveToMap(EXIT[2], EXIT[3], EXIT[4], EXIT[5], 0, 0, 0, 0, "hes_out2.odm")
end
for event = 51, 53 do
    local door = event
    handlers[event] = function()
        evt.SetDoorState(door, DoorAction.Trigger)
        evt.PlaySoundName("d03_membrane")
    end
end
handlers[54] = function()
    if bit(100024) then evt.SetDoorState(54, DoorAction.Trigger)
    else evt.StatusText("The membrane is sealed. It answers only the Overseer.") end
end
handlers[55] = function()
    if bit(100408) then evt.SetDoorState(55, DoorAction.Trigger)
    else evt.StatusText("Sealed. The foreman's console in the stores opens it.") end
end
handlers[58] = function() evt.SetDoorState(58, DoorAction.Open) end

handlers[70] = function(step)
    if bit(100402) then return end
    local canHack = hacker()
    if not canHack and not HasItem(11304) then
        evt.StatusText("The pylon's eye turns slowly. Hacking, or a Breach Charge, would kill it.")
        return
    end
    if step == 2 then return end
    if step ~= 1 then
        AskChoiceWithAnswerSteps(70, 2, canHack and "Hack the pylon?"
            or "Set a Breach Charge on the pylon?", {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})
        return
    end
    if not canHack then RemoveItem(11304) end
    SetQBit(QBit(100402))
    pylonOff()
    evt.StatusText(canHack and "The eye dims to a cinder. The Yard goes quiet."
        or "The charge splits the spine; the eye gutters out.")
end
for event, group in pairs({[71] = 10, [72] = 11}) do
    handlers[event] = function()
        if hacker(const.SkillCheck.Master) then
            evt.SetTexture(event, "hkconsok")
            hostile(group, false)
            evt.StatusText("The turrets swing aside and stand down.")
        else evt.StatusText("Kreegan turret controls. Only a Master hacker could stand these down.") end
    end
end
handlers[73] = function()
    if hacker() then
        SetQBit(QBit(100408))
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetTexture(73, "hkconsok")
    else evt.StatusText("A Kreegan console with grafted Ancient keys. A hacker could open the lab door from here.") end
end
for event, door in pairs({[74] = 56, [75] = 56, [78] = 57, [79] = 57}) do
    handlers[event] = function() evt.SetDoorState(door, DoorAction.Trigger) end
end
handlers[76] = function()
    if not hacker() then
        evt.StatusText("A Kreegan signal loom, its coils humming. A hacker could silence it.")
        return
    end
    SetQBit(QBit(100409))
    set(1, 0)
    evt.SetLight(3, false)
    evt.SetTexture(76, "hkloomx")
    evt.StatusText("The loom falls silent. Nothing here will call the pods again.")
end
handlers[77] = function()
    if bit(100403) or bit(100409) or (bit(100401) and bit(100402)) or value(1) > 0 then return end
    set(1, 1)
    if evt.GetMapVar("d3_warned") ~= 1 then
        evt.SetMapVar("d3_warned", 1)
        evt.StatusText("The pylon's eye fixes on you.")
    end
end
handlers[80] = function() set(1, 0) end
handlers[81] = function(context)
    for _, index in ipairs(BARRACKS) do
        if context.actorIndex == index then hostile(20, true); return end
    end
end
handlers[150] = function()
    if value(6) == 1 or bit(100024) then return end
    set(6, 1)
    evt.StatusText("Overseer Krav: The Yard eats colonists. Squad, feed it.")
    evt.PlaySoundName("vo_krav_sight")   -- voiced (design/kreegan_world/audio/BOSS_LINES.md), non-positional
    evt.SetActorBehavior(KRAV[1], "hesper/bosses/krav")
end
handlers[151] = function()
    if bit(100024) or not evt.CheckMonstersKilled(ActorKillCheck.Group, 30, 0, false) then return end
    SetQBit(QBit(100024))
    evt.SetDoorState(54, DoorAction.Open)
    evt.PlaySoundName("d03_membrane", 1150, 4296, 160)
    evt.SummonItem(11022, 1100, 3050, 0, 0, 1, false)
    evt.SummonItem(11332, 1100, 3050, 0, 0, 1, false)
    -- shortcut: SummonItem cannot set a gold heap's value; pay the exact reward until the integrator adds that API.
    AddValue(VarTag.Gold, 10000)
    evt.StatusText("Krav's purse holds 10 000 gold.")
    for group = 32 + value(2), 34 do hidden(group, true) end
    SetAutonote(10111)
end
handlers[152] = function()
    if bit(100024) or value(2) >= 3 then return end
    local group = 32 + value(2)
    evt.SetFacetBit(100 + group, FacetBits.Invisible + FacetBits.Untouchable, true)
    hidden(group, false)
    hostile(group, true)
    if value(2) == 0 then evt.StatusText("Diggers, up! Feed on them.") end
    set(2, value(2) + 1)
end
handlers[153] = function()
    if bit(100403) then return end
    SetQBit(QBit(100403))
    set(1, 0)
    set(4, 1)
    evt.SetLight(2, true)
    hostile(20, true)
    hidden(40, false)
    hostile(40, true)
    evt.SetSprite(140, 1, "hes_drop_pod_open")
    evt.PlaySoundName("d03_alarm", 3800, 700, -300)
    evt.PlaySoundName("d03_pod", 3400, 500, -768)
    evt.StatusText("A horn shrieks through the outpost. The pods along the Yard are splitting open!")
end
handlers[154] = function()
    hidden(41, false)
    hostile(41, true)
    evt.SetSprite(141, 1, "hes_drop_pod_open")
    evt.PlaySoundName("d03_pod", 4200, 500, -768)
    set(4, 0)
    evt.StatusText("More pods burst.")
end

-- The clock advances 30 game seconds per real second, indoors and outdoors.
for event = 3, 5 do RegisterMapTimerEvent(event, 30, handlers[event], "Quarry timer " .. event, "", 30) end
RegisterMapTimerEvent(7, 120, handlers[7], "Crusher", "", 120)
RegisterMonsterKilledHook(151, "Krav's death", handlers[151])
RegisterMonsterDamageHook(81, "The Barracks wake", handlers[81])
RegisterEvent(6, "Leave the Quarry", handlers[6])

-- GetCurrentMapName returns the display title; pass this dungeon's H1/H2 treasure level explicitly.
HesperPickups.setup({
    treasure = 5,
    vats = {701, 702, 703, 704, 705, 706, 707, 708},
    bundles = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770}
})
