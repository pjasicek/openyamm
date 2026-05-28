-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FARMANIMAL.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseWander.Inc" }
script.includes[#script.includes + 1] = { line = 11, path = "BaseRun.Inc" }

-- FarmAnimal.Inc
-- Jeff Leggett
-- Just wander around.
-- If damaged, run away...
script.labels["FarmInitWander"] = function(ctx)
    -- FARMANIMAL.inc:15
    mm9.gosub(script, ctx, "BaseWanderInit") -- FARMANIMAL.inc:17
    do return ctx:exit("") end -- FARMANIMAL.inc:19
end

script.labels["EnableWandering"] = function(ctx)
    -- FARMANIMAL.inc:22
    mm9.gosub(script, ctx, "BaseWanderStart") -- FARMANIMAL.inc:24
    do return ctx:exit("") end -- FARMANIMAL.inc:25
end

script.labels["DisableWandering"] = function(ctx)
    -- FARMANIMAL.inc:28
    mm9.gosub(script, ctx, "BaseWanderStop") -- FARMANIMAL.inc:30
    do return ctx:exit("") end -- FARMANIMAL.inc:31
end

script.labels["OnDamage"] = function(ctx)
    -- FARMANIMAL.inc:34
    if ctx:condition("g_hTarget!=NULL") then -- FARMANIMAL.inc:37
        do return ctx:exit("FALSE") end -- FARMANIMAL.inc:38
    end -- FARMANIMAL.inc:39
    ctx:getParam(0, "g_hTarget") -- FARMANIMAL.inc:41
    ctx:command("target", "g_hTarget, FALSE") -- FARMANIMAL.inc:42
    do return ctx:exit("FALSE") end -- FARMANIMAL.inc:44
end

script.labels["BaseRunCancel"] = function(ctx)
    -- FARMANIMAL.inc:47
    mm9.gosub(script, ctx, "BaseRunCancel") -- FARMANIMAL.inc:49
    ctx:command("target", "NULL") -- FARMANIMAL.inc:51
    ctx:command("g_htarget", "= NULL") -- FARMANIMAL.inc:52
    ctx:command("stop", "") -- FARMANIMAL.inc:54
    mm9.gosub(script, ctx, "EnableWandering") -- FARMANIMAL.inc:55
    do return ctx:exit("") end -- FARMANIMAL.inc:57
end

script.labels["BaseRunAway"] = function(ctx)
    -- FARMANIMAL.inc:60
    mm9.gosub(script, ctx, "DisableWandering") -- FARMANIMAL.inc:63
    mm9.gosub(script, ctx, "BaseRunAway") -- FARMANIMAL.inc:64
    do return ctx:exit("") end -- FARMANIMAL.inc:66
end

script.labels["OnDamageDone"] = function(ctx)
    -- FARMANIMAL.inc:69
    if ctx:condition("g_hTarget!=NULL") then -- FARMANIMAL.inc:72
        mm9.gosub(script, ctx, "BaseRunAway") -- FARMANIMAL.inc:73
    end -- FARMANIMAL.inc:74
    do return ctx:exit("") end -- FARMANIMAL.inc:76
end

script.labels["OnTargetDead"] = function(ctx)
    -- FARMANIMAL.inc:80
    ctx:command("target", "NULL") -- FARMANIMAL.inc:82
    ctx:command("g_htarget", "= NULL") -- FARMANIMAL.inc:83
    mm9.gosub(script, ctx, "BaseRunCancel") -- FARMANIMAL.inc:84
    do return ctx:exit("") end -- FARMANIMAL.inc:86
end

script.labels["BaseShouldRun"] = function(ctx)
    -- FARMANIMAL.inc:89
    -- Farm animals always run..
    ctx:command("g_btemp", "= TRUE") -- FARMANIMAL.inc:93
    do return ctx:exit("") end -- FARMANIMAL.inc:94
end

script.labels["FarmAnimalInit"] = function(ctx)
    -- FARMANIMAL.inc:97
    ctx:setPropNumber("WanderWaitMin", 10) -- FARMANIMAL.inc:100
    ctx:setPropNumber("WanderWaitMax", 20) -- FARMANIMAL.inc:101
    mm9.gosub(script, ctx, "BaseRunInit") -- FARMANIMAL.inc:103
    ctx:command("wait", "0, 0.1, FarmInitWander") -- FARMANIMAL.inc:105
    ctx:command("ondamage", "OnDamage") -- FARMANIMAL.inc:107
    ctx:command("ondamagedone", "OnDamageDone") -- FARMANIMAL.inc:108
    ctx:command("ontargetdead", "OnTargetDead") -- FARMANIMAL.inc:109
    do return ctx:exit("") end -- FARMANIMAL.inc:111
end

return script
