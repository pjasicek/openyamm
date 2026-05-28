-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAMCAMEO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "njam1000.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basewander.inc" }

-- NjamCameo.scr
-- By Timmy
-- 11/16
-- Manager for Njam's cameos
-- #include basemelee.inc
-- flag variables
script.labels["ShouldRunAway"] = function(ctx)
    -- NJAMCAMEO.scr:23
    do return ctx:exit("") end -- NJAMCAMEO.scr:26
end

script.labels["OnDamage"] = function(ctx)
    -- NJAMCAMEO.scr:29
    ctx:getParam(0, "g_htarget") -- NJAMCAMEO.scr:32
    ctx:command("target", "g_htarget") -- NJAMCAMEO.scr:33
    mm9.gosub(script, ctx, "vanish") -- NJAMCAMEO.scr:34
    -- gosub Ondamage, 1
    do return ctx:exit("") end -- NJAMCAMEO.scr:36
end

script.labels["Main"] = function(ctx)
    -- NJAMCAMEO.scr:39
    -- delete me!!
    ctx:command("traceon", "") -- NJAMCAMEO.scr:42
    mm9.gosub(script, ctx, "Init") -- NJAMCAMEO.scr:44
    mm9.gosub(script, ctx, "BasewanderInit") -- NJAMCAMEO.scr:45
    mm9.gosub(script, ctx, "BaseWanderForceStartUp") -- NJAMCAMEO.scr:46
    ctx:command("ondamage", "OnDamage") -- NJAMCAMEO.scr:47
    ctx:addTrigger("Use", "OnDamage") -- NJAMCAMEO.scr:48
    ctx:command("ontouchnotify", "OnDamage") -- NJAMCAMEO.scr:49
    do return ctx:exit("") end -- NJAMCAMEO.scr:50
end

return script
