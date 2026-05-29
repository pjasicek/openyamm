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
    ctx:object("C1"):trigger("use") -- SONG.scr:15-16
    ctx:wait(.5, .5, "D") -- SONG.scr:17
    do return ctx:exit("") end -- SONG.scr:18
end

script.labels["D"] = function(ctx)
    -- SONG.scr:21
    ctx:object("F2"):trigger("use") -- SONG.scr:24-25
    ctx:wait(1, 1, "G") -- SONG.scr:26
    do return ctx:exit("") end -- SONG.scr:28
end

script.labels["G"] = function(ctx)
    -- SONG.scr:31
    ctx:object("G2"):trigger("use") -- SONG.scr:34-35
    ctx:wait(1, 1, "G#") -- SONG.scr:36
    do return ctx:exit("") end -- SONG.scr:38
end

script.labels["G#"] = function(ctx)
    -- SONG.scr:41
    ctx:object("G#2"):trigger("use") -- SONG.scr:44-45
    ctx:wait(.25, .25, "A") -- SONG.scr:46
    do return ctx:exit("") end -- SONG.scr:48
end

script.labels["A"] = function(ctx)
    -- SONG.scr:51
    ctx:object("A#2"):trigger("use") -- SONG.scr:54-55
    ctx:wait(.25, .25, "G#2") -- SONG.scr:56
    do return ctx:exit("") end -- SONG.scr:58
end

script.labels["G#2"] = function(ctx)
    -- SONG.scr:62
    ctx:object("G#2"):trigger("use") -- SONG.scr:65-66
    ctx:wait(1, 1, "C") -- SONG.scr:67
    do return ctx:exit("") end -- SONG.scr:69
end

script.labels["C"] = function(ctx)
    -- SONG.scr:72
    ctx:object("C1"):trigger("use") -- SONG.scr:75-76
    ctx:wait(1, 1, "C2") -- SONG.scr:77
    do return ctx:exit("") end -- SONG.scr:78
end

-- ----phrase 2
script.labels["C2"] = function(ctx)
    -- SONG.scr:84
    ctx:object("C1"):trigger("use") -- SONG.scr:87-88
    ctx:wait(.5, .5, "F") -- SONG.scr:89
    do return ctx:exit("") end -- SONG.scr:90
end

script.labels["F"] = function(ctx)
    -- SONG.scr:93
    ctx:object("F2"):trigger("use") -- SONG.scr:96-97
    ctx:wait(1, 1, "G2") -- SONG.scr:98
    do return ctx:exit("") end -- SONG.scr:99
end

script.labels["G2"] = function(ctx)
    -- SONG.scr:101
    ctx:object("G2"):trigger("use") -- SONG.scr:104-105
    ctx:wait(.5, .5, "G#3") -- SONG.scr:106
    do return ctx:exit("") end -- SONG.scr:107
end

script.labels["G#3"] = function(ctx)
    -- SONG.scr:110
    ctx:object("G#2"):trigger("use") -- SONG.scr:113-114
    ctx:wait(.5, .5, "F2") -- SONG.scr:115
    do return ctx:exit("") end -- SONG.scr:116
end

script.labels["F2"] = function(ctx)
    -- SONG.scr:118
    ctx:object("F2"):trigger("use") -- SONG.scr:121-122
    ctx:wait(.25, .25, "G#4") -- SONG.scr:123
    do return ctx:exit("") end -- SONG.scr:124
end

script.labels["G#4"] = function(ctx)
    -- SONG.scr:127
    ctx:object("G#2"):trigger("use") -- SONG.scr:130-131
    ctx:wait(.25, .25, "F3") -- SONG.scr:132
    do return ctx:exit("") end -- SONG.scr:133
end

script.labels["F3"] = function(ctx)
    -- SONG.scr:135
    ctx:object("F2"):trigger("use") -- SONG.scr:138-139
    ctx:wait(.25, .25, "C3") -- SONG.scr:140
    do return ctx:exit("") end -- SONG.scr:141
end

script.labels["C3"] = function(ctx)
    -- SONG.scr:145
    ctx:object("C2"):trigger("use") -- SONG.scr:148-149
    ctx:wait(.25, .25, "F4") -- SONG.scr:150
    do return ctx:exit("") end -- SONG.scr:151
end

script.labels["F4"] = function(ctx)
    -- SONG.scr:153
    ctx:object("A#2"):trigger("use") -- SONG.scr:156-157
    -- Wait .25, F
    do return ctx:exit("") end -- SONG.scr:159
end

script.labels["Main"] = function(ctx)
    -- SONG.scr:163
    -- TRACEON
    ctx:state().counter = 0 -- SONG.scr:168
    ctx:addTrigger("Play", "OnPlay") -- SONG.scr:169
    do return ctx:exit("") end -- SONG.scr:170
end

return script
