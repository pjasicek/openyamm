-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SUNTEMPLEPRISON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- SunTemplePrison.scr
-- Tony Evans
-- This script controls the buttons that operate the
-- Prison Gate in the Grand Temple of the Sun
-- Parameters: none
script.labels["HandleButton1"] = function(ctx)
    -- SUNTEMPLEPRISON.scr:17
    if ctx:condition("PrisonBut1==TRUE") then -- SUNTEMPLEPRISON.scr:20
        ctx:state().PrisonBut1 = false -- SUNTEMPLEPRISON.scr:21
    else -- SUNTEMPLEPRISON.scr:22
        ctx:state().PrisonBut1 = true -- SUNTEMPLEPRISON.scr:23
    end -- SUNTEMPLEPRISON.scr:24
    if ctx:condition("PrisonBut1==TRUE") then -- SUNTEMPLEPRISON.scr:26
        if ctx:condition("PrisonBut2==TRUE") then -- SUNTEMPLEPRISON.scr:27
            mm9.gosub(script, ctx, "HandlePrisonGateOpen") -- SUNTEMPLEPRISON.scr:28
            ctx:state().PrisonBut1 = false -- SUNTEMPLEPRISON.scr:29
            ctx:state().PrisonBut2 = false -- SUNTEMPLEPRISON.scr:30
        end -- SUNTEMPLEPRISON.scr:31
    end -- SUNTEMPLEPRISON.scr:32
    do return ctx:exit("") end -- SUNTEMPLEPRISON.scr:34
end

script.labels["HandleButton2"] = function(ctx)
    -- SUNTEMPLEPRISON.scr:37
    if ctx:condition("PrisonBut2==TRUE") then -- SUNTEMPLEPRISON.scr:40
        ctx:state().PrisonBut2 = false -- SUNTEMPLEPRISON.scr:41
    else -- SUNTEMPLEPRISON.scr:42
        ctx:state().PrisonBut2 = true -- SUNTEMPLEPRISON.scr:43
    end -- SUNTEMPLEPRISON.scr:44
    if ctx:condition("PrisonBut2==TRUE") then -- SUNTEMPLEPRISON.scr:46
        if ctx:condition("PrisonBut1==TRUE") then -- SUNTEMPLEPRISON.scr:47
            mm9.gosub(script, ctx, "HandlePrisonGateOpen") -- SUNTEMPLEPRISON.scr:48
            ctx:state().PrisonBut1 = false -- SUNTEMPLEPRISON.scr:49
            ctx:state().PrisonBut2 = false -- SUNTEMPLEPRISON.scr:50
        end -- SUNTEMPLEPRISON.scr:51
    end -- SUNTEMPLEPRISON.scr:52
    do return ctx:exit("") end -- SUNTEMPLEPRISON.scr:54
end

script.labels["HandlePrisonGateOpen"] = function(ctx)
    -- SUNTEMPLEPRISON.scr:57
    -- make Gate open
    ctx:object("PrisonDoor"):trigger("open") -- SUNTEMPLEPRISON.scr:61-62
    local object = ctx:object("RopeWheel") -- SUNTEMPLEPRISON.scr:63
    object:trigger("reverse") -- SUNTEMPLEPRISON.scr:64
    object:trigger("on") -- SUNTEMPLEPRISON.scr:65
    do return ctx:exit("") end -- SUNTEMPLEPRISON.scr:66
end

script.labels["HandlePrisonGateClose"] = function(ctx)
    -- SUNTEMPLEPRISON.scr:69
    -- make Gate close
    ctx:object("PrisonDoor"):trigger("close") -- SUNTEMPLEPRISON.scr:73-74
    local object = ctx:object("RopeWheel") -- SUNTEMPLEPRISON.scr:75
    object:trigger("reverse") -- SUNTEMPLEPRISON.scr:76
    object:trigger("on") -- SUNTEMPLEPRISON.scr:77
    do return ctx:exit("") end -- SUNTEMPLEPRISON.scr:78
end

script.labels["Main"] = function(ctx)
    -- SUNTEMPLEPRISON.scr:83
    ctx:addTrigger("Button1", "HandleButton1") -- SUNTEMPLEPRISON.scr:86
    ctx:addTrigger("Button2", "HandleButton2") -- SUNTEMPLEPRISON.scr:87
    ctx:addTrigger("ClosePrison", "HandlePrisonGateClose") -- SUNTEMPLEPRISON.scr:88
    do return ctx:exit("") end -- SUNTEMPLEPRISON.scr:90
end

return script
