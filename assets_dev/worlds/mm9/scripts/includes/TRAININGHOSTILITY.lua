-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRAININGHOSTILITY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "range.inc" }

script.labels["InitTrainingHostility"] = function(ctx)
    -- TRAININGHOSTILITY.inc:5
    ctx:command("ondeath", "_OnDeath") -- TRAININGHOSTILITY.inc:7
    ctx:command("ondamage", "_OnDamage") -- TRAININGHOSTILITY.inc:8
    ctx:command("onfoundtarget", "_OnFoundTarget") -- TRAININGHOSTILITY.inc:9
    ctx:command("onalert", "_OnDamage") -- TRAININGHOSTILITY.inc:10
    do return ctx:exit("TRUE") end -- TRAININGHOSTILITY.inc:12
end

script.labels["_OnFoundTarget"] = function(ctx)
    -- TRAININGHOSTILITY.inc:15
    mm9.gosub(script, ctx, "_BaseInit") -- TRAININGHOSTILITY.inc:17
    mm9.gosub(script, ctx, "OnFoundTarget") -- TRAININGHOSTILITY.inc:18
    do return ctx:exit("TRUE") end -- TRAININGHOSTILITY.inc:20
end

script.labels["_OnDeath"] = function(ctx)
    -- TRAININGHOSTILITY.inc:23
    mm9.gosub(script, ctx, "_BaseInit") -- TRAININGHOSTILITY.inc:25
    mm9.gosub(script, ctx, "OnDeath") -- TRAININGHOSTILITY.inc:26
    do return ctx:exit("TRUE") end -- TRAININGHOSTILITY.inc:28
end

script.labels["_OnDamage"] = function(ctx)
    -- TRAININGHOSTILITY.inc:31
    mm9.gosub(script, ctx, "_BaseInit") -- TRAININGHOSTILITY.inc:33
    mm9.gosub(script, ctx, "OnDamage") -- TRAININGHOSTILITY.inc:34
    do return ctx:exit("TRUE") end -- TRAININGHOSTILITY.inc:36
end

script.labels["_BaseInit"] = function(ctx)
    -- TRAININGHOSTILITY.inc:39
    ctx:getParam(0, "g_hTarget") -- TRAININGHOSTILITY.inc:41
    ctx:command("sendalert", "g_hTarget") -- TRAININGHOSTILITY.inc:42
    mm9.gosub(script, ctx, "BaseInit") -- TRAININGHOSTILITY.inc:44
    mm9.gosub(script, ctx, "RangeInit") -- TRAININGHOSTILITY.inc:45
    mm9.gosub(script, ctx, "SetupTarget") -- TRAININGHOSTILITY.inc:47
    mm9.gosub(script, ctx, "AggressiveStart") -- TRAININGHOSTILITY.inc:48
    do return ctx:exit("TRUE") end -- TRAININGHOSTILITY.inc:50
end

return script
