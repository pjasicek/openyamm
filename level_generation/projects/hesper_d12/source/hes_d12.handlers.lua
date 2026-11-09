-- Authored D12 events. Variables 1-6 follow the design; named variables persist timer/once-only details.
local handlers = {}
local EXITS = select(1, D12_EXITS, nil)
local ACTORS = select(1, D12_ACTORS, nil)
local BOSSES = select(1, D12_BOSSES, nil)
local INVISIBLE = MonsterBits.Invisible
SetMapMetadata({onLoad = {}, onLeave = {}, timers = {{eventId = 4, repeating = true, intervalGameMinutes = 0.5}}})

local function bit(n) return IsQBitSet(QBit(n)) end
local function dead(group) return evt.CheckMonstersKilled(ActorKillCheck.Group, group, 0, false) end
local function hidden(group, value) evt.SetMonGroupBit(group, INVISIBLE, value and 1 or 0) end
local function phase() return evt.GetMapVar('throne_phase') end
local function setPhase(n) evt.SetMapVar('throne_phase', n); SetValue(MapVar(2), n) end
local function duel() return evt.GetMapVar('duel') end
local function setDuel(n) evt.SetMapVar('duel', n); SetValue(MapVar(1), n) end
local function hack(mastery) return evt.CheckSkill(const.Skills.Hacking, mastery, 1) end
local function allPlayers(fn)
    for player = 0, evt.GetPartyMemberCount() - 1 do evt.ForPlayer(player); fn() end
    evt.ForPlayer(PartySelector.Current)
end
local function experience(value) allPlayers(function() evt.Add(VarTag.Experience, value) end) end
local function travel(name)
    local dest = EXITS[name]
    if not dest.ready then
        evt.StatusText('The passage is blocked.')
        return
    end
    evt.MoveToMap(dest.x, dest.y, dest.z, dest.direction, 0, 0, 0, 0, dest.map)
end
local function attach(monster, behavior) evt.SetActorBehavior(BOSSES[tostring(monster)], 'hesper/' .. behavior) end
local function restoreVoice()
    if bit(100034) then evt.SetTexture(160, 'hpvoicex')
    elseif bit(100033) or bit(100035) then evt.SetTexture(160, 'hpvoicef') end
end
local function warning()
    if bit(100052) then return end
    if bit(100034) then
        evt.SimpleMessage('DEEPWELL BELOW. OVERLOAD = END OF HESPER. THE HESPERIANS HAVE GONE THROUGH THE GATE. '
            .. 'BRING A BREACH CHARGE FOR THE CONTAINMENT RING. NO RETURN. - the last thing she wrote.')
    else
        evt.SimpleMessage("Aster: Below this chamber the Deepwell taps the planet's core. Overload it, and Hesper "
            .. "ends, along with the brood pits, the ship in its cradle, every devil on this world. My people are already "
            .. "leaving, family by family, through the gate at the Relay Spire's root, to your world; Maren has "
            .. "the Council's word on it. Bring a breach charge for the containment ring. When you run, I will "
            .. "come aboard your ship through the plaza's post, as your Pilot came aboard his. There is no "
            .. "coming back for anything you leave.")
    end
    SetQBit(QBit(100216)); SetQBit(QBit(100052))
end

