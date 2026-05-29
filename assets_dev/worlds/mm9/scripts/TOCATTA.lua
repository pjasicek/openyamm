-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOCATTA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- tocatta.scr
-- timmy
-- Plays the intro to tocatta and fugue in dm (transposed to gm)
script.labels["OnPlay"] = function(ctx)
    -- TOCATTA.scr:12
    ctx:object("D2"):trigger("use") -- TOCATTA.scr:15-16
    ctx:wait(.2, .2, "1") -- TOCATTA.scr:17
    do return ctx:exit("") end -- TOCATTA.scr:18
end

script.labels["1"] = function(ctx)
    -- TOCATTA.scr:21
    ctx:object("C2"):trigger("use") -- TOCATTA.scr:24-25
    ctx:wait(.2, .2, "2") -- TOCATTA.scr:26
    do return ctx:exit("") end -- TOCATTA.scr:28
end

script.labels["2"] = function(ctx)
    -- TOCATTA.scr:31
    ctx:object("D2"):trigger("use") -- TOCATTA.scr:34-35
    ctx:wait(1, 1, "3") -- TOCATTA.scr:36
    do return ctx:exit("") end -- TOCATTA.scr:38
end

-- RUN DOWN #1
script.labels["3"] = function(ctx)
    -- TOCATTA.scr:43
    ctx:object("C2"):trigger("use") -- TOCATTA.scr:46-47
    ctx:wait(.5, .5, "4") -- TOCATTA.scr:48
    do return ctx:exit("") end -- TOCATTA.scr:50
end

script.labels["4"] = function(ctx)
    -- TOCATTA.scr:53
    ctx:object("A#2"):trigger("use") -- TOCATTA.scr:56-57
    ctx:wait(.5, .5, "5") -- TOCATTA.scr:58
    do return ctx:exit("") end -- TOCATTA.scr:60
end

script.labels["5"] = function(ctx)
    -- TOCATTA.scr:64
    ctx:object("a2"):trigger("use") -- TOCATTA.scr:67-68
    ctx:wait(.5, .5, "6") -- TOCATTA.scr:69
    do return ctx:exit("") end -- TOCATTA.scr:71
end

script.labels["6"] = function(ctx)
    -- TOCATTA.scr:74
    ctx:object("g2"):trigger("use") -- TOCATTA.scr:77-78
    ctx:wait(.5, .5, "7") -- TOCATTA.scr:79
    do return ctx:exit("") end -- TOCATTA.scr:80
end

script.labels["7"] = function(ctx)
    -- TOCATTA.scr:85
    ctx:object("f#2"):trigger("use") -- TOCATTA.scr:88-89
    ctx:wait(1, 1, "8") -- TOCATTA.scr:90
    do return ctx:exit("") end -- TOCATTA.scr:92
end

script.labels["8"] = function(ctx)
    -- TOCATTA.scr:95
    ctx:object("g2"):trigger("use") -- TOCATTA.scr:98-99
    ctx:wait(1.5, 1.5, "Phrase2") -- TOCATTA.scr:100
    do return ctx:exit("") end -- TOCATTA.scr:101
end

-- PHRASE 2
script.labels["Phrase2"] = function(ctx)
    -- TOCATTA.scr:113
    ctx:object("D1"):trigger("use") -- TOCATTA.scr:116-117
    ctx:wait(.2, .2, "1-2") -- TOCATTA.scr:118
    do return ctx:exit("") end -- TOCATTA.scr:119
end

script.labels["1-2"] = function(ctx)
    -- TOCATTA.scr:122
    ctx:object("C1"):trigger("use") -- TOCATTA.scr:125-126
    ctx:wait(.2, .2, "2-2") -- TOCATTA.scr:127
    do return ctx:exit("") end -- TOCATTA.scr:129
end

script.labels["2-2"] = function(ctx)
    -- TOCATTA.scr:132
    ctx:object("D1"):trigger("use") -- TOCATTA.scr:135-136
    ctx:wait(1, 1, "3-2") -- TOCATTA.scr:137
    do return ctx:exit("") end -- TOCATTA.scr:139
end

-- RUN DOWN #2
script.labels["3-2"] = function(ctx)
    -- TOCATTA.scr:144
    ctx:object("A1"):trigger("use") -- TOCATTA.scr:147-148
    ctx:wait(.5, .5, "4-2") -- TOCATTA.scr:149
    do return ctx:exit("") end -- TOCATTA.scr:151
