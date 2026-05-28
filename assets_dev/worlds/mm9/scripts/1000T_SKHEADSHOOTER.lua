-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_SKHEADSHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- 1000t_SkHeadShooter.scr
-- Karl Drown
-- 11-29-01
-- Shoot fireballs from the eye sockets
-- of the Skullhead
script.labels["StartShooting"] = function(ctx)
    -- 1000T_SKHEADSHOOTER.scr:21
    -- Cprint StartShooting
    ctx:command("target", "hTarget") -- 1000T_SKHEADSHOOTER.scr:24
    mm9.gosub(script, ctx, "Fire") -- 1000T_SKHEADSHOOTER.scr:25
    do return ctx:exit("TRUE") end -- 1000T_SKHEADSHOOTER.scr:26
end

script.labels["Fire"] = function(ctx)
    -- 1000T_SKHEADSHOOTER.scr:29
    -- Cprint Fire
    if ctx:condition("nCount<=0") then -- 1000T_SKHEADSHOOTER.scr:32
        mm9.gosub(script, ctx, "StopShooting") -- 1000T_SKHEADSHOOTER.scr:33
        do return ctx:exit("") end -- 1000T_SKHEADSHOOTER.scr:34
    end -- 1000T_SKHEADSHOOTER.scr:35
    ctx:command("ncount", "= nCount - 1") -- 1000T_SKHEADSHOOTER.scr:36
    ctx:trigger("hMe", "On") -- 1000T_SKHEADSHOOTER.scr:37
    ctx:command("wait", "0, 1, Fire") -- 1000T_SKHEADSHOOTER.scr:39
    do return ctx:exit("TRUE") end -- 1000T_SKHEADSHOOTER.scr:41
end

script.labels["StopShooting"] = function(ctx)
    -- 1000T_SKHEADSHOOTER.scr:43
    -- Cprint StopShooting
    ctx:trigger("hMe", "Off") -- 1000T_SKHEADSHOOTER.scr:46
    ctx:command("target", "NULL") -- 1000T_SKHEADSHOOTER.scr:47
    do return ctx:exit("TRUE") end -- 1000T_SKHEADSHOOTER.scr:48
end

script.labels["Main2"] = function(ctx)
    -- 1000T_SKHEADSHOOTER.scr:50
    ctx:addTrigger("Go", "StartShooting") -- 1000T_SKHEADSHOOTER.scr:52
    ctx:command("getmyhandle", "hMe") -- 1000T_SKHEADSHOOTER.scr:53
    ctx:command("getobjecthandle", "sTarget, hTarget") -- 1000T_SKHEADSHOOTER.scr:54
    do return ctx:exit("TRUE") end -- 1000T_SKHEADSHOOTER.scr:55
end

script.labels["Main"] = function(ctx)
    -- 1000T_SKHEADSHOOTER.scr:58
    ctx:getParam(0, "sTarget") -- 1000T_SKHEADSHOOTER.scr:60
    ctx:getParam(1, "nCount") -- 1000T_SKHEADSHOOTER.scr:61
    ctx:command("wait", "0, 1, Main2") -- 1000T_SKHEADSHOOTER.scr:62
    do return ctx:exit("TRUE") end -- 1000T_SKHEADSHOOTER.scr:64
end

return script
