-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SONG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- song.scr
-- timmy
-- Handles the book's multiple animation
script.labels["OnPlay"] = function(ctx)
    -- SONG.scr:12
    ctx:command("getobjecthandle", "C1, g_hobject") -- SONG.scr:15
    ctx:trigger("g_hobject", "use") -- SONG.scr:16
    ctx:command("wait", ".5, D") -- SONG.scr:17
    do return ctx:exit("") end -- SONG.scr:18
end

script.labels["D"] = function(ctx)
    -- SONG.scr:21
    ctx:command("getobjecthandle", "F2, g_hobject") -- SONG.scr:24
    ctx:trigger("g_hobject", "use") -- SONG.scr:25
    ctx:command("wait", "1, G") -- SONG.scr:26
    do return ctx:exit("") end -- SONG.scr:28
end

script.labels["G"] = function(ctx)
    -- SONG.scr:31
    ctx:command("getobjecthandle", "G2, g_hobject") -- SONG.scr:34
    ctx:trigger("g_hobject", "use") -- SONG.scr:35
    ctx:command("wait", "1, G#") -- SONG.scr:36
    do return ctx:exit("") end -- SONG.scr:38
end

script.labels["G#"] = function(ctx)
    -- SONG.scr:41
    ctx:command("getobjecthandle", "G#2, g_hobject") -- SONG.scr:44
    ctx:trigger("g_hobject", "use") -- SONG.scr:45
    ctx:command("wait", ".25, A") -- SONG.scr:46
    do return ctx:exit("") end -- SONG.scr:48
end

script.labels["A"] = function(ctx)
    -- SONG.scr:51
    ctx:command("getobjecthandle", "A#2, g_hobject") -- SONG.scr:54
    ctx:trigger("g_hobject", "use") -- SONG.scr:55
    ctx:command("wait", ".25, G#2") -- SONG.scr:56
    do return ctx:exit("") end -- SONG.scr:58
end

script.labels["G#2"] = function(ctx)
    -- SONG.scr:62
    ctx:command("getobjecthandle", "G#2, g_hobject") -- SONG.scr:65
    ctx:trigger("g_hobject", "use") -- SONG.scr:66
    ctx:command("wait", "1, C") -- SONG.scr:67
    do return ctx:exit("") end -- SONG.scr:69
end

script.labels["C"] = function(ctx)
    -- SONG.scr:72
    ctx:command("getobjecthandle", "C1, g_hobject") -- SONG.scr:75
    ctx:trigger("g_hobject", "use") -- SONG.scr:76
    ctx:command("wait", "1, C2") -- SONG.scr:77
    do return ctx:exit("") end -- SONG.scr:78
end

-- ----phrase 2
script.labels["C2"] = function(ctx)
    -- SONG.scr:84
    ctx:command("getobjecthandle", "C1, g_hobject") -- SONG.scr:87
    ctx:trigger("g_hobject", "use") -- SONG.scr:88
    ctx:command("wait", ".5, F") -- SONG.scr:89
    do return ctx:exit("") end -- SONG.scr:90
end

script.labels["F"] = function(ctx)
    -- SONG.scr:93
    ctx:command("getobjecthandle", "F2, g_hobject") -- SONG.scr:96
    ctx:trigger("g_hobject", "use") -- SONG.scr:97
    ctx:command("wait", "1, G2") -- SONG.scr:98
    do return ctx:exit("") end -- SONG.scr:99
end

script.labels["G2"] = function(ctx)
    -- SONG.scr:101
    ctx:command("getobjecthandle", "G2, g_hobject") -- SONG.scr:104
    ctx:trigger("g_hobject", "use") -- SONG.scr:105
    ctx:command("wait", ".5, G#3") -- SONG.scr:106
    do return ctx:exit("") end -- SONG.scr:107
end

script.labels["G#3"] = function(ctx)
    -- SONG.scr:110
    ctx:command("getobjecthandle", "G#2, g_hobject") -- SONG.scr:113
    ctx:trigger("g_hobject", "use") -- SONG.scr:114
    ctx:command("wait", ".5, F2") -- SONG.scr:115
    do return ctx:exit("") end -- SONG.scr:116
end

script.labels["F2"] = function(ctx)
    -- SONG.scr:118
    ctx:command("getobjecthandle", "F2, g_hobject") -- SONG.scr:121
    ctx:trigger("g_hobject", "use") -- SONG.scr:122
    ctx:command("wait", ".25, G#4") -- SONG.scr:123
    do return ctx:exit("") end -- SONG.scr:124
end

script.labels["G#4"] = function(ctx)
    -- SONG.scr:127
    ctx:command("getobjecthandle", "G#2, g_hobject") -- SONG.scr:130
    ctx:trigger("g_hobject", "use") -- SONG.scr:131
    ctx:command("wait", ".25, F3") -- SONG.scr:132
    do return ctx:exit("") end -- SONG.scr:133
end

script.labels["F3"] = function(ctx)
    -- SONG.scr:135
    ctx:command("getobjecthandle", "F2, g_hobject") -- SONG.scr:138
    ctx:trigger("g_hobject", "use") -- SONG.scr:139
    ctx:command("wait", ".25, C3") -- SONG.scr:140
    do return ctx:exit("") end -- SONG.scr:141
end

script.labels["C3"] = function(ctx)
    -- SONG.scr:145
    ctx:command("getobjecthandle", "C2, g_hobject") -- SONG.scr:148
    ctx:trigger("g_hobject", "use") -- SONG.scr:149
    ctx:command("wait", ".25, F4") -- SONG.scr:150
    do return ctx:exit("") end -- SONG.scr:151
end

script.labels["F4"] = function(ctx)
    -- SONG.scr:153
    ctx:command("getobjecthandle", "A#2, g_hobject") -- SONG.scr:156
    ctx:trigger("g_hobject", "use") -- SONG.scr:157
    -- Wait .25, F
    do return ctx:exit("") end -- SONG.scr:159
end

script.labels["Main"] = function(ctx)
    -- SONG.scr:163
    -- TRACEON
    ctx:command("set", "counter, 0") -- SONG.scr:168
    ctx:addTrigger("Play", "OnPlay") -- SONG.scr:169
    do return ctx:exit("") end -- SONG.scr:170
end

return script