end

script.labels["4-2"] = function(ctx)
    -- TOCATTA.scr:154
    ctx:object("A#1"):trigger("use") -- TOCATTA.scr:157-158
    ctx:wait(.5, .5, "5-2") -- TOCATTA.scr:159
    do return ctx:exit("") end -- TOCATTA.scr:161
end

script.labels["5-2"] = function(ctx)
    -- TOCATTA.scr:165
    ctx:object("F#1"):trigger("use") -- TOCATTA.scr:168-169
    ctx:wait(1, 1, "6-2") -- TOCATTA.scr:170
    do return ctx:exit("") end -- TOCATTA.scr:172
end

script.labels["6-2"] = function(ctx)
    -- TOCATTA.scr:175
    ctx:object("G1"):trigger("use") -- TOCATTA.scr:178-179
    ctx:wait(1.5, 1.5, "Phrase3") -- TOCATTA.scr:180
    do return ctx:exit("") end -- TOCATTA.scr:181
end

-- PHRASE 3
script.labels["Phrase3"] = function(ctx)
    -- TOCATTA.scr:197
    ctx:object("D1"):trigger("use") -- TOCATTA.scr:200-201
    ctx:wait(.2, .2, "1-3") -- TOCATTA.scr:202
    do return ctx:exit("") end -- TOCATTA.scr:203
end

script.labels["1-3"] = function(ctx)
    -- TOCATTA.scr:206
    ctx:object("C1"):trigger("use") -- TOCATTA.scr:209-210
    ctx:wait(.2, .2, "2-3") -- TOCATTA.scr:211
    do return ctx:exit("") end -- TOCATTA.scr:213
end

script.labels["2-3"] = function(ctx)
    -- TOCATTA.scr:216
    ctx:object("D1"):trigger("use") -- TOCATTA.scr:219-220
    ctx:wait(1, 1, "3-3") -- TOCATTA.scr:221
    do return ctx:exit("") end -- TOCATTA.scr:223
end

-- RUN DOWN #3
script.labels["3-3"] = function(ctx)
    -- TOCATTA.scr:228
    ctx:object("C1"):trigger("use") -- TOCATTA.scr:231-232
    ctx:wait(.5, .5, "4-3") -- TOCATTA.scr:233
    do return ctx:exit("") end -- TOCATTA.scr:235
end

script.labels["4-3"] = function(ctx)
    -- TOCATTA.scr:238
    ctx:object("A#1"):trigger("use") -- TOCATTA.scr:241-242
    ctx:wait(.5, .5, "5-3") -- TOCATTA.scr:243
    do return ctx:exit("") end -- TOCATTA.scr:245
end

script.labels["5-3"] = function(ctx)
    -- TOCATTA.scr:249
    ctx:object("A1"):trigger("use") -- TOCATTA.scr:252-253
    ctx:wait(.5, .5, "6-3") -- TOCATTA.scr:254
    do return ctx:exit("") end -- TOCATTA.scr:256
end

script.labels["6-3"] = function(ctx)
    -- TOCATTA.scr:259
    ctx:object("G1"):trigger("use") -- TOCATTA.scr:262-263
    ctx:wait(.5, .5, "7-3") -- TOCATTA.scr:264
    do return ctx:exit("") end -- TOCATTA.scr:265
end

script.labels["7-3"] = function(ctx)
    -- TOCATTA.scr:270
    ctx:object("F#1"):trigger("use") -- TOCATTA.scr:273-274
    ctx:wait(1, 1, "8-3") -- TOCATTA.scr:275
    do return ctx:exit("") end -- TOCATTA.scr:277
end

script.labels["8-3"] = function(ctx)
    -- TOCATTA.scr:280
    ctx:object("G1"):trigger("use") -- TOCATTA.scr:283-284
    -- Wait 1.5, C2
    do return ctx:exit("") end -- TOCATTA.scr:286
end

script.labels["Main"] = function(ctx)
    -- TOCATTA.scr:296
    -- TRACEON
    ctx:state().counter = 0 -- TOCATTA.scr:301
    ctx:addTrigger("Play", "OnPlay") -- TOCATTA.scr:302
    do return ctx:exit("") end -- TOCATTA.scr:303
end

return script
