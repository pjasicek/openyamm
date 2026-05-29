-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MARYSHEEP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "followplayer.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basewander.inc" }

-- NPC309.scr
-- timmy
-- handles mary sheepherder voice and quest stuff
script.labels["OnUse"] = function(ctx)
    -- MARYSHEEP.scr:14
    ctx:getParam(0, "g_htarget") -- MARYSHEEP.scr:17
    ctx:self():faceObject(ctx:object("g_htarget"), 200, "DoNothing") -- MARYSHEEP.scr:18
    mm9.gosub(script, ctx, "FollowInit") -- MARYSHEEP.scr:20
    mm9.gosub(script, ctx, "FollowOnUse") -- MARYSHEEP.scr:21
    ctx:object("CommonerChildHuman2ChildA0"):trigger("Target") -- MARYSHEEP.scr:22-23
    do return ctx:exit("") end -- MARYSHEEP.scr:25
end

script.labels["OnRun"] = function(ctx)
    -- MARYSHEEP.scr:28
    ctx:getParam(0, "g_htarget") -- MARYSHEEP.scr:31
    ctx:self():stop() -- MARYSHEEP.scr:32
    mm9.gosub(script, ctx, "followstop") -- MARYSHEEP.scr:33
    ctx:self():runTo(ctx:object("g_htarget"), 16, "OnArrive") -- MARYSHEEP.scr:34
    do return ctx:exit("") end -- MARYSHEEP.scr:35
end

script.labels["OnArrive"] = function(ctx)
    -- MARYSHEEP.scr:38
    ctx:runScript("Cat.scr") -- MARYSHEEP.scr:41
    do return ctx:exit("") end -- MARYSHEEP.scr:42
end

script.labels["Main"] = function(ctx)
    -- MARYSHEEP.scr:45
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("RuntoMe", "OnRun") -- MARYSHEEP.scr:52
    ctx:addTrigger("Use", "OnUse") -- MARYSHEEP.scr:53
    do return ctx:exit("") end -- MARYSHEEP.scr:55
end

return script
