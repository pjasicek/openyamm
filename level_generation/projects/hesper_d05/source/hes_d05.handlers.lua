-- D5 Relay Spire. Authored source; build_d05.py supplies arrivals and registrations.
local handlers = {}
SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {
    {eventId = 3, intervalGameMinutes = 0.25, repeating = true},
    {eventId = 4, intervalGameMinutes = 0.5, repeating = true}}})

local function deaf()
    return IsAtLeast(MapVar(1), 1)
end

local function pulse()
    local step = 0
    for k = 1, 5 do
        if IsAtLeast(MapVar(2), k) then step = k end
    end
    for k = 0, 5 do evt.SetLight(21 + k, not deaf() and k == step and 1 or 0) end
    if deaf() then evt.SetTexture(176, "hkloomx") end
end

local function ring()
    local lit = IsQBitSet(QBit(100007)) and not IsQBitSet(QBit(100016))
    evt.SetLight(2, lit and 1 or 0)
    evt.SetTexture(170, lit and "hkwebon" or "hkweb")
end

handlers[2] = function() SetAutonote(10220) end
handlers[1] = function()
    handlers[2]()
    pulse()
    ring()
    if IsQBitSet(QBit(100028)) then
        evt.SetMonGroupBit(21, const.MonsterBits.Invisible, 1)
        evt.SetDoorState(52, DoorAction.Open)
    else
        evt.SetActorBehavior(68, "hes_vhorrax_d5")
    end
    if IsAtLeast(MapVar(3), 1) then
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetTexture(175, "hkconsok")
    end
end
handlers[3] = function()
    if deaf() then return end
    if IsAtLeast(MapVar(2), 5) then SetValue(MapVar(2), 0) else AddValue(MapVar(2), 1) end
    pulse()
end
-- Lord Vhorrax's first sight (design/kreegan_world/audio/BOSS_LINES.md): his voiced line once per save, here or in
-- D11's Duelling Gallery, whichever comes first (QBit 100540, P2's block). Within 2 200 of him, as his behaviour's
-- old greeting; polled by the timer below.
local function vhorraxSight()
    if IsQBitSet(QBit(100540)) or IsQBitSet(QBit(100028)) or not evt.IsMapActorWithinPartyDistance(68, 2200) then
        return
    end
    SetQBit(QBit(100540))
    evt.StatusText("Lord Vhorrax: You are far from your dirt, little colonists.")
    evt.PlaySoundName("vo_vhorrax_sight")
end
handlers[4] = function()
    vhorraxSight()
    if not IsQBitSet(QBit(100028)) and evt.CheckMonstersKilled(1, 21, 0, 0) then handlers[150]() end
end

handlers[10] = function()
    if IsQBitSet(QBit(100034)) then evt.SimpleMessage("..."); return end
    if IsQBitSet(QBit(100007)) then
        evt.SimpleMessage("The gate holds. Step through when you like; the far end will know you.")
    elseif HasItem(11470) then
        SetQBit(QBit(100007))
        ClearQBit(QBit(100207))
        SetAutonote(10404)
        evt.ForPlayer(Players.All)
        AddValue(Experience, 20000)
        ring()
        evt.SimpleMessage("Hold it to the post. I have its pattern now. Stand back from the ring.\n\n"
            .. "Light runs round the broken ring like water finding old channels. The arch hums, steadies, "
            .. "and opens on a gray distance: somewhere very far away, and home.")
    else
        evt.SimpleMessage("This was a gate of the Web, my makers' bridge between worlds; the devils broke it. "
            .. "Bring me the jammer from the crown: its pattern is the key I lack.")
    end