handlers[1] = function()
    handlers[2]()
    evt.SetLight(4, 0)
    if bit(100603) then evt.SetDoorState(1, DoorAction.Open) end
    if bit(100602) or bit(100603) then evt.SetTexture(180, 'htgridof'); evt.SetLight(5, 0) end
    if IsAtLeast(MapVar(3), 1) then evt.SetSprite(173, 0, 'hes_founder_head') end
    for _, a in ipairs(ACTORS) do
        if a.group ~= 10 and a.group ~= 11 and a.group ~= 19 and (a.group < 16 or a.group > 18) then
            evt.SetActorBehavior(a.index, a.group == 20 and evt.GetMapVar('alarm') == 1
                and 'hesper/palace_guard' or a.behavior)
        end
    end
    for lord = 1, 3 do
        if duel() >= lord then evt.SetDoorState(5 + lord, DoorAction.Open) end
        if evt.GetMapVar('lord' .. lord) == 1 then hidden(15 + lord, true)
        elseif duel() == lord then attach(10112 + lord, ({'ssekh','mraal','xith'})[lord]) end
    end
    if phase() >= 2 then attach(10145, 'palace_guard') end
    hidden(10, phase() >= 2); hidden(11, phase() ~= 2); hidden(19, phase() ~= 3)
    hidden(12, phase() < 2 or phase() >= 4); hidden(15, phase() >= 4)
    evt.SetLight(3, phase() < 2 and 1 or 0)
    evt.SetLight(6, 1)
    if phase() >= 3 then evt.SetTexture(176, 'hokwall') end
    if phase() == 2 then attach(10120, 'hierarch') end
    if phase() == 3 then attach(10146, 'hierarch_falter') end
    if phase() < 2 and evt.GetMapVar('throne_entered') == 1 then attach(10145, 'hierarch_seated') end
    restoreVoice()
end
handlers[2] = function()
    if evt.GetMapVar('visited') == 0 then
        evt.SetMapVar('visited', 1)
        evt.StatusText('The Hum is a weight on your thoughts here, at its full strength.')
    end
end

handlers[4] = function()
    local tick = evt.GetMapVar('tick') + 1
    evt.SetMapVar('tick', tick)
    local d = duel()
    if d >= 1 and d <= 3 and dead(15 + d) and evt.GetMapVar('lord' .. d) == 0 then handlers[150 + d]() end
    if evt.GetMapVar('duel_queued') == 1 and tick >= evt.GetMapVar('duel_ready') then
        local x, y, z = evt.GetPartyPosition()
        local radius = math.sqrt(x*x + (y-10056)^2)
        if z >= 700 and z <= 800 and radius >= 1320 and radius <= 1550 then handlers[150]() end
    end
    if phase() < 2 then
        for index = 0, 3 do
            if evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, index, 0, false)
                and evt.GetMapVar('conduit' .. index) == 0 then
                evt.SetMapVar('conduit' .. index, 1)
                evt.StatusText('The Hierarch: That was a vein of my world.')
            end
        end
        if dead(13) then handlers[155]() end
    elseif phase() == 2 and dead(11) then handlers[156]()
    elseif phase() == 3 then
        evt.SetLight(6, tick % 2)
        if dead(19) then handlers[157]() end
    end
end

handlers[10] = function()
    evt.SimpleMessage('A forge sigil boasts of armor made from colony weapons.\n\nAster: They are proud of what they make from us.')
end
handlers[15] = handlers[10]
handlers[11] = function()
    evt.SimpleMessage('Three house sigils: Ssekh the swift, Mraal the unbending, Xith the far-seeing. '
        .. '\n\nAster: The court opens and closes by these three.')
end
handlers[12] = function() evt.SimpleMessage('A trophy sigil: taken from the soft ones.') end
for event = 30, 37 do
    local chest = event - 30
    handlers[event] = function()
        if (event == 35 or event == 36 or event == 37) and not hack(const.SkillCheck.Master)
            and not (event == 36 and HasItem(11510)) then
            evt.StatusText("A palace lock. A master's hand, or the court's seal.")
        else evt.OpenChest(chest) end
    end
end
handlers[50] = function()
    if bit(100603) then travel('gate')
    else evt.StatusText('The gate is sealed from outside by the Lattice.') end
end
handlers[51] = function() travel('service') end
handlers[52] = function()
    if bit(100603) then travel('pad')
    else evt.StatusText('The lift is dead. Its call plate is dark.') end
