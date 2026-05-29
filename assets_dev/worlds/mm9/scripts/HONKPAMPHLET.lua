-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKPAMPHLET.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "HonkHostility.inc" }

-- HONKpamphlet.scr
-- Purpose: pamphlet holding honk
-- with hostility check
-- activate prop
-- prop anim setup
script.labels["Main"] = function(ctx)
    -- HONKPAMPHLET.scr:20
    ctx:onEvent("OnPostStartWorld", "InitHonkGuardBasic") -- HONKPAMPHLET.scr:22
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:24
end

script.labels["InitHonkGuardBasic"] = function(ctx)
    -- HONKPAMPHLET.scr:27
    mm9.gosub(script, ctx, "BaseWanderInit") -- HONKPAMPHLET.scr:29
    mm9.gosub(script, ctx, "BaseWanderStartup") -- HONKPAMPHLET.scr:30
    mm9.gosub(script, ctx, "StartWork") -- HONKPAMPHLET.scr:32
    ctx:onEvent("OnDamage", "OnDamage") -- HONKPAMPHLET.scr:34
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:36
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- HONKPAMPHLET.scr:39
    -- this happens every time he stops wandering
    -- so, run the animation stuff here
    mm9.gosub(script, ctx, "StartWork") -- HONKPAMPHLET.scr:43
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:45
end

script.labels["StartWork"] = function(ctx)
    -- HONKPAMPHLET.scr:48
    -- if we dont have prop, attach it,
    -- then start animating
    if ctx:condition("hProp==0") then -- HONKPAMPHLET.scr:52
        mm9.gosub(script, ctx, "AttachTool") -- HONKPAMPHLET.scr:53
    end -- HONKPAMPHLET.scr:54
    ctx:self():loopAnimation("sAnimName", 2, "StartFidget") -- HONKPAMPHLET.scr:56
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:58
end

script.labels["StartFidget"] = function(ctx)
    -- HONKPAMPHLET.scr:61
    ctx:self():loopAnimation("Fidget_Name", 2, "StopWork") -- HONKPAMPHLET.scr:63
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:65
end

script.labels["StopWork"] = function(ctx)
    -- HONKPAMPHLET.scr:68
    -- since this is the end of the animations,
    -- go back to wandering...
    ctx:self():loopAnimation("sPauseName", 1, "StartWork") -- HONKPAMPHLET.scr:72
    -- This is what normally happens
    -- each time he stops. Resume wander...
    mm9.gosub(script, ctx, "BaseWanderStopTick") -- HONKPAMPHLET.scr:76
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:78
end

script.labels["AttachTool"] = function(ctx)
    -- HONKPAMPHLET.scr:81
    -- pamphlet attachment to model
    mm9.gosub(script, ctx, "SafeDetach") -- HONKPAMPHLET.scr:84
    ctx:self():attachProp("HonkPamphlet.ABC", "Pamphlet.DTX", "Pamphlet", ctx:object("hProp")) -- HONKPAMPHLET.scr:86
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:88
end

script.labels["SafeDetach"] = function(ctx)
    -- HONKPAMPHLET.scr:91
    -- remove the prop from the world safely
    if ctx:condition("hProp!=0") then -- HONKPAMPHLET.scr:94
        ctx:self():detachProp(ctx:object("hProp"), "FALSE") -- HONKPAMPHLET.scr:95
        ctx:object("hProp"):remove() -- HONKPAMPHLET.scr:96
        ctx:state().hProp = nil -- HONKPAMPHLET.scr:97
    end -- HONKPAMPHLET.scr:98
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:100
end

script.labels["OnDamage"] = function(ctx)
    -- HONKPAMPHLET.scr:103
    -- if player hit us, remove prop, attack
    ctx:getParam(0, "hParam") -- HONKPAMPHLET.scr:106
    ctx:state().bIsPlayer = ctx:object("hParam"):isPlayer() -- HONKPAMPHLET.scr:107
    if ctx:condition("bIsPlayer==TRUE") then -- HONKPAMPHLET.scr:108
        mm9.gosub(script, ctx, "SafeDetach") -- HONKPAMPHLET.scr:109
        mm9.gosub(script, ctx, "BecomeHostile") -- HONKPAMPHLET.scr:110
    end -- HONKPAMPHLET.scr:111
    do return ctx:exit("TRUE") end -- HONKPAMPHLET.scr:113
end

return script
