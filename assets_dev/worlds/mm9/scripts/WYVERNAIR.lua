-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WYVERNAIR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "wanderair.inc" }

-- WyvernAir.scr
-- Quick-and-dirty script for wyvern...
script.labels["LaunchDone"] = function(ctx)
    -- WYVERNAIR.scr:13
    ctx:self():setTarget(ctx:object("g_hAttacker")) -- WYVERNAIR.scr:16
    ctx:runScript("WyvernGround.scr") -- WYVERNAIR.scr:17
    do return ctx:exit("TRUE") end -- WYVERNAIR.scr:19
end

script.labels["WaitCancel"] = function(ctx)
    -- WYVERNAIR.scr:22
    do return ctx:exit("TRUE") end -- WYVERNAIR.scr:25
end

script.labels["DamageDone"] = function(ctx)
    -- WYVERNAIR.scr:28
    ctx:state().g_bTemp = ctx:self():isOnGround() -- WYVERNAIR.scr:31
    if ctx:condition("g_bTemp==TRUE") then -- WYVERNAIR.scr:33
        ctx:self():launch("LaunchDone", 200) -- WYVERNAIR.scr:34
    else -- WYVERNAIR.scr:35
        mm9.gosub(script, ctx, "LaunchDone") -- WYVERNAIR.scr:36
    end -- WYVERNAIR.scr:37
    do return ctx:exit("TRUE") end -- WYVERNAIR.scr:39
end

script.labels["Damage"] = function(ctx)
    -- WYVERNAIR.scr:42
    ctx:getParam(0, "g_hAttacker") -- WYVERNAIR.scr:44
    ctx:self():sendAlert(ctx:object("g_hAttacker")) -- WYVERNAIR.scr:45
    do return ctx:exit("FALSE") end -- WYVERNAIR.scr:47
end

script.labels["FoundPlayer"] = function(ctx)
    -- WYVERNAIR.scr:50
    ctx:getParam(0, "g_hTarget") -- WYVERNAIR.scr:52
    ctx:self():setTarget(ctx:object("g_hTarget")) -- WYVERNAIR.scr:53
    ctx:runScript("WyvernGround.scr") -- WYVERNAIR.scr:55
    do return ctx:exit("TRUE") end -- WYVERNAIR.scr:57
end

script.labels["Main"] = function(ctx)
    -- WYVERNAIR.scr:60
    mm9.gosub(script, ctx, "WanderAirInit") -- WYVERNAIR.scr:65
    ctx:onEvent("OnFoundPlayer", "FoundPlayer") -- WYVERNAIR.scr:67
    ctx:onEvent("OnDamage", "Damage") -- WYVERNAIR.scr:68
    ctx:onEvent("OnDamageDone", "DamageDone") -- WYVERNAIR.scr:69
    do return ctx:exit("") end -- WYVERNAIR.scr:71
end

return script
