-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPCSHOPKEEPER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "BaseWander.inc" }

-- shopkeeper.scr
-- timmy
-- handles shopkeeper voice and anims
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnUse"] = function(ctx)
    -- NPCSHOPKEEPER.scr:22
    ctx:playSound("sound", "Onexit", 100, 240, "FALSE", 100) -- NPCSHOPKEEPER.scr:25
    do return ctx:exit("") end -- NPCSHOPKEEPER.scr:26
end

script.labels["OnExit"] = function(ctx)
    -- NPCSHOPKEEPER.scr:29
    do return ctx:exit("") end -- NPCSHOPKEEPER.scr:32
end

script.labels["Main"] = function(ctx)
    -- NPCSHOPKEEPER.scr:35
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- NPCSHOPKEEPER.scr:41
    ctx:getParam(1, "Params") -- NPCSHOPKEEPER.scr:42
    ctx:getParam(2, "g_ntemp") -- NPCSHOPKEEPER.scr:43
    ctx:self():loopAnimation("Params", "g_ntemp", "DoNothing") -- NPCSHOPKEEPER.scr:44
    ctx:addTrigger("Use", "OnUse") -- NPCSHOPKEEPER.scr:47
    -- jsl-->Wander if we're setup to..
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPCSHOPKEEPER.scr:50
    do return ctx:exit("") end -- NPCSHOPKEEPER.scr:52
end

return script