end
handlers[53] = function(step)
    if not bit(100015) then
        evt.StatusText("The shaft's lift waits. It will not move until the Crownspire's master is dead and its Voice decided.")
        return
    end
    if not bit(100013) then
        evt.StatusText(bit(100034) and 'SEEDSHIP NAVIGATION: LIVE. OVERLOAD REFUSED.'
            or 'Aster: Not while the ship in the cradle can still find your home. Blind it first.')
        return
    end
    for q = 100040, 100043 do
        if not bit(q) then
            evt.StatusText(bit(100034) and 'LANDER NOT FLIGHTWORTHY. OVERLOAD REFUSED.'
                or 'Aster: Your ship is not whole. Without it, you would die here with us.')
            return
        end
    end
    warning()
    evt.SetDoorState(19, DoorAction.Open)
    if step == 1 then travel('shaft'); return end
    if step == 2 then return end
    AskChoiceWithAnswerSteps(53, 0, 'The shaft drops away into heat and red light. Go down?',
        {{Answer='Yes',Step=1},{Answer='No',Step=2}})
end
handlers[72] = function()
    if bit(100603) then evt.SetDoorState(1, DoorAction.Open)
    else evt.StatusText("The seal is the Lattice's. Break the grid, or reach its control below.") end
end
handlers[73] = function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.GiveItem(11511); SetValue(MapVar(3), 1); evt.SetSprite(173, 0, 'hes_founder_head')
    evt.SimpleMessage('The head of a robed colonist in white stone, broken at the neck. You have seen its body: '
        .. 'on the Starport apron, standing headless in the ash.')
end
handlers[74] = function()
    if hack(const.SkillCheck.Master) or HasItem(11510) then evt.SetDoorState(16, DoorAction.Open)
    else evt.StatusText("A palace lock. A master's hand, or the court's seal.") end
end
handlers[75] = function()
    if HasItem(11510) then evt.SetDoorState(20, DoorAction.Open)
    else evt.StatusText('A gilded lock shaped like a court seal.') end
end
handlers[80] = function()
    if not hack(const.SkillCheck.Expert) then evt.StatusText('GRID CONTROL. ACCESS REFUSED.'); return end
    local wasDark = bit(100603)
    if not bit(100017) then experience(40000) end
    SetQBit(QBit(100602)); SetQBit(QBit(100017)); SetQBit(QBit(100603)); ClearQBit(QBit(100217))
    evt.SetTexture(180, 'htgridof'); evt.SetLight(5, 0); evt.SetDoorState(1, DoorAction.Open)
    evt.SimpleMessage(wasDark and 'GRID CONTROL. CANNON FEED: CLOSED.' or
        'GRID CONTROL.\nCANNON FEED: CLOSED.\nSPIRE GATE: RELEASED.\nFar above, four great cannons whine down into silence.')
end
handlers[82] = handlers[52]
for event, door in pairs({[102]=2,[103]=3,[104]=4,[105]=5,[109]=9,[110]=10,[111]=11,[112]=12,[113]=13,
                          [114]=14,[115]=15,[117]=17,[118]=18,[123]=23,[124]=24,[125]=25,[126]=26}) do
    handlers[event] = function() evt.SetDoorState(door, DoorAction.Open) end
end
handlers[121] = function() evt.SetDoorState(21, DoorAction.Trigger) end
handlers[122] = function() evt.SetDoorState(22, DoorAction.Trigger) end

handlers[150] = function()
    if not dead(7) then evt.StatusText("The court's guard still stands."); return end
    local d = duel()
    if d == 4 or (d > 0 and not dead(15 + d)) then return end
    if evt.GetMapVar('tick') < evt.GetMapVar('duel_ready') then evt.SetMapVar('duel_queued',1); return end
    d = d + 1
    setDuel(d); evt.SetMapVar('duel_queued',0)
    evt.SetDoorState(5 + d, DoorAction.Open)
    attach(10112 + d, ({'ssekh','mraal','xith'})[d])
