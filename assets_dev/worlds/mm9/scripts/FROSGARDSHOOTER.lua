-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FROSGARDSHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- FrosgardShooter.scr
-- By Timmy
-- Turns the shooter on and Off in Frosgard
script.labels["OnStart"] = function(ctx)
    -- FROSGARDSHOOTER.scr:18
    if ctx:condition("sTargetName==NULL") then -- FROSGARDSHOOTER.scr:21
        ctx:set("sTargetName", "Shoot") -- FROSGARDSHOOTER.scr:22
    end -- FROSGARDSHOOTER.scr:23
    ctx:getParam(0, "g_hTarget") -- FROSGARDSHOOTER.scr:26
    ctx:trigger("g_hmyobject", "On") -- FROSGARDSHOOTER.scr:29
    if ctx:condition("bTest==FALSE") then -- FROSGARDSHOOTER.scr:31
        ctx:object("BreakIce"):trigger("start") -- FROSGARDSHOOTER.scr:32-33
    end -- FROSGARDSHOOTER.scr:34
    if ctx:condition("bTest==TRUE") then -- FROSGARDSHOOTER.scr:36
        ctx:wait(4, 5, "Fire") -- FROSGARDSHOOTER.scr:37
    end -- FROSGARDSHOOTER.scr:38
    do return mm9.gotoLabel(script, ctx, "Target") end -- FROSGARDSHOOTER.scr:40
    do return ctx:exit("") end -- FROSGARDSHOOTER.scr:41
end

script.labels["Target"] = function(ctx)
    -- FROSGARDSHOOTER.scr:46
    if ctx:condition("nCounter==8") then -- FROSGARDSHOOTER.scr:51
        mm9.gosub(script, ctx, "off") -- FROSGARDSHOOTER.scr:52
        do return ctx:exit("") end -- FROSGARDSHOOTER.scr:53
    end -- FROSGARDSHOOTER.scr:54
    ctx:self():setTarget(nil) -- FROSGARDSHOOTER.scr:56
    ctx:set("sTarget", "sTargetName") -- FROSGARDSHOOTER.scr:58
    ctx:randomInt(0, 5, "g_ntemp") -- FROSGARDSHOOTER.scr:61
    ctx:set("sTarget", "sTarget + g_ntemp") -- FROSGARDSHOOTER.scr:62
    ctx:state().g_hobject = ctx:objectOrNil("sTarget") -- FROSGARDSHOOTER.scr:64
    ctx:self():setTarget(ctx:object("g_hobject")) -- FROSGARDSHOOTER.scr:65
    ctx:wait(1, .4, "Target") -- FROSGARDSHOOTER.scr:67
    ctx:state().nCounter = (tonumber(ctx:state().nCounter) or 0) + 1 -- FROSGARDSHOOTER.scr:68
    do return ctx:exit("") end -- FROSGARDSHOOTER.scr:69
end

script.labels["Fire"] = function(ctx)
    -- FROSGARDSHOOTER.scr:72
    ctx:object("shooter7"):trigger("on") -- FROSGARDSHOOTER.scr:75-76
    do return ctx:exit("") end -- FROSGARDSHOOTER.scr:78
end

script.labels["Off"] = function(ctx)
    -- FROSGARDSHOOTER.scr:81
    ctx:trigger("g_hmyobject", "Off") -- FROSGARDSHOOTER.scr:84
    if ctx:condition("bTest==FALSE") then -- FROSGARDSHOOTER.scr:85
        ctx:object("DestructableProp0"):trigger("destroy") -- FROSGARDSHOOTER.scr:86-87
    end -- FROSGARDSHOOTER.scr:88
    do return ctx:exit("") end -- FROSGARDSHOOTER.scr:90
end

script.labels["Main"] = function(ctx)
    -- FROSGARDSHOOTER.scr:93
    -- TraceOn ;delete me!!
    ctx:addTrigger("Start", "OnStart") -- FROSGARDSHOOTER.scr:97
    ctx:getParam(0, "sTargetName") -- FROSGARDSHOOTER.scr:98
    ctx:getParam(1, "bTest") -- FROSGARDSHOOTER.scr:99
    do return ctx:exit("") end -- FROSGARDSHOOTER.scr:100
end

return script
