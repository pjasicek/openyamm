-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LINDISFARNEBELLCONTROLLER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- LindisfarneBellController.scr
-- timmy
-- Controls Lindisfarne Bell Puzzle
script.labels["Reset"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:18
    ctx:command("set", "FirstBell, 0") -- LINDISFARNEBELLCONTROLLER.scr:21
    ctx:command("set", "SecondBell, 0") -- LINDISFARNEBELLCONTROLLER.scr:22
    ctx:command("set", "ThirdBell, 0") -- LINDISFARNEBELLCONTROLLER.scr:23
    ctx:command("set", "FourthBell, 0") -- LINDISFARNEBELLCONTROLLER.scr:24
    ctx:command("set", "FifthBell, 0") -- LINDISFARNEBELLCONTROLLER.scr:25
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:26
end

script.labels["OnBell1"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:29
    ctx:command("set", "FirstBell 1") -- LINDISFARNEBELLCONTROLLER.scr:32
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:33
end

script.labels["OnBell2"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:36
    if ctx:condition("FirstBell==1") then -- LINDISFARNEBELLCONTROLLER.scr:39
        ctx:command("set", "SecondBell, 1") -- LINDISFARNEBELLCONTROLLER.scr:40
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:41
    else -- LINDISFARNEBELLCONTROLLER.scr:42
        mm9.gosub(script, ctx, "Reset") -- LINDISFARNEBELLCONTROLLER.scr:43
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:44
    end -- LINDISFARNEBELLCONTROLLER.scr:45
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:47
end

script.labels["OnBell3"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:50
    if ctx:condition("SecondBell==1") then -- LINDISFARNEBELLCONTROLLER.scr:54
        ctx:command("set", "ThirdBell, 1") -- LINDISFARNEBELLCONTROLLER.scr:55
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:56
    else -- LINDISFARNEBELLCONTROLLER.scr:57
        mm9.gosub(script, ctx, "Reset") -- LINDISFARNEBELLCONTROLLER.scr:58
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:59
    end -- LINDISFARNEBELLCONTROLLER.scr:60
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:61
end

script.labels["OnBell4"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:64
    if ctx:condition("ThirdBell==1") then -- LINDISFARNEBELLCONTROLLER.scr:68
        ctx:command("set", "FourthBell, 1") -- LINDISFARNEBELLCONTROLLER.scr:69
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:70
    else -- LINDISFARNEBELLCONTROLLER.scr:71
        mm9.gosub(script, ctx, "Reset") -- LINDISFARNEBELLCONTROLLER.scr:72
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:73
    end -- LINDISFARNEBELLCONTROLLER.scr:74
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:75
end

script.labels["OnBell5"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:78
    if ctx:condition("FourthBell==1") then -- LINDISFARNEBELLCONTROLLER.scr:82
        ctx:command("set", "FifthBell, 1") -- LINDISFARNEBELLCONTROLLER.scr:83
        mm9.gosub(script, ctx, "Finish") -- LINDISFARNEBELLCONTROLLER.scr:84
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:85
    else -- LINDISFARNEBELLCONTROLLER.scr:86
        mm9.gosub(script, ctx, "Reset") -- LINDISFARNEBELLCONTROLLER.scr:87
        do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:88
    end -- LINDISFARNEBELLCONTROLLER.scr:89
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:90
end

script.labels["Finish"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:94
    if not ctx:hasKey(9507) then -- LINDISFARNEBELLCONTROLLER.scr:97-98
        ctx:giveExp(2000) -- LINDISFARNEBELLCONTROLLER.scr:99
    end -- LINDISFARNEBELLCONTROLLER.scr:100
    ctx:giveKey(9507) -- LINDISFARNEBELLCONTROLLER.scr:102
    ctx:command("getobjecthandle", "thjorad g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:103
    ctx:trigger("G_Hobject", "TurnOn") -- LINDISFARNEBELLCONTROLLER.scr:104
    ctx:command("getobjecthandle", "ThjoradMonk1 g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:106
    ctx:trigger("g_hobject", "GoToPray") -- LINDISFARNEBELLCONTROLLER.scr:107
    ctx:command("getobjecthandle", "ThjoradMonk2 g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:108
    ctx:trigger("g_hobject", "GoToPray") -- LINDISFARNEBELLCONTROLLER.scr:109
    ctx:command("getobjecthandle", "ThjoradMonk3 g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:110
    ctx:trigger("g_hobject", "GoToPray") -- LINDISFARNEBELLCONTROLLER.scr:111
    ctx:command("getobjecthandle", "ThjoradMonk4 g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:112
    ctx:trigger("g_hobject", "GoToPray") -- LINDISFARNEBELLCONTROLLER.scr:113
    ctx:command("getobjecthandle", "Bell1, g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:116
    ctx:trigger("g_hobject", "use") -- LINDISFARNEBELLCONTROLLER.scr:117
    ctx:command("wait", "1 .5, 1") -- LINDISFARNEBELLCONTROLLER.scr:118
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:119
end

script.labels["1"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:122
    ctx:command("getobjecthandle", "Bell2, g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:125
    ctx:trigger("g_hobject", "use") -- LINDISFARNEBELLCONTROLLER.scr:126
    ctx:command("wait", "1 .5, 2") -- LINDISFARNEBELLCONTROLLER.scr:127
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:129
end

script.labels["2"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:132
    ctx:command("getobjecthandle", "Bell3, g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:135
    ctx:trigger("g_hobject", "use") -- LINDISFARNEBELLCONTROLLER.scr:136
    ctx:command("wait", "1 .25, 3") -- LINDISFARNEBELLCONTROLLER.scr:137
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:139
end

script.labels["3"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:144
    ctx:command("getobjecthandle", "Bell4, g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:147
    ctx:trigger("g_hobject", "use") -- LINDISFARNEBELLCONTROLLER.scr:148
    ctx:command("wait", "1 .25, 4") -- LINDISFARNEBELLCONTROLLER.scr:149
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:151
end

script.labels["4"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:154
    ctx:command("getobjecthandle", "Bell5, g_hobject") -- LINDISFARNEBELLCONTROLLER.scr:157
    ctx:trigger("g_hobject", "use") -- LINDISFARNEBELLCONTROLLER.scr:158
    ctx:command("wait", "1 .5, DoNothing") -- LINDISFARNEBELLCONTROLLER.scr:159
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:161
end

script.labels["Main"] = function(ctx)
    -- LINDISFARNEBELLCONTROLLER.scr:167
    -- TraceON
    ctx:addTrigger("Bell1", "OnBell1") -- LINDISFARNEBELLCONTROLLER.scr:172
    ctx:addTrigger("Bell2", "OnBell2") -- LINDISFARNEBELLCONTROLLER.scr:173
    ctx:addTrigger("Bell3", "OnBell3") -- LINDISFARNEBELLCONTROLLER.scr:174
    ctx:addTrigger("Bell4", "OnBell4") -- LINDISFARNEBELLCONTROLLER.scr:175
    ctx:addTrigger("Bell5", "OnBell5") -- LINDISFARNEBELLCONTROLLER.scr:176
    mm9.gosub(script, ctx, "Reset") -- LINDISFARNEBELLCONTROLLER.scr:178
    do return ctx:exit("") end -- LINDISFARNEBELLCONTROLLER.scr:179
end

return script
