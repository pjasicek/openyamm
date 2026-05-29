-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_SORCSTATUES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- 1000T_SorcStatues.scr
-- Karl Drown 11-20-01
-- Statues that call a shooter object to fire
-- at the party.
script.labels["DoNothing"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:23
    do return ctx:exit("True") end -- 1000T_SORCSTATUES.scr:26
end

script.labels["Start"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:29
    ctx:state().bIsCasting = true -- 1000T_SORCSTATUES.scr:31
    ctx:trigger("hDummy", "Go") -- 1000T_SORCSTATUES.scr:32
    ctx:trigger("hCastingSmoke", "On") -- 1000T_SORCSTATUES.scr:33
    mm9.gosub(script, ctx, "StartSequence") -- 1000T_SORCSTATUES.scr:34
    do return ctx:exit("TRUE") end -- 1000T_SORCSTATUES.scr:35
end

script.labels["TurnOff"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:37
    ctx:wait(1, 1, "DoNothing") -- 1000T_SORCSTATUES.scr:39
    ctx:trigger("hCastingSmoke", "Off") -- 1000T_SORCSTATUES.scr:40
    ctx:state().bIsCasting = false -- 1000T_SORCSTATUES.scr:41
    do return ctx:exit("TRUE") end -- 1000T_SORCSTATUES.scr:42
end

script.labels["Continue"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:44
    if ctx:condition("bIsCasting==FALSE") then -- 1000T_SORCSTATUES.scr:46
        do return ctx:exit("") end -- 1000T_SORCSTATUES.scr:47
    end -- 1000T_SORCSTATUES.scr:48
    ctx:self():playAnimation("Taunt", "StartSequence") -- 1000T_SORCSTATUES.scr:49
    do return ctx:exit("True") end -- 1000T_SORCSTATUES.scr:50
end

script.labels["StartSequence"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:52
    if ctx:condition("bIsCasting==FALSE") then -- 1000T_SORCSTATUES.scr:54
        do return ctx:exit("") end -- 1000T_SORCSTATUES.scr:55
    end -- 1000T_SORCSTATUES.scr:56
    ctx:self():playAnimation("fidget2", "Continue") -- 1000T_SORCSTATUES.scr:58
    do return ctx:exit("True") end -- 1000T_SORCSTATUES.scr:60
end

script.labels["Main2"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:62
    ctx:self():playAnimation("fidget2", "DoNothing") -- 1000T_SORCSTATUES.scr:64
    ctx:addTrigger("Go", "Start") -- 1000T_SORCSTATUES.scr:65
    ctx:addTrigger("Stop", "TurnOff") -- 1000T_SORCSTATUES.scr:66
    ctx:state().hDummy = ctx:objectOrNil("sShooter") -- 1000T_SORCSTATUES.scr:67
    ctx:state().hCastingSmoke = ctx:objectOrNil("sCastingSmoke") -- 1000T_SORCSTATUES.scr:68
    do return ctx:exit("True") end -- 1000T_SORCSTATUES.scr:69
end

script.labels["Main"] = function(ctx)
    -- 1000T_SORCSTATUES.scr:71
    ctx:getParam(0, "sShooter") -- 1000T_SORCSTATUES.scr:73
    ctx:getParam(1, "sCastingSmoke") -- 1000T_SORCSTATUES.scr:74
    ctx:wait(0, 0.5, "Main2") -- 1000T_SORCSTATUES.scr:75
    do return ctx:exit("") end -- 1000T_SORCSTATUES.scr:76
end

return script
