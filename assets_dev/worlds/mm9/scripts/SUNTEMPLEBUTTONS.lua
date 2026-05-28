-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SUNTEMPLEBUTTONS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- SunTempleButtons.scr
-- Tony Evans
-- This script controls the buttons that operate the
-- elevator in the Grand Temple of the Sun
-- Parameters:
-- variables for handling the buttons
script.labels["HandleStar1"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:22
    if ctx:condition("StarBut1==TRUE") then -- SUNTEMPLEBUTTONS.scr:25
        ctx:command("set", "StarBut1, FALSE") -- SUNTEMPLEBUTTONS.scr:26
    else -- SUNTEMPLEBUTTONS.scr:27
        ctx:command("set", "StarBut1, TRUE") -- SUNTEMPLEBUTTONS.scr:28
    end -- SUNTEMPLEBUTTONS.scr:29
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:31
end

script.labels["HandleStar2"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:34
    if ctx:condition("StarBut2==TRUE") then -- SUNTEMPLEBUTTONS.scr:37
        ctx:command("set", "StarBut2, FALSE") -- SUNTEMPLEBUTTONS.scr:38
    else -- SUNTEMPLEBUTTONS.scr:39
        ctx:command("set", "StarBut2, TRUE") -- SUNTEMPLEBUTTONS.scr:40
    end -- SUNTEMPLEBUTTONS.scr:41
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:43
end

script.labels["HandleDiamond1"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:46
    if ctx:condition("DiamondBut1==TRUE") then -- SUNTEMPLEBUTTONS.scr:49
        ctx:command("set", "DiamondBut1, FALSE") -- SUNTEMPLEBUTTONS.scr:50
    else -- SUNTEMPLEBUTTONS.scr:51
        ctx:command("set", "DiamondBut1, TRUE") -- SUNTEMPLEBUTTONS.scr:52
    end -- SUNTEMPLEBUTTONS.scr:53
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:55
end

script.labels["HandleDiamond2"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:58
    if ctx:condition("DiamondBut2==TRUE") then -- SUNTEMPLEBUTTONS.scr:61
        ctx:command("set", "DiamondBut2, FALSE") -- SUNTEMPLEBUTTONS.scr:62
    else -- SUNTEMPLEBUTTONS.scr:63
        ctx:command("set", "DiamondBut2, TRUE") -- SUNTEMPLEBUTTONS.scr:64
    end -- SUNTEMPLEBUTTONS.scr:65
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:67
end

script.labels["HandleMoon1"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:70
    if ctx:condition("MoonBut1==TRUE") then -- SUNTEMPLEBUTTONS.scr:73
        ctx:command("set", "MoonBut1, FALSE") -- SUNTEMPLEBUTTONS.scr:74
    else -- SUNTEMPLEBUTTONS.scr:75
        ctx:command("set", "MoonBut1, TRUE") -- SUNTEMPLEBUTTONS.scr:76
    end -- SUNTEMPLEBUTTONS.scr:77
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:79
end

script.labels["HandleMoon2"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:82
    if ctx:condition("MoonBut2==TRUE") then -- SUNTEMPLEBUTTONS.scr:85
        ctx:command("set", "MoonBut2, FALSE") -- SUNTEMPLEBUTTONS.scr:86
    else -- SUNTEMPLEBUTTONS.scr:87
        ctx:command("set", "MoonBut2, TRUE") -- SUNTEMPLEBUTTONS.scr:88
    end -- SUNTEMPLEBUTTONS.scr:89
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:91
end

script.labels["HandleMainButton"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:94
    if ctx:condition("StarBut1==TRUE") then -- SUNTEMPLEBUTTONS.scr:97
        if ctx:condition("StarBut2==FALSE") then -- SUNTEMPLEBUTTONS.scr:98
            if ctx:condition("DiamondBut1==FALSE") then -- SUNTEMPLEBUTTONS.scr:99
                if ctx:condition("DiamondBut2=TRUE") then -- SUNTEMPLEBUTTONS.scr:100
                    if ctx:condition("MoonBut1=FALSE") then -- SUNTEMPLEBUTTONS.scr:101
                        if ctx:condition("MoonBut2=FALSE") then -- SUNTEMPLEBUTTONS.scr:102
                            mm9.gosub(script, ctx, "HandleElevator") -- SUNTEMPLEBUTTONS.scr:103
                        end -- SUNTEMPLEBUTTONS.scr:104
                    end -- SUNTEMPLEBUTTONS.scr:105
                end -- SUNTEMPLEBUTTONS.scr:106
            end -- SUNTEMPLEBUTTONS.scr:107
        end -- SUNTEMPLEBUTTONS.scr:108
    end -- SUNTEMPLEBUTTONS.scr:109
    do return ctx:exit("FALSE") end -- SUNTEMPLEBUTTONS.scr:111
end

script.labels["HandleElevator"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:114
    -- make elevator descend
    ctx:command("getobjecthandle", "MainElevator, g_hobject") -- SUNTEMPLEBUTTONS.scr:118
    ctx:trigger("g_hobject", "open") -- SUNTEMPLEBUTTONS.scr:119
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:121
end

script.labels["Main"] = function(ctx)
    -- SUNTEMPLEBUTTONS.scr:124
    ctx:addTrigger("Star1", "HandleStar1") -- SUNTEMPLEBUTTONS.scr:127
    ctx:addTrigger("Star2", "HandleStar2") -- SUNTEMPLEBUTTONS.scr:128
    ctx:addTrigger("Diamond1", "HandleDiamond1") -- SUNTEMPLEBUTTONS.scr:129
    ctx:addTrigger("Diamond2", "HandleDiamond2") -- SUNTEMPLEBUTTONS.scr:130
    ctx:addTrigger("Moon1", "HandleMoon1") -- SUNTEMPLEBUTTONS.scr:131
    ctx:addTrigger("Moon2", "HandleMoon2") -- SUNTEMPLEBUTTONS.scr:132
    ctx:addTrigger("Use", "HandleMainButton") -- SUNTEMPLEBUTTONS.scr:133
    do return ctx:exit("") end -- SUNTEMPLEBUTTONS.scr:135
end

return script
