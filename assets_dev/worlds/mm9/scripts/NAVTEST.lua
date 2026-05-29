-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NAVTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }

-- NavTest.scr
-- NavPoint testing script...
script.labels["GoGetHim"] = function(ctx)
    -- NAVTEST.scr:12
    if ctx:condition("g_hTarget!=NULL") then -- NAVTEST.scr:15
        ctx:self():setTarget(ctx:object("g_hTarget")) -- NAVTEST.scr:16
        ctx:self():walkTo(ctx:object("g_hTarget")) -- NAVTEST.scr:17
    end -- NAVTEST.scr:18
    do return ctx:exit("") end -- NAVTEST.scr:20
end

script.labels["OnReset"] = function(ctx)
    -- NAVTEST.scr:23
    ctx:self():setTarget(nil) -- NAVTEST.scr:26
    ctx:state().g_hTarget = nil -- NAVTEST.scr:27
    do return ctx:exit("") end -- NAVTEST.scr:29
end

script.labels["OnUse"] = function(ctx)
    -- NAVTEST.scr:32
    ctx:getParam(0, "g_hObject") -- NAVTEST.scr:35
    ctx:self():faceObject(ctx:object("g_hObject"), 180) -- NAVTEST.scr:36
    ctx:setInt("g_sOut", "g_hObject") -- NAVTEST.scr:38
    do return ctx:exit("") end -- NAVTEST.scr:40
end

script.labels["OnDisable"] = function(ctx)
    -- NAVTEST.scr:43
    do return ctx:exit("") end -- NAVTEST.scr:47
end

script.labels["OnEnable"] = function(ctx)
    -- NAVTEST.scr:50
    mm9.gosub(script, ctx, "OnReset") -- NAVTEST.scr:53
    do return ctx:exit("") end -- NAVTEST.scr:55
end

script.labels["Damage"] = function(ctx)
    -- NAVTEST.scr:59
    ctx:getParam(0, "g_hTarget") -- NAVTEST.scr:61
    mm9.gosub(script, ctx, "GoGetHim") -- NAVTEST.scr:62
    do return ctx:exit("") end -- NAVTEST.scr:63
end

script.labels["main"] = function(ctx)
    -- NAVTEST.scr:66
    ctx:onEvent("OnDamageDone", "GoGetHim") -- NAVTEST.scr:70
    ctx:onEvent("OnDamage", "Damage") -- NAVTEST.scr:71
    ctx:addTrigger("Reset", "OnReset") -- NAVTEST.scr:73
    ctx:addTrigger("Use", "OnUse") -- NAVTEST.scr:74
    ctx:addTrigger("Disable", "OnDisable") -- NAVTEST.scr:75
    ctx:addTrigger("Enable", "OnEnable") -- NAVTEST.scr:76
    do return ctx:exit("") end -- NAVTEST.scr:78
end

return script
