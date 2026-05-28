-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_LIGHTNINGSHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- 1000t_LightningShooter.scr
-- Karl Drown 12-1-01
-- Shoot bolts of lightning at a marker
-- P0 = MarkerTarget
script.labels["TurnOff"] = function(ctx)
    -- 1000T_LIGHTNINGSHOOTER.scr:21
    ctx:command("target", "NULL") -- 1000T_LIGHTNINGSHOOTER.scr:24
    ctx:trigger("hMe", "Off") -- 1000T_LIGHTNINGSHOOTER.scr:25
    do return ctx:exit("TRUE") end -- 1000T_LIGHTNINGSHOOTER.scr:27
end

script.labels["StartShooting"] = function(ctx)
    -- 1000T_LIGHTNINGSHOOTER.scr:29
    ctx:command("target", "hMarker, TRUE") -- 1000T_LIGHTNINGSHOOTER.scr:32
    ctx:trigger("hMe", "On") -- 1000T_LIGHTNINGSHOOTER.scr:33
    do return ctx:exit("TRUE") end -- 1000T_LIGHTNINGSHOOTER.scr:35
end

script.labels["Main2"] = function(ctx)
    -- 1000T_LIGHTNINGSHOOTER.scr:37
    ctx:addTrigger("Go", "StartShooting") -- 1000T_LIGHTNINGSHOOTER.scr:39
    ctx:addTrigger("Stop", "TurnOff") -- 1000T_LIGHTNINGSHOOTER.scr:40
    ctx:command("getobjecthandle", "sMarker, hMarker") -- 1000T_LIGHTNINGSHOOTER.scr:41
    ctx:command("getmyhandle", "hMe") -- 1000T_LIGHTNINGSHOOTER.scr:42
    do return ctx:exit("True") end -- 1000T_LIGHTNINGSHOOTER.scr:43
end

script.labels["Main"] = function(ctx)
    -- 1000T_LIGHTNINGSHOOTER.scr:45
    ctx:getParam(0, "sMarker") -- 1000T_LIGHTNINGSHOOTER.scr:47
    ctx:command("wait", "0, 0.5, Main2") -- 1000T_LIGHTNINGSHOOTER.scr:48
    do return ctx:exit("") end -- 1000T_LIGHTNINGSHOOTER.scr:49
end

return script
