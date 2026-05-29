-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COFFINMUMMY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "flags.inc" }

-- MummyAwaken.scr
-- by SJR
-- 11-07-01
-- Purpose:mummy sleeps until
-- triggered to be awake
-- ScriptParams:
-- p3 = name of coffin to smash
script.labels["Main"] = function(ctx)
    -- COFFINMUMMY.scr:22
    ctx:getParam(3, "sCoffinName") -- COFFINMUMMY.scr:24
    ctx:onEvent("OnPostStartWorld", "OnPostStartworld") -- COFFINMUMMY.scr:26
    do return ctx:exit("TRUE") end -- COFFINMUMMY.scr:28
end

script.labels["OnPostStartworld"] = function(ctx)
    -- COFFINMUMMY.scr:31
    ctx:state().bAnimOk = ctx:self():isClass("Mummy") -- COFFINMUMMY.scr:35
    if ctx:condition("bAnimOk==FALSE") then -- COFFINMUMMY.scr:36
        ctx:state().bAnimOk = ctx:self():isClass("Zombie") -- COFFINMUMMY.scr:37
    end -- COFFINMUMMY.scr:38
    if ctx:condition("bAnimOk==TRUE") then -- COFFINMUMMY.scr:40
        -- AddModelKey "PreKick", OnPostDestroy
        ctx:self():loopAnimation("coffin2", 0) -- COFFINMUMMY.scr:42
    end -- COFFINMUMMY.scr:43
    ctx:self():setFlag("FLAG_VISIBLE", true) -- COFFINMUMMY.scr:45
    ctx:addTrigger("awaken", "WakeUp") -- COFFINMUMMY.scr:46
    ctx:self():setStat("gravity", "FALSE") -- COFFINMUMMY.scr:47
    -- clear solid flag so player cannot shoot us
    -- until we're ready...
    ctx:self():setFlag("FLAG_SOLID", false) -- COFFINMUMMY.scr:51
    do return ctx:exit("") end -- COFFINMUMMY.scr:53
end

script.labels["WakeUp"] = function(ctx)
    -- COFFINMUMMY.scr:56
    ctx:removeTrigger("awaken") -- COFFINMUMMY.scr:58
    ctx:onEvent("OnDamage", "DoNothing") -- COFFINMUMMY.scr:59
    ctx:self():setFlag("FLAG_VISIBLE", true) -- COFFINMUMMY.scr:61
    ctx:self():setFlag("FLAG_SOLID", true) -- COFFINMUMMY.scr:62
    ctx:state().hCoffin = ctx:objectOrNil("sCoffinName") -- COFFINMUMMY.scr:64
    ctx:addModelKey("AtKick", "OnPostDestroy") -- COFFINMUMMY.scr:66
    ctx:self():playAnimation("wakeup2") -- COFFINMUMMY.scr:67
    do return ctx:exit("TRUE") end -- COFFINMUMMY.scr:69
end

script.labels["GoNormal"] = function(ctx)
    -- COFFINMUMMY.scr:72
    -- Make sure we go after the player...
    -- (using hMe so as not to break the
    -- save game...)
    ctx:state().hMe = ctx:player() -- COFFINMUMMY.scr:79
    ctx:self():setTarget(ctx:self()) -- COFFINMUMMY.scr:80
    ctx:runScript("baseMelee.scr") -- COFFINMUMMY.scr:82
    do return ctx:exit("") end -- COFFINMUMMY.scr:83
end

script.labels["OnPostDestroy"] = function(ctx)
    -- COFFINMUMMY.scr:86
    ctx:self():setNumberProperty("CanDamage", "TRUE") -- COFFINMUMMY.scr:88
    ctx:self():setStat("gravity", "TRUE") -- COFFINMUMMY.scr:89
    if ctx:condition("hCoffin!=0") then -- COFFINMUMMY.scr:91
        ctx:trigger("hCoffin", "destroy") -- COFFINMUMMY.scr:92
    end -- COFFINMUMMY.scr:93
    ctx:self():stop() -- COFFINMUMMY.scr:95
    ctx:self():setIdle() -- COFFINMUMMY.scr:96
    mm9.gosub(script, ctx, "GoNormal") -- COFFINMUMMY.scr:98
    do return ctx:exit("TRUE") end -- COFFINMUMMY.scr:100
end

return script
