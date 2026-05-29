-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC240.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- shopkeeper.scr
-- timmy
-- handles shopkeeper voice and anims
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["Off"] = function(ctx)
    -- NPC240.scr:18
    ctx:debugOut("Done!!") -- NPC240.scr:22
    do return ctx:exit("") end -- NPC240.scr:23
end

-- Delete this when the script works the way it's supposed to!!!
script.labels["OnUse"] = function(ctx)
    -- NPC240.scr:28
    ctx:playSound("\\voices\\npc\\NPC_240.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC240.scr:31
    do return ctx:exit("") end -- NPC240.scr:32
end

script.labels["OnExit"] = function(ctx)
    -- NPC240.scr:35
    do return ctx:exit("") end -- NPC240.scr:38
end

script.labels["Main"] = function(ctx)
    -- NPC240.scr:41
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- NPC240.scr:47
    ctx:getParam(1, "Params") -- NPC240.scr:48
    ctx:getParam(2, "g_ntemp") -- NPC240.scr:49
    ctx:self():loopAnimation("Params", "g_ntemp", "Off") -- NPC240.scr:50
    ctx:addTrigger("Use", "OnUse") -- NPC240.scr:53
    do return ctx:exit("") end -- NPC240.scr:55
end

return script
