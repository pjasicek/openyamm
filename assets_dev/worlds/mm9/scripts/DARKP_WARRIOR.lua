-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_WARRIOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "BaseMelee.inc" }

-- DarkP_Warrior.scr
-- kd
-- 11-11-01
-- ColloidialWarrior deals final blow
-- to NPCAdventurer
script.labels["Stop"] = function(ctx)
    -- DARKP_WARRIOR.scr:18
    ctx:trigger("hNpc", "Destroy") -- DARKP_WARRIOR.scr:20
    ctx:command("getplayerhandle", "hPlayer, 3000") -- DARKP_WARRIOR.scr:21
    ctx:command("runto", "hPlayer, 50, BaseInit") -- DARKP_WARRIOR.scr:22
    mm9.gosub(script, ctx, "BaseInit") -- DARKP_WARRIOR.scr:23
    do return ctx:exit("TRUE") end -- DARKP_WARRIOR.scr:24
end

script.labels["BeginSequence"] = function(ctx)
    -- DARKP_WARRIOR.scr:26
    ctx:command("playanim", "Hattack1, AnimateC") -- DARKP_WARRIOR.scr:28
    do return ctx:exit("TRUE") end -- DARKP_WARRIOR.scr:29
end

script.labels["AnimateC"] = function(ctx)
    -- DARKP_WARRIOR.scr:31
    ctx:trigger("hNpc", "Wince") -- DARKP_WARRIOR.scr:33
    ctx:command("playanim", "Hattack2, Stop") -- DARKP_WARRIOR.scr:34
    do return ctx:exit("TRUE") end -- DARKP_WARRIOR.scr:35
end

script.labels["Main2"] = function(ctx)
    -- DARKP_WARRIOR.scr:37
    ctx:command("getobjecthandle", "NPCAdventurer0, hNpc") -- DARKP_WARRIOR.scr:39
    ctx:addTrigger("HitNpc", "BeginSequence") -- DARKP_WARRIOR.scr:40
    do return ctx:exit("TRUE") end -- DARKP_WARRIOR.scr:41
end

script.labels["Main"] = function(ctx)
    -- DARKP_WARRIOR.scr:43
    ctx:command("wait", "0, 0.1, Main2") -- DARKP_WARRIOR.scr:45
    do return ctx:exit("TRUE") end -- DARKP_WARRIOR.scr:46
end

return script
