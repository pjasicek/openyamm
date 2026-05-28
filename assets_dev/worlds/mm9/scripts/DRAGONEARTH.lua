-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONEARTH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "base.inc" }

-- dragonearth.scr
-- Jeff Leggett
-- Implementation of the earth dragon...
script.labels["DragonAwake"] = function(ctx)
    -- DRAGONEARTH.scr:13
    -- Now we're awake, go get him...
    ctx:command("target", "g_hTarget, TRUE") -- DRAGONEARTH.scr:18
    ctx:command("onfoundplayer", "BaseFoundPlayer") -- DRAGONEARTH.scr:20
    ctx:command("onattackready", "BaseAttackReady") -- DRAGONEARTH.scr:21
    ctx:command("ondamage", "BaseDamage") -- DRAGONEARTH.scr:22
    ctx:command("set", "g_sTemp, g_hTarget") -- DRAGONEARTH.scr:24
    ctx:command("setparam", "0, g_sTemp") -- DRAGONEARTH.scr:26
    mm9.gosub(script, ctx, "BaseFoundPlayer") -- DRAGONEARTH.scr:28
    do return ctx:exit("") end -- DRAGONEARTH.scr:30
end

script.labels["WakeUp"] = function(ctx)
    -- DRAGONEARTH.scr:33
    -- Wake up and go get 'em boy!
    ctx:getParam(0, "g_hTarget") -- DRAGONEARTH.scr:39
    if ctx:condition("g_hTarget==NULL") then -- DRAGONEARTH.scr:41
        do return ctx:exit("FALSE") end -- DRAGONEARTH.scr:42
    end -- DRAGONEARTH.scr:43
    ctx:command("onfoundplayer", "") -- DRAGONEARTH.scr:45
    ctx:command("onattackready", "") -- DRAGONEARTH.scr:46
    ctx:command("ondamage", "") -- DRAGONEARTH.scr:47
    ctx:command("target", "g_hTarget, TRUE") -- DRAGONEARTH.scr:49
    ctx:command("onattackready", "") -- DRAGONEARTH.scr:51
    ctx:command("onfoundplayer", "") -- DRAGONEARTH.scr:52
    ctx:command("playanim", "StandUp, DragonAwake") -- DRAGONEARTH.scr:54
    do return ctx:exit("TRUE") end -- DRAGONEARTH.scr:56
end

script.labels["SetupSleeping"] = function(ctx)
    -- DRAGONEARTH.scr:59
    -- Setup the dragon as asleep....
    -- Loop our sleeping animation
    ctx:command("loopanim", "Rest,0") -- DRAGONEARTH.scr:66
    -- When we find the player, we'll need to wake up...
    ctx:command("onfoundplayer", "WakeUp") -- DRAGONEARTH.scr:69
    ctx:command("onattackready", "WakeUp") -- DRAGONEARTH.scr:70
    ctx:command("ondamage", "WakeUp") -- DRAGONEARTH.scr:71
    do return ctx:exit("") end -- DRAGONEARTH.scr:74
end

script.labels["OnCongestion"] = function(ctx)
    -- DRAGONEARTH.scr:77
    -- Don't do anything here...
    do return ctx:exit("FALSE") end -- DRAGONEARTH.scr:83
end

script.labels["Main"] = function(ctx)
    -- DRAGONEARTH.scr:86
    -- Parameters:
    -- p0 ==> bIsSleeping
    mm9.gosub(script, ctx, "InitBase") -- DRAGONEARTH.scr:94
    -- TraceOn
    ctx:getParam(0, "g_nTemp") -- DRAGONEARTH.scr:98
    if ctx:condition("g_nTemp!=FALSE") then -- DRAGONEARTH.scr:100
        mm9.gosub(script, ctx, "SetupSleeping") -- DRAGONEARTH.scr:101
    end -- DRAGONEARTH.scr:102
    ctx:command("oncongestion", "OnCongestion") -- DRAGONEARTH.scr:104
    do return ctx:exit("") end -- DRAGONEARTH.scr:106
end

return script