end
local texts = {
    [11] = "A watch sigil, cut over the door: hear the sky; call the Lattice.\n\nAster: It heard you come down, I think.",
    [12] = "A roster sigil: the Spire's fire teams, their turns at the lifts.\n\n"
        .. "Aster: One team is scored out. Gone to the egg fields.",
    [13] = "A roost sigil: the Overseer keeps the shaft; the Noble keeps the crown.",
    [14] = "A Noble's sigil, cut deep and gilded: Vhorrax, whose blade is courtesy.\n\n"
        .. "Aster: He signs his tower the way a painter signs a picture.",
    [15] = "An Ancient power core, white and gold under the roots that grip it. "
        .. "It beats cold light up the shaft, once every three heartbeats.",
}
for event, text in pairs(texts) do handlers[event] = function() evt.SimpleMessage(text) end end
for event = 30, 37 do
    handlers[event] = function() evt.OpenChest(event - 30) end
end
handlers[32] = function()
    if not IsQBitSet(QBit(100028)) then handlers[52](); return end
    evt.OpenChest(2)
    if not deaf() then
        SetValue(MapVar(1), 1)
        pulse()
        evt.StatusText("As the Jammer comes out of its cradle, the light in the shaft falters and goes out. "
            .. "Far below, something in the roots goes quiet.")
    end
end
handlers[50] = function()
    evt.MoveToMap(BROOD_ARRIVAL, "hes_out3.odm")
end
handlers[51] = function()
    if IsAtLeast(MapVar(3), 1) then evt.SetDoorState(51, DoorAction.Open)
    else evt.StatusText("Sealed from inside. The console beside it is the way.") end
end
handlers[52] = function()
    if IsQBitSet(QBit(100028)) then evt.SetDoorState(52, DoorAction.Open)
    else evt.StatusText("A membrane seal, tight as a drum. Something up here is not finished with you.") end
end
for door = 201, 220 do
    handlers[door] = function() evt.SetDoorState(door, DoorAction.Trigger) end
end
handlers[70] = function(continueStep)
    if continueStep == 1 then evt.SimpleMessage("The thread will not hold yet."); return end
    if continueStep == 2 then return end
    if IsQBitSet(QBit(100016)) then evt.SimpleMessage("The ring is dark.")
    elseif IsQBitSet(QBit(100007)) then
        AskChoiceWithAnswerSteps(70, 0, "The ring hums. Through it, very far away: home. Step through?",
            {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})
    else
        evt.SimpleMessage("A ring of white ceramic and gold, taller than a man, set in resin. Inside it the dark "
            .. "of a dead thread. Aster could tell you what it was. Aster could tell you what it could be.")
    end
end
for event, door in pairs({[71] = 53, [72] = 53, [73] = 54, [74] = 54}) do
    handlers[event] = function() evt.SetDoorState(door, DoorAction.Trigger) end
end
handlers[75] = function()
    evt.ForPlayer(Players.All)
    if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Expert, 1) then
        SetValue(MapVar(3), 1)
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetTexture(175, "hkconsok")
    else
        evt.StatusText("The console's keys are Ancient, rewired in resin. An expert could talk to it.")
    end
end
handlers[76] = function()
    if deaf() then evt.SimpleMessage("The coils are dark. The looms weave nothing. The Spire is deaf.")
    else evt.SimpleMessage("The looms weave light: every pulse up the shaft is the sky, listened to. "
        .. "Somewhere above, the listening is gathered into one small thing in a cradle.") end
end
handlers[150] = function()
    if IsQBitSet(QBit(100028)) then return end
    evt.SetMonGroupBit(21, const.MonsterBits.Invisible, 1)
    SetQBit(QBit(100028))
    SetAutonote(10221)
    evt.SetDoorState(52, DoorAction.Open)
end
-- Non-face lifecycle and boss hooks must be registered as well as the builder's interaction events.
for _, event in ipairs({2, 3, 4, 150}) do RegisterEvent(event, "Relay Spire", handlers[event], "") end

-- GetCurrentMapName returns the display title; use this dungeon's H2 treasure level explicitly.
HesperPickups.setup({treasure = 5,
    canisters = {}, vats = {},
    satchels = {}, bundles = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770},
})
