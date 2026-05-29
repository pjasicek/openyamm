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
    ctx:state().hBansheeObjectA = ctx:objectOrNil("CanyonDoorL0") -- DARKP_CANYONSWITCH.scr:20
    ctx:state().hBansheeObjectB = ctx:objectOrNil("CanyonDoorR0") -- DARKP_CANYONSWITCH.scr:21
    ctx:trigger("hBansheeObjectA", "Unlock") -- DARKP_CANYONSWITCH.scr:22
    ctx:trigger("hBansheeObjectB", "Unlock") -- DARKP_CANYONSWITCH.scr:23
    ctx:trigger("hBansheeObjectA", "Use") -- DARKP_CANYONSWITCH.scr:24
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:25
end

script.labels["Stop"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:27
    ctx:state().hBansheeObjectA = ctx:objectOrNil("BansheeAEye4") -- DARKP_CANYONSWITCH.scr:29
    ctx:state().hBansheeObjectB = ctx:objectOrNil("BansheeAEye5") -- DARKP_CANYONSWITCH.scr:30
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:31
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:32
    ctx:cprint("hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:33
    ctx:cprint("hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:34
    ctx:self():stop() -- DARKP_CANYONSWITCH.scr:35
    ctx:removeTrigger("Use") -- DARKP_CANYONSWITCH.scr:36
    mm9.gosub(script, ctx, "CanyonDoors") -- DARKP_CANYONSWITCH.scr:37
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:40
    ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_CANYONSWITCH.scr:42
    ctx:self():playAnimation("Hattack2", "AnimateA") -- DARKP_CANYONSWITCH.scr:43
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:44
end

script.labels["AnimateA"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:46
    ctx:state().hBansheeObjectA = ctx:objectOrNil("BansheeAEye0") -- DARKP_CANYONSWITCH.scr:48
    ctx:state().hBansheeObjectB = ctx:objectOrNil("BansheeAEye1") -- DARKP_CANYONSWITCH.scr:49
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:50
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:51
    ctx:cprint("hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:52
    ctx:cprint("hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:53
    ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_CANYONSWITCH.scr:54
    ctx:self():playAnimation("Taunt", "AnimateB") -- DARKP_CANYONSWITCH.scr:55
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:56
end

script.labels["AnimateB"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:59
    ctx:state().hBansheeObjectA = ctx:objectOrNil("BansheeAEye2") -- DARKP_CANYONSWITCH.scr:61
    ctx:state().hBansheeObjectB = ctx:objectOrNil("BansheeAEye3") -- DARKP_CANYONSWITCH.scr:62
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:63
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:64
    ctx:cprint("hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:65
    ctx:cprint("hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:66
    ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_CANYONSWITCH.scr:67
    ctx:self():playAnimation("Rattack1", "AnimateC") -- DARKP_CANYONSWITCH.scr:68
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:69
end

script.labels["AnimateC"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:71
    ctx:state().hBansheeObjectA = ctx:objectOrNil("BansheeAEye6") -- DARKP_CANYONSWITCH.scr:73
    ctx:state().hBansheeObjectB = ctx:objectOrNil("BansheeAEye7") -- DARKP_CANYONSWITCH.scr:74
    ctx:trigger("hBansheeObjectA", "On") -- DARKP_CANYONSWITCH.scr:75
    ctx:trigger("hBansheeObjectB", "On") -- DARKP_CANYONSWITCH.scr:76
    ctx:cprint("hBansheeObjectA") -- DARKP_CANYONSWITCH.scr:77
    ctx:cprint("hBansheeObjectB") -- DARKP_CANYONSWITCH.scr:78
    ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_CANYONSWITCH.scr:79
    ctx:self():playAnimation("Fidget1", "Stop") -- DARKP_CANYONSWITCH.scr:80
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:81
end

script.labels["Main2"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:83
    ctx:addTrigger("Use", "OnUse") -- DARKP_CANYONSWITCH.scr:86
    ctx:self():playAnimation("CastSpell", "DoNothing") -- DARKP_CANYONSWITCH.scr:87
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:88
end

script.labels["Main"] = function(ctx)
    -- DARKP_CANYONSWITCH.scr:90
    ctx:wait(0, 0.1, "Main2") -- DARKP_CANYONSWITCH.scr:93
    do return ctx:exit("TRUE") end -- DARKP_CANYONSWITCH.scr:94
end

return script
