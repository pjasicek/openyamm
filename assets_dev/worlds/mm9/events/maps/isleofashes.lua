-- Isle of Ashes, MM9 rework (level_generation/projects/mm9r_isleofashes/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {BunkerDoor1 = 1, BunkerDoor2 = 2, RotatingDoor8 = 3, Terrain3 = 4}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest1
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- ForadWorld.scr (ScriptObject0, "isleofashes"): key 1024 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- StatStone0 (StatStone: Stat 0 Might, +10 for 3600 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(0, 10, 3600)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 60)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+10 Might for 1 hour")
end
-- Isle of Ashes (regionlua.py): MM9's story scripts as native handlers, each citing its .scr and lines.
local MAP = "isleofashes"
local TICK_SECONDS = 0.25               -- the story tick (event 31000, a game-time timer)
local EFFECT_SCALE = 2.56               -- MM9 effects at the world scale
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local function ticks() return var("Isle.Ticks") end

-- The story's actors (convert.py places them first, from the old import's records), doors, cogs and points.
local YRSA = 12                  -- Yrsa the Troll (YRSA.scr, RUDE 1)
local FORAD = 13                 -- Forad Darre (FORAD.scr, RUDE 2)
local ANNUD = 14                 -- Annud Redeye, ShopkeeperHuman2MaleA0 (HideModel.scr "28 unhide", RUDE 138)
local LICH = 19                  -- LichSummoner (Isle_Summoner.scr "Skeletoid SpawnLocation")
local BONE_THRASHER0 = 15
local BONE_THRASHER1 = 16
local BONE_THRASHER2 = 17
local BONE_THRASHER3 = 18
local STORY_ACTORS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}
local BUNKER_DOOR1, BUNKER_DOOR2 = 1, 2
local HUT_DOOR = 3                -- RotatingDoor8, Yrsa's hut
local ISLET = 4                   -- Terrain3, the islet the cinema sinks (MM9's Door, 1000 LT down)
local FORT_WALL, FORT_WALL0 = 520, 7   -- cogs of their faces (DAT index)
local BOAT = 493                   -- the boat's decoration (SetSprite key: DAT index)
local BOOK = {-963, 5417, 138}
local SPAWN_LOCATION = {9298, 9933, 819}
local MARKER_FROM = {8970, 9646, 679}
local MARKER_TO = {-205, 1823, 630}   -- on the rebuilt shore (on_floor)
local EXPLOSION_EFFECT0 = {9462, 10342, 515}
local EXPLOSION_EFFECT1 = {10117, 9851, 515}
local EXPLOSION_EFFECT2 = {9626, 9687, 515}
local EXPLOSION_EFFECT3 = {10445, 10670, 760}
local EXPLOSION_EFFECT4 = {9953, 10342, 760}
local SHOOTER, SHOOTER_AIM = {-835, 5285, 293}, {1820, 7779, 1945}
local SHOOTER0, FORT_WALL0_AT = {5652, 7209, 2130}, {10122, 10194, 1004}

-- MM9's 'Wait <slot> <seconds> <routine>': a step after so many story ticks (not saved; the explosions only).
local pending = {}
local function after(secondsLater, step)
    table.insert(pending, {at = ticks() + math.max(1, math.floor(secondsLater / TICK_SECONDS + 0.5)), step = step})
end

-- TM_HARDROCK.scr:29-54 (KillControl, ScriptParams "8 27 200"): each OneDown counts; at the 8th key 27,
-- the quest sound and 200 experience. The senders: the flyers whose DeathTriggerTarget is KillControl.
local KILL_CONTROL = 483
local KILL_CONTROL_SENDERS = {[0] = true, [1] = true, [2] = true, [3] = true, [4] = true, [5] = true, [6] = true, [7] = true, [8] = true, [9] = true, [10] = true, [11] = true}
local function killControlOneDown()
    local count = MM9.scrValue(KILL_CONTROL, "count", 0) + 1
    MM9.setScrValue(KILL_CONTROL, "count", count)
    if count == 8 then reward(27, 200, 0) end
end

-- AUTORESURRECT.scr:66-87 Main: the Bone Thrashers wait hidden under the ground (map load, below); :34-46
-- OnResurrect: one rises (shown) on RESURRECT. A dead or removed one takes no message (MM9.receives).
local function resurrect(name, a)
    if MM9.receives(MAP, name, "RESURRECT", a) then show(a, true) end
end

-- ISLE_SUMMONER.scr:47-69 (LichSummoner): each 'spawn' summons a Skeletoid at SpawnLocation with
-- Isle_SpawnCreature.scr; after the fifth the trigger is removed (the sixth still spawns: it counts before).
-- Isle.Skeletoid.<n> holds the n-th summon's actor index + 1, Isle.SkeletoidState.<n> 1 while it runs to
-- MarkerFrom, 2 once it fights, 3 dead. A dead Lich takes no 'spawn' (MM9.receives), and once he is gone
-- (his death, the islet's fall: Isle.LichGone) nothing more comes.
local SKELETOID_ROW = 9183            -- the Skeletoids placed on the isle
local SKELETOID_RUN_SECONDS = 20
local function lichSpawn()
    if not MM9.receives(MAP, "LichSummoner", "spawn", LICH) or var("Isle.LichGone") == 1 then return end
    local counter = var("Isle.SummonCount")
    if counter > 5 then return end
    set("Isle.SummonCount", counter + 1)
    evt.PlayActorClip(LICH, "attack_melee", false)   -- PlayAnim hattack1 (the Lich King's AttackMelee)
    local _, spawned = evt.SummonMonstersById({monster = SKELETOID_ROW, x = SPAWN_LOCATION[1],
        y = SPAWN_LOCATION[2], z = SPAWN_LOCATION[3], radius = 128, count = 1})
    local a = spawned ~= nil and spawned[1] or nil
    if a == nil then return end
    local slot = counter + 1
    set("Isle.Skeletoid." .. slot, a + 1)
    set("Isle.SkeletoidState." .. slot, 1)
    set("Isle.SkeletoidSince." .. slot, ticks())
    -- Isle_SpawnCreature.scr:30-47 InitSpawnCreature: elemental blast and column of fire on it, RunTo MarkerFrom
    local x, y, z = evt.GetMapActorPosition(a)
    if x == nil then x, y, z = SPAWN_LOCATION[1], SPAWN_LOCATION[2], SPAWN_LOCATION[3] end
    evt.SpawnWorldEffect("mm9:elemental_blast", x, y, z, EFFECT_SCALE)
    evt.SpawnWorldEffect("mm9:column_of_fire", x, y, z, EFFECT_SCALE)
    evt.MoveActorTo(a, MARKER_FROM[1], MARKER_FROM[2], MARKER_FROM[3], 0, true)
end
-- Isle_SpawnCreature.scr:60-75 Teleport: at MarkerTo (the mainland's shore) with a column of fire, then BaseInit
-- and BaseWanderStartup (the shared AI). Each tick a running Skeletoid that has arrived (or whose run a reload
-- lost, or that takes too long) teleports; it counts as fighting only once the game has moved it. Saves from
-- before 2026-11-09 hold Skeletoids marked fighting that never left MarkerFrom (MarkerTo over the floor): they
-- teleport too.
local function strandedAtMarkerFrom(a)
    local x, y = evt.GetMapActorPosition(a)
    return x ~= nil and math.abs(x - MARKER_FROM[1]) < 300 and math.abs(y - MARKER_FROM[2]) < 300
end
local function updateSkeletoids()
    for slot = 1, var("Isle.SummonCount") do
        local a = var("Isle.Skeletoid." .. slot) - 1
        local state = var("Isle.SkeletoidState." .. slot)
        local elapsed = (ticks() - var("Isle.SkeletoidSince." .. slot)) * TICK_SECONDS
        if a >= 0 and ((state == 1 and (not evt.IsActorMoving(a) or elapsed >= SKELETOID_RUN_SECONDS))
                or (state == 2 and strandedAtMarkerFrom(a))) then
            evt.StopActorMove(a)
            if evt.SetMapActorPosition(a, MARKER_TO[1], MARKER_TO[2], MARKER_TO[3]) then
                evt.SpawnWorldEffect("mm9:column_of_fire", MARKER_TO[1], MARKER_TO[2], MARKER_TO[3], EFFECT_SCALE)
                set("Isle.SkeletoidState." .. slot, 2)
            end
        end
    end
end
-- Isle_SpawnCreature.scr:49-58 OnDeath: a dead Skeletoid tells LichSummoner to spawn the next.
local function skeletoidKilled(a)
    for slot = 1, var("Isle.SummonCount") do
        if var("Isle.Skeletoid." .. slot) == a + 1 and var("Isle.SkeletoidState." .. slot) ~= 3 then
            set("Isle.SkeletoidState." .. slot, 3)
            lichSpawn()
            return
        end
    end
end
-- TriggerEffects' last message: the Lich is destroyed with the islet.
local function lichDestroyed()
    if not MM9.receives(MAP, "LichSummoner", "destroy", LICH) then return end
    set("Isle.LichGone", 1)
    show(LICH, false)
end

-- ISLE_ISLANDEXPLOSION.scr:28-52 CreateExplosion: five bursts of elemental blast and black smoke 1-2 s apart,
-- then mist (CreateSteam).
local function explode(p, burst)
    burst = burst or 0
    if burst < 5 then
        evt.SpawnWorldEffect("mm9:elemental_blast", p[1], p[2], p[3], EFFECT_SCALE)
        evt.SpawnWorldEffect("mm9:blacksmoke", p[1], p[2], p[3], EFFECT_SCALE)
        after(evt.RandomBetween(4, 8) * TICK_SECONDS, function() explode(p, burst + 1) end)
    else
        evt.SpawnWorldEffect("mm9:mist", p[1], p[2], p[3], EFFECT_SCALE)
    end
end
-- TriggerEffects (DAT 573, FortWall0's DeathTriggerTarget): its messages in order.
local function triggerEffects()
    explode(EXPLOSION_EFFECT0)   -- ExplosionEffect0 (Isle_IslandExplosion.scr)
    explode(EXPLOSION_EFFECT1)   -- ExplosionEffect1 (Isle_IslandExplosion.scr)
    explode(EXPLOSION_EFFECT2)   -- ExplosionEffect2 (Isle_IslandExplosion.scr)
    explode(EXPLOSION_EFFECT3)   -- ExplosionEffect3 (Isle_IslandExplosion.scr)
    explode(EXPLOSION_EFFECT4)   -- ExplosionEffect4 (Isle_IslandExplosion.scr)
    lichDestroyed()
end

-- DestructableBrush 'destroy' (TriggerDestroyOnly): the brush's faces go. FortWall0's death triggers
-- TriggerEffects, once (ShouldMiniSave: Isle.FortWall0Destroyed).
local function removeFaces(cog)
    evt.SetFacetBit(cog, FacetBits.Invisible, 1)
    evt.SetFacetBit(cog, FacetBits.Untouchable, 1)
end
local function fortWallDestroy() removeFaces(FORT_WALL) end
local function fortWall0Destroy()
    if var("Isle.FortWall0Destroyed") == 1 then return end
    set("Isle.FortWall0Destroyed", 1)
    removeFaces(FORT_WALL0)
    triggerEffects()
end

-- Shooter objects (ShootInterval 0: one FireBolt per 'on'): Shooter fires out of the bunker through the broken
-- FortWall along its own aim (5 damage), Shooter0 at the islet's FortWall0 (500).
local function shooterOn()
    evt.FireMissile("Fire", SHOOTER[1], SHOOTER[2], SHOOTER[3], SHOOTER_AIM[1], SHOOTER_AIM[2], SHOOTER_AIM[3], 5,
        "Fire", 0)
    MM9.launchSound("FireBolt", SHOOTER[1], SHOOTER[2], SHOOTER[3])
end
local function shooter0On()
    evt.FireMissile("Fire", SHOOTER0[1], SHOOTER0[2], SHOOTER0[3], FORT_WALL0_AT[1], FORT_WALL0_AT[2],
        FORT_WALL0_AT[3], 500, "Fire", 0)
    MM9.launchSound("FireBolt", SHOOTER0[1], SHOOTER0[2], SHOOTER0[3])
end

-- IS_BOAT.scr:33-44 OnMove: the boat shows and sails to BoatMarker's x at 100 (MoveToPos x, its own height,
-- BoatMarker's z): a glide of its decoration.
local function boatMove()
    evt.SetSprite(BOAT, 1)
    evt.MoveDecoration(BOAT, 4557, 4342, 0, 24.5874)
end

-- IA_ISLAND.scr / Door Terrain3 'open': the islet sinks 1000 LT (its mover: overrides.yml motion dat, 20 s).
local function isletOpen() evt.SetDoorState(ISLET, DoorAction.Open) end

-- ExitTrigger1 'trigger' (DAT 484): it lies 43 000 west at sea, outside this map, so its row of
-- map_transitions.txt runs without the volume: the travel days pass, then the arrival.
local function exitTrigger1()
    evt.AdvanceGameMinutes(4 * 24 * 60)
    evt.MoveToMap(7511, -17581, 247, 1024, 0, 0, 0, 0, "sturmford.blv")
end

-- ISLEASHESBOOK.scr: the cinema. The cinematic book_sinking shows it and runs these steps as its map events at
-- the script's waits; a skip runs the ones still to come at once. Each step runs once (Isle.CinemaStep.<step>),
-- and the done event runs any that has not (a cinematic that could not play), in order.
-- :OnUse 44-50 Gosub DestroyMonsters (81-103): the AIBase within 500 of the book are removed (the story actors;
-- hidden here).
local function destroyMonsters()
    local radius = 1280
    for _, a in ipairs(STORY_ACTORS) do
        local x, y, z = evt.GetMapActorPosition(a)
        if x ~= nil and (x - BOOK[1]) ^ 2 + (y - BOOK[2]) ^ 2 + (z - BOOK[3]) ^ 2 <= radius ^ 2 then
            show(a, false)
        end
    end
end
-- :OnSink 160-186: FortWall0 destroy (its death triggers TriggerEffects), Terrain3 open, Boat move, key 28, 5200
-- experience and the quest sound (eblast03, drown01 and the fire loop are the cinematic's).
local function sink()
    fortWall0Destroy()
    isletOpen()
    boatMove()
    reward(28, 5200, 0)
end
local CINEMA_STEPS = {
    {"monsters", destroyMonsters},       -- :OnUse 44-50
    {"fortWall", fortWallDestroy},       -- :StartDestroy 106-115 (SpawnMgr off: the isle has none)
    {"shooter", shooterOn},              -- :Shoot 119-125
    {"shooter0", shooter0On},            -- :Shoot2 139-146 (ebolt01 is the cinematic's)
    {"sink", sink},                      -- :OnSink 160-186
    {"exit", exitTrigger1},              -- :FadeOut2 218-226 (letterbox and camera3 off: the cinematic's)
}
local function cinemaStep(step)
    local done = "Isle.CinemaStep." .. step[1]
    if var(done) == 0 then
        set(done, 1)
        step[2]()
    end
end
handlers[31010] = function() cinemaStep(CINEMA_STEPS[1]) end   -- monsters
handlers[31011] = function() cinemaStep(CINEMA_STEPS[2]) end   -- fortWall
handlers[31012] = function() cinemaStep(CINEMA_STEPS[3]) end   -- shooter
handlers[31013] = function() cinemaStep(CINEMA_STEPS[4]) end   -- shooter0
handlers[31014] = function() cinemaStep(CINEMA_STEPS[5]) end   -- sink
handlers[31015] = function() cinemaStep(CINEMA_STEPS[6]) end   -- exit
handlers[31019] = function()   -- the cinematic ended (played or skipped)
    for _, step in ipairs(CINEMA_STEPS) do cinemaStep(step) end
end
-- ISLEASHESBOOK.scr:29-54 OnUse: ContainerCheck (58-77: the party stands on the bunker's AI rails; any party at
-- the book does here), then the cinema once Forad has joined (key 29) and before it ran (key 28). A cinematic is
-- never saved half played, so the steps' map vars only guard against a second use while it plays.
local function bookUse()
    if has(29) and not has(28) and var("Isle.CinemaStep.monsters") == 0 then
        evt.PlayCinematic("book_sinking", 31019)
    end
end
handlers[30495] = bookUse   -- Book
-- PROPTRIGGER.scr:24-36 (Prop159, "Book Use"): using the lectern uses the book.
handlers[30496] = bookUse   -- Prop159

-- DOORLOCK.scr:22-48 (BunkerDoor1/2, ScriptParams "568 1"): with the Turret Key (item 568) the doors
-- unlock and the key is taken; they are Sticky (they stay open) and DoubleDoorName opens the pair together.
-- Without the key they stay Locked.
handlers[30498] = function()
    if var("Isle.BunkerOpen") == 1 then return end
    if MM9.hasItem(568, "DOORLOCK.scr:25") ~= 1 then
        evt.StatusText("Locked")
        return
    end
    MM9.takeItem(568, "DOORLOCK.scr:34")
    set("Isle.BunkerOpen", 1)
    evt.SetDoorState(BUNKER_DOOR1, DoorAction.Open)
    evt.SetDoorState(BUNKER_DOOR2, DoorAction.Open)
end
-- RotatingDoor8 (Yrsa's hut door, no script, not locked): a click opens or closes it (MM9 closes it again after
-- CloseWaitTime 5 s; here it stays as the party leaves it).
handlers[30769] = function() evt.SetDoorState(HUT_DOOR, DoorAction.Trigger) end

-- YRSA.scr:74-102 OnUse: key 480; the first time key 365, 800 experience and the quest sound; her voice; then
-- her dialogue (DoRude 1, NPCNbr 1).
handlers[53046] = function()
    MM9.giveKey(480)
    if not has(365) then reward(365, 800, 0) end
    MM9.playSound("voices\\NPC\\NPC_001.wav")
    MM9.openRude(1)
end
-- YRSA.scr:14-70 OnRude: :Key (the Turret Key, item 568, once key 469 is held and the party has none),
-- :dragonfly (key 27: 2000 experience and key 366, once), :Mainline (key 1: 2000 experience and key 367, once).
handlers[50046] = function()
    if MM9.hasItem(568, "YRSA.scr:26") ~= 1 and has(469) then MM9.giveItem(568, "YRSA.scr:33") end
    if not has(366) and has(27) then reward(366, 2000, 0) end
    if not has(367) and has(1) then reward(367, 2000, 0) end
end
-- FORAD.scr:22-41 OnUse: the first time (no key 480) key 480, 800 experience and the quest sound; then his
-- greeting (the DAT's GreetingSound, which MM9's NPC use plays: the script's own Playsound is commented out)
-- and his dialogue (DoRude 2, NPCNbr 2). MM9 has no approach talk here: FORAD.scr's
-- OnFoundPlayer / OnTargetWithinDist 16 Talk is armed only by an Appear message, which only Frosgard City's
-- BattleMan.scr sends.
handlers[53061] = function()
    if not has(480) then reward(480, 800, 0) end
    MM9.playSound("voices/npc/npc_002.wav")
    MM9.openRude(2)
end
-- Annud Redeye (HideModel.scr has no OnUse): MM9's NPC use plays his GreetingSound, then his dialogue.
handlers[53747] = function()
    MM9.playSound("voices/npc/npc_138.wav")
    MM9.openRude(138)
end
-- FORAD.scr:45-86 OnRude: with key 104 (a later chapter's betrayal) he turns hostile instead (OnFoundPlayer off;
-- BaseInit, his fight, is not ported); else :Forad: key 368 and 4000 experience once, and once his hire row
-- gave key 29 he is gone with the party (RemoveObject).
handlers[50061] = function()
    if has(104) then MM9.disableFoundPlayer(61) return end
    if not has(368) then reward(368, 4000, 0) end
    if has(29) then MM9.removeActor(FORAD) end
end

-- Trigger1 (DAT 8): BoneThrasher0 RESURRECT, Trigger1 off.
local function trigger1()
    resurrect("BoneThrasher0", BONE_THRASHER0)
    -- Trigger1 off: it fires once
end
-- Trigger2 (DAT 10): BoneThrasher1 RESURRECT, BoneThrasher2 RESURRECT, BoneThrasher3 RESURRECT, Trigger2 off.
local function trigger2()
    resurrect("BoneThrasher1", BONE_THRASHER1)
    resurrect("BoneThrasher2", BONE_THRASHER2)
    resurrect("BoneThrasher3", BONE_THRASHER3)
    -- Trigger2 off: it fires once
end
-- TriggerStarters (DAT 566): LichSummoner spawn, LichSummoner spawn.
local function triggerStarters()
    lichSpawn()
    lichSpawn()
end
-- DAT Trigger objects the party walks into (PlayerTriggerable; Dims are half extents, reaching 192 over and under), each
-- once (ActivationCount 1: Isle.TriggerCount.<name>).
local PLAYER_TRIGGERS = {
    {name = "Trigger1", fire = trigger1, box = {{-3605, -10425, 376}, {-3113, -9933, 1016}}},
    {name = "Trigger2", fire = trigger2, box = {{-1188, 3748, -74}, {-696, 4240, 566}}},
    {name = "TriggerStarters", fire = triggerStarters, box = {{3154, -3912, 133}, {3810, -3256, 845}}},
}
local function playerTriggers()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(PLAYER_TRIGGERS) do
        local count, b = "Isle.TriggerCount." .. t.name, t.box
        if var(count) == 0 and x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]
                and z >= b[1][3] and z <= b[2][3] then
            set(count, 1)
            t.fire()
        end
    end
end

handlers[31000] = function()   -- the story tick: delayed steps, the triggers, the running Skeletoids
    set("Isle.Ticks", ticks() + 1)
    local now, due = ticks(), {}
    for k = #pending, 1, -1 do
        if pending[k].at <= now then
            table.insert(due, 1, pending[k].step)
            table.remove(pending, k)
        end
    end
    for _, step in ipairs(due) do step() end
    playerTriggers()
    updateSkeletoids()
end

-- Deaths: KillControl's flyers send OneDown (their DeathTriggerTarget); Isle_Summoner.scr OnDeath ends the
-- summons ("give player an incentive to kill the summoner soon"); a summoned Skeletoid's brings the next.
handlers[31003] = function(context)
    local a = context.actorIndex
    if KILL_CONTROL_SENDERS[a] then killControlOneDown() end
    if a == LICH then set("Isle.LichGone", 1) end
    skeletoidKilled(a)
end

-- FORADWORLD.scr:23-36, 135 OnWorldSwitch TakeKey: the location keys go as the party leaves.
handlers[31002] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
end

-- The map load (after ForadWorld.scr's Init, outdoor_blv.py).
handlers.regionLoad = function()
    -- game.cpp (cshell.dll 0x100a6e40) entering worlds\isleofashes: before the cinema (key 28) and the first
    -- time (key 481) it gives key 481 and plays movies\Shipwreck.bik (MM9Shipwreck).
    if not has(28) and not has(481) then
        MM9.giveKey(481)
        evt.ShowMovie("MM9Shipwreck", true)
    end
    -- IS_BOAT.scr:46-51, 64 placed2: the boat stays hidden until it leaves.
    evt.SetSprite(BOAT, 0)
    -- FORAD.scr:96-108, 178-183 DeleteCheck: Forad has joined the party (key 29).
    if has(29) then show(FORAD, false) end
    -- YRSA.scr:106-118, 138-139 Init: Yrsa is gone once Forad has joined (key 29) when the party comes back. MM9
    -- has no saves on the isle, so it never reloads the map between Forad joining and Yrsa giving the Turret Key;
    -- here a reload in that window would hide her and lock the bunker for good. She leaves after the cinema
    -- (key 28) instead.
    if has(29) and has(28) then show(YRSA, false) end
    -- HIDEMODEL.scr:26-34, 55-70 ("28 unhide"): Annud Redeye is there after the cinema.
    show(ANNUD, has(28))
    -- AUTORESURRECT.scr:66-80: the Bone Thrashers wait under the ground until their trigger has fired.
    if var("Isle.TriggerCount.Trigger1") == 0 then show(BONE_THRASHER0, false) end
    if var("Isle.TriggerCount.Trigger2") == 0 then show(BONE_THRASHER1, false); show(BONE_THRASHER2, false); show(BONE_THRASHER3, false) end
    -- Saves from before the cinematic (2026-11-06) could hold the old timed cinema half played: it starts over.
    if evt.GetMapVar("Isle.CinemaStart", -1) >= 0 and not has(28) then
        set("Isle.CinemaStart", -1)
        for _, step in ipairs(CINEMA_STEPS) do set("Isle.CinemaStep." .. step[1], 0) end
    end
    -- ISLEASHESBOOK.scr:230-243 Init: after the cinema (key 28) FortWall0 is gone and the islet sunk (Terrain3
    -- sinkspeed, open); the Lich went with it (FortWall0 is ShouldMiniSave: its death trigger does not fire again).
    if has(28) then
        removeFaces(FORT_WALL0)
        isletOpen()
        set("Isle.FortWall0Destroyed", 1)
        set("Isle.LichGone", 1)
        show(LICH, false)
    end
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1024)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's exploding destructibles (Exploding 1): breaking deals ExplodeDamage within DamageRadius of its
-- centre to the party and to the other exploding destructibles there (the next of a chain breaks then).
local EXPLODING = {[7] = {{10122, 10194, 1004}, 512, 100}, [520] = {{-655, 5407, 471}, 512, 100}}
local function explode(id)
    local e = EXPLODING[id]
    local c, r = e[1], e[2]
    evt.SpawnWorldEffect("mm9:column_of_fire", c[1], c[2], c[3], 0.6)
    local x, y, z = evt.GetPartyPosition()
    local dz = math.max(0, c[3] - (z + 170), z - c[3])
    if (x - c[1]) ^ 2 + (y - c[2]) ^ 2 + dz ^ 2 <= r * r then
        evt.DamagePlayer(Players.All, const.Damage.Fire, e[3])
    end
    for other, o in pairs(EXPLODING) do
        local q = o[1]
        if other ~= id and (q[1] - c[1]) ^ 2 + (q[2] - c[2]) ^ 2 + (q[3] - c[3]) ^ 2 <= r * r then
            evt.DamageDestructible(other, e[3])
        end
    end
end
-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30007] = function() explode(7) end   -- FortWall0
handlers[30520] = function() explode(520) end   -- FortWall

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23551] = 1, [23552] = 1, [23553] = 1}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
end

RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(31010, "Isle cinema: monsters", handlers[31010])
RegisterEvent(31011, "Isle cinema: fortWall", handlers[31011])
RegisterEvent(31012, "Isle cinema: shooter", handlers[31012])
RegisterEvent(31013, "Isle cinema: shooter0", handlers[31013])
RegisterEvent(31014, "Isle cinema: sink", handlers[31014])
RegisterEvent(31015, "Isle cinema: exit", handlers[31015])
RegisterEvent(31019, "Isle cinema: done", handlers[31019])
RegisterEvent(30495, "Book", handlers[30495], "Read")
RegisterEvent(30496, "Lectern", handlers[30496], "Read")
RegisterEvent(30498, "BunkerDoor1", handlers[30498], "Open")
RegisterEvent(30769, "RotatingDoor8", handlers[30769], "Open")
RegisterEvent(53046, "Yrsa", handlers[53046])
RegisterEvent(50046, "Yrsa: dialogue exit", handlers[50046])
RegisterEvent(53061, "Forad Darre", handlers[53061])
RegisterEvent(50061, "Forad Darre: dialogue exit", handlers[50061])
RegisterEvent(53747, "Annud Redeye", handlers[53747])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30007, "FortWall0", handlers[30007])
RegisterEvent(30520, "FortWall", handlers[30520])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
SetMapContextAction(30498, {kind = "open_door", source = "mm9_mechanism", targetName = "BunkerDoor1"})
SetMapContextAction(30769, {kind = "open_door", source = "mm9_mechanism", targetName = "RotatingDoor8"})
RegisterMapTimerEvent(31000, seconds(TICK_SECONDS), handlers[31000], "Isle of Ashes story")
RegisterMonsterKilledHook(31003, "Isle of Ashes deaths", handlers[31003])
RegisterMapOnLeaveEvent(31002, "Isle of Ashes location keys", handlers[31002])
