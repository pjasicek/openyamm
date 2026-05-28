-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_CANYONSWITCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "Globals.inc" }

-- DarkP_CanyonSwitch.scr
-- kd
-- 11-6-01
-- Not sure what this can do
script.labels["CanyonDoors"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:18
    ctx:command("getobjecthandle", "CanyonDoorL0, hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:20
    ctx:command("getobjecthandle", "CanyonDoorR0, hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:21
    ctx:trigger("hBansheeObjectA", "Unlock") -- DARKP_CANYONSWITCH.scr:22
    ctx:trigger("hBansheeObjectB", "Unlock") -- DARKP_CANYONSWITCH.scr:23
    ctx:trigger("hBansheeObjectA", "Use") -- DARKP_CANYONSWITCH.scr:24
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:25
end

script.labels["Stop"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:27
    ctx:command("getobjecthandle", "BansheeAEye4, hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:29
    ctx:command("getobjecthandle", "BansheeAEye5, hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:30
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:31
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:32
    ctx:command("cprint", "hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:33
    ctx:command("cprint", "hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:34
    ctx:command("stop", "") -- DARKP_CANYONSWITCH.scr:35
    ctx:command("removetrigger", "Use") -- DARKP_CANYONSWITCH.scr:36
    mm9.gosub(script, ctx, "CanyonDoors") -- DARKP_CANYONSWITCH.scr:37
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:40
    ctx:command("playsound", "Sounds\\spells\\EnchantItem.wav DoNothing 500 1000 FALSE 100") -- DARKP_CANYONSWITCH.scr:42
    ctx:command("playanim", "Hattack2, AnimateA") -- DARKP_CANYONSWITCH.scr:43
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:44
end

script.labels["AnimateA"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:46
    ctx:command("getobjecthandle", "BansheeAEye0, hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:48
    ctx:command("getobjecthandle", "BansheeAEye1, hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:49
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:50
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:51
    ctx:command("cprint", "hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:52
    ctx:command("cprint", "hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:53
    ctx:command("playsound", "Sounds\\spells\\EnchantItem.wav DoNothing 500 1000 FALSE 100") -- DARKP_CANYONSWITCH.scr:54
    ctx:command("playanim", "Taunt, AnimateB") -- DARKP_CANYONSWITCH.scr:55
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:56
end

script.labels["AnimateB"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:59
    ctx:command("getobjecthandle", "BansheeAEye2, hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:61
    ctx:command("getobjecthandle", "BansheeAEye3, hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:62
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:63
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:64
    ctx:command("cprint", "hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:65
    ctx:command("cprint", "hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:66
    ctx:command("playsound", "Sounds\\spells\\EnchantItem.wav DoNothing 500 1000 FALSE 100") -- DARKP_CANYONSWITCH.scr:67
    ctx:command("playanim", "Rattack1, AnimateC") -- DARKP_CANYONSWITCH.scr:68
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:69
end

script.labels["AnimateC"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:71
    ctx:command("getobjecthandle", "BansheeAEye6, hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:73
    ctx:command("getobjecthandle", "BansheeAEye7, hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:74
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:75
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:76
    ctx:command("cprint", "hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:77
    ctx:command("cprint", "hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:78
    ctx:command("playsound", "Sounds\\spells\\EnchantItem.wav DoNothing 500 1000 FALSE 100") -- DARKP_CANYONSWITCH.scr:79
    ctx:command("playanim", "Fidget1, Stop") -- DARKP_CANYONSWITCH.scr:80
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:81
end

script.labels["Main2"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:83
    ctx:addTrigger("Use", "OnUse") -- DARKP_CANYONSWITCH.scr:86
    ctx:command("playanim", "CastSpell, DoNothing") -- DARKP_CANYONSWITCH.scr:87
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:88
end

script.labels["Main"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:90
    ctx:command("wait", "0, 0.1, Main2") -- DARKP_CANYONSWITCH.scr:93
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:94
end

return script