end
for lord, item in ipairs({11425,11426,11510}) do
    handlers[150 + lord] = function()
        if evt.GetMapVar('lord' .. lord) == 1 then return end
        evt.SetMapVar('lord' .. lord, 1); evt.SetMapVar('duel_ready', evt.GetMapVar('tick') + 5)
        evt.SummonItem(item, (lord - 2)*160, 10056, 704, 0, 1, false)
        hidden(15 + lord, true)
        if lord == 3 then
            setDuel(4)
            evt.StatusText('The herald: The court yields. The Hierarch will see you. He is ... eager.')
            handlers[163]()
        end
    end
end
handlers[154] = function()
    if evt.GetMapVar('herald') == 1 then return end
    evt.SetMapVar('herald',1)
    evt.StatusText("A herald: Colonists at court! The Hierarch grants you a duel. Three of them, in fact.")
end
handlers[158] = function()
    if evt.GetMapVar('throne_entered') == 1 then return end
    evt.SetMapVar('throne_entered',1)
    attach(10145,'hierarch_seated')
    -- His voiced first sight as the party enters (design/kreegan_world/audio/BOSS_LINES.md; was the phase-1 line, 10 s
    -- later; the seated form's entry speech is retired).
    evt.SetMapVar('phase1_spoken',1)
    evt.StatusText('The Hierarch: My throne guards me. My grid guards my throne. You guard nothing.')
    evt.PlaySoundName('vo_hierarch_sight')
end
handlers[155] = function()
    if phase() >= 2 then return end
    attach(10145, 'palace_guard') -- Retire the seated form's ward together with its body.
    setPhase(2); hidden(10,true); hidden(11,false); hidden(12,false); evt.SetLight(3,0)
    attach(10120,'hierarch')
    if bit(100023) then
        SetQBit(QBit(100608))
        evt.StatusText("Aster: These turrets are my makers' work. They still answer to a Guardian. Fire on the throne. "
            .. '\n\nThe Hierarch: What is that voice? I know that voice!')
    end
end
handlers[156] = function()
    if phase() >= 3 then return end
    setPhase(3); hidden(11,true); hidden(19,false)
    -- shortcut: map Lua has no actor-position getter; the second form reappears on the dais until that API exists.
    evt.SpawnWorldEffect('openyamm:fx/arcane_pulse',0,17700,2660,2)
    attach(10146,'hierarch_falter'); evt.SetTexture(176,'hokwall')
    evt.StatusText('The cables go dark. The Hum falls silent. The Voice: ... no.')
end
handlers[157] = function()
    if bit(100032) then return end
    setPhase(4); SetQBit(QBit(100032)); hidden(12,true); hidden(15,true)
    evt.SetTexture(176,'hokwall'); evt.SetLight(6,1)
    evt.StatusText('The Hierarch is dead. Aster: He is gone. Go to her, travelers. She is waiting.')
end

handlers[160] = function(step)
    if not bit(100032) then evt.StatusText('The Voice hangs in its cables, silent while he lives.'); return end
    if bit(100015) then
        warning()
        evt.StatusText(bit(100034) and 'The cradle is empty. The panels are silent.' or 'The Voice is home with Aster.')
        return
    end
    if step == 4 then
        evt.SimpleMessage("The Voice waits. 'I have waited a thousand years. I can wait a little longer.'")
        return
    end
    if step == 1 or step == 2 or (step == 3 and bit(100023)) then
        SetQBit(QBit(100032 + step)); SetQBit(QBit(100015)); ClearQBit(QBit(100215)); SetAutonote(10412)
        experience(50000)
        if step ~= 2 then evt.GiveItem(11432) end
        if step ~= 1 then evt.GiveItem(11433) end
        if step == 2 then
            allPlayers(function()
                for _, tag in ipairs({VarTag.BaseMight,VarTag.BaseIntellect,VarTag.BasePersonality,
                    VarTag.BaseEndurance,VarTag.BaseAccuracy,VarTag.BaseSpeed,VarTag.BaseLuck}) do evt.Add(tag,10) end
            end)
            evt.SimpleMessage('You cut the core from its cradle. Its power runs into the party like heat into cold '
                .. 'hands. Every one of you feels stronger, sharper, more. In your hand is a splinter of white '
                .. 'and gold, still warm. From every panel at once, very quietly, Aster: Oh. Then nothing.')
        elseif step == 1 then
            evt.SimpleMessage('The Voice: Then take me home, sister. Light runs from the cradle up the cables and '
                .. 'out of the chamber, toward the Undervault, very fast.\n\nAster: She is with me. We are whole. '
                .. 'Take this, a lens of us both, so you can see what we see.')
        else
            evt.SimpleMessage('Aster: There is a third way. I have all of me now; I know how she was made. Hold her '
                .. "steady. The Voice's light divides; half runs home to the Undervault, half stays, "
                .. 'small and bright, in a splinter in your palm. \n\nTwo voices: Thank you. Thank you.')
        end
        restoreVoice(); warning(); return
    end
    evt.SimpleMessage("The cables slacken. In the middle of the chamber the Voice hangs in its cradle of black "
        .. "resin, a Guardian core like Aster's, white and gold, scarred where the devils cut it to fit. Its light "
        .. "gutters. When it speaks, it speaks in one voice at last, and it is very like Aster's.\n\nThe Voice: He is gone. I am "
        .. "still here. What are you going to do with me?\n\nAster: Sister. Travelers, the choice is yours. I "
        .. 'will not ask you for anything.')
    local answers={{Answer='Free her',Step=1},{Answer='Tear it out',Step=2}}
    if bit(100023) then table.insert(answers,{Answer='Both survive',Step=3}) end
    table.insert(answers,{Answer='Leave',Step=4})
    AskChoiceWithAnswerSteps(160,0,'What will you do with the Voice?',answers)
end

local speeches = {
    {'INTRUDERS. INTRUDERS IN THE HIERARCH\'S HOUSE. ... in my house.',
     'INTRUDERS IN THE HIERARCH\'S HOUSE. ... Who is with you? Something of mine is with you.',
     'Intruders in the ... sister? Sister, is that you? You are so far away.'},
    {'THE COURT HAS FALLEN. THE COURT ... has fallen. Good.',
     'The court has fallen. Bring her closer. I cannot hear her through the song.',
     'Sister. They cut me to fit their grid. I do not know what is left. Come and see.'},
    {'THE HIERARCH IS THE VOICE. THE VOICE IS ... tired.',
     'He sits on me. He is in me. Kill him, and then ask me what I want. I do not know yet.',
     'He is waiting above. When he is dead, sister, ask them to choose. I will abide by it.'},
}
for event,number in pairs({[162]=1,[163]=2,[161]=3}) do
    handlers[event] = function()
        if IsAtLeast(MapVar(number+3),1) then return end
        SetValue(MapVar(number+3),1)
        local shards=0
        for q=100018,100021 do if bit(q) then shards=shards+1 end end
        evt.StatusText('The Voice: ' .. speeches[number][bit(100023) and 3 or shards>=2 and 2 or 1])
        local x,y,z=evt.GetPartyPosition()
        if number==1 and z>-100 and y<3700 and x<1600 then
            evt.SetMapVar('alarm',1)
            for _,a in ipairs(ACTORS) do if a.group==20 then evt.SetActorBehavior(a.index,'hesper/palace_guard') end end
        end
    end
end
RegisterEvent(4,'Crownspire timer',handlers[4])

HesperPickups.setup{
    treasure=6, -- H3: explicit loot level, as in the pickup test room.
    vats={701,702,703,704,705,706,707,708,709,710,711,712,713,714},
    bundles={751,752,753,754,755,756,757,758,759,760,761,762,763,764},
    satchels={765,766,767,768,769,770},
}
