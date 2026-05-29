-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARROW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- arrow.scr
-- timmy
-- Handles the arrow shooter in A2_RD1
script.labels["OnUse"] = function(ctx)
    -- ARROW.scr:12
    ctx:randomInt(1, 8, "g_ntemp") -- ARROW.scr:15
    if ctx:condition("g_ntemp==1") then -- ARROW.scr:17
        do return mm9.gotoLabel(script, ctx, "1") end -- ARROW.scr:18
    end -- ARROW.scr:20
    if ctx:condition("g_ntemp==2") then -- ARROW.scr:22
        do return mm9.gotoLabel(script, ctx, "2") end -- ARROW.scr:23
    end -- ARROW.scr:24
    if ctx:condition("g_ntemp==3") then -- ARROW.scr:26
        do return mm9.gotoLabel(script, ctx, "3") end -- ARROW.scr:27
    end -- ARROW.scr:28
    if ctx:condition("g_ntemp==4") then -- ARROW.scr:30
        do return mm9.gotoLabel(script, ctx, "4") end -- ARROW.scr:31
    end -- ARROW.scr:32
    if ctx:condition("g_ntemp==5") then -- ARROW.scr:34
        do return mm9.gotoLabel(script, ctx, "5") end -- ARROW.scr:35
    end -- ARROW.scr:36
    if ctx:condition("g_ntemp==6") then -- ARROW.scr:38
        do return mm9.gotoLabel(script, ctx, "6") end -- ARROW.scr:39
    end -- ARROW.scr:40
    if ctx:condition("g_ntemp==7") then -- ARROW.scr:42
        do return mm9.gotoLabel(script, ctx, "7") end -- ARROW.scr:43
    end -- ARROW.scr:44
    if ctx:condition("g_ntemp==8") then -- ARROW.scr:46
        do return mm9.gotoLabel(script, ctx, "8") end -- ARROW.scr:47
    end -- ARROW.scr:48
    do return ctx:exit("") end -- ARROW.scr:50
end

script.labels["1"] = function(ctx)
    -- ARROW.scr:53
    ctx:state().g_hobject = ctx:objectOrNil("arrows1") -- ARROW.scr:57
    if ctx:condition("g_hobject==null") then -- ARROW.scr:58
        ctx:debugOut("NULL!") -- ARROW.scr:59
        do return ctx:exit("") end -- ARROW.scr:60
    end -- ARROW.scr:61
    ctx:trigger("g_hobject", "On") -- ARROW.scr:62
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:63
    do return ctx:exit("") end -- ARROW.scr:64
end

script.labels["2"] = function(ctx)
    -- ARROW.scr:68
    ctx:state().g_hobject = ctx:objectOrNil("arrows2") -- ARROW.scr:72
    if ctx:condition("g_hobject==null") then -- ARROW.scr:73
        ctx:debugOut("NULL!") -- ARROW.scr:74
        do return ctx:exit("") end -- ARROW.scr:75
    end -- ARROW.scr:76
    ctx:trigger("g_hobject", "On") -- ARROW.scr:77
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:78
    do return ctx:exit("") end -- ARROW.scr:79
end

script.labels["3"] = function(ctx)
    -- ARROW.scr:83
    ctx:state().g_hobject = ctx:objectOrNil("arrows3") -- ARROW.scr:87
    if ctx:condition("g_hobject==null") then -- ARROW.scr:88
        ctx:debugOut("NULL!") -- ARROW.scr:89
        do return ctx:exit("") end -- ARROW.scr:90
    end -- ARROW.scr:91
    ctx:trigger("g_hobject", "On") -- ARROW.scr:92
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:93
    do return ctx:exit("") end -- ARROW.scr:94
end

script.labels["4"] = function(ctx)
    -- ARROW.scr:98
    ctx:state().g_hobject = ctx:objectOrNil("arrows4") -- ARROW.scr:102
    if ctx:condition("g_hobject==null") then -- ARROW.scr:103
        ctx:debugOut("NULL!") -- ARROW.scr:104
        do return ctx:exit("") end -- ARROW.scr:105
    end -- ARROW.scr:106
    ctx:trigger("g_hobject", "On") -- ARROW.scr:107
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:108
    do return ctx:exit("") end -- ARROW.scr:109
end

script.labels["5"] = function(ctx)
    -- ARROW.scr:113
    ctx:state().g_hobject = ctx:objectOrNil("arrows5") -- ARROW.scr:117
    if ctx:condition("g_hobject==null") then -- ARROW.scr:118
        ctx:debugOut("NULL!") -- ARROW.scr:119
        do return ctx:exit("") end -- ARROW.scr:120
    end -- ARROW.scr:121
    ctx:trigger("g_hobject", "On") -- ARROW.scr:122
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:123
    do return ctx:exit("") end -- ARROW.scr:124
end

script.labels["6"] = function(ctx)
    -- ARROW.scr:128
    ctx:state().g_hobject = ctx:objectOrNil("arrows6") -- ARROW.scr:132
    if ctx:condition("g_hobject==null") then -- ARROW.scr:133
        ctx:debugOut("NULL!") -- ARROW.scr:134
        do return ctx:exit("") end -- ARROW.scr:135
    end -- ARROW.scr:136
    ctx:trigger("g_hobject", "On") -- ARROW.scr:137
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:138
    do return ctx:exit("") end -- ARROW.scr:139
end

script.labels["7"] = function(ctx)
    -- ARROW.scr:143
    ctx:state().g_hobject = ctx:objectOrNil("arrows7") -- ARROW.scr:147
    if ctx:condition("g_hobject==null") then -- ARROW.scr:148
        ctx:debugOut("NULL!") -- ARROW.scr:149
        do return ctx:exit("") end -- ARROW.scr:150
    end -- ARROW.scr:151
    ctx:trigger("g_hobject", "On") -- ARROW.scr:152
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:153
    do return ctx:exit("") end -- ARROW.scr:154
end

script.labels["8"] = function(ctx)
    -- ARROW.scr:158
    ctx:state().g_hobject = ctx:objectOrNil("arrows8") -- ARROW.scr:162
    if ctx:condition("g_hobject==null") then -- ARROW.scr:163
        ctx:debugOut("NULL!") -- ARROW.scr:164
        do return ctx:exit("") end -- ARROW.scr:165
    end -- ARROW.scr:166
    ctx:trigger("g_hobject", "On") -- ARROW.scr:167
    ctx:trigger("g_hobject", "Off") -- ARROW.scr:168
    do return ctx:exit("") end -- ARROW.scr:169
end

script.labels["Main"] = function(ctx)
    -- ARROW.scr:172
    -- TRACEON
    ctx:state().counter = 0 -- ARROW.scr:177
    ctx:addTrigger("Shoot", "OnUse") -- ARROW.scr:178
    do return ctx:exit("") end -- ARROW.scr:179
end

return script
