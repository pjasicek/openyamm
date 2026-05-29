-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DIESIRAE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- diesirae.scr
-- timmy
-- Plays diesirae
script.labels["OnPlay"] = function(ctx)
    -- DIESIRAE.scr:12
    ctx:object("C1"):trigger("use") -- DIESIRAE.scr:15-16
    ctx:wait(.75, .75, "1") -- DIESIRAE.scr:17
    do return ctx:exit("") end -- DIESIRAE.scr:18
end

script.labels["1"] = function(ctx)
    -- DIESIRAE.scr:21
    ctx:object("B1"):trigger("use") -- DIESIRAE.scr:24-25
    ctx:wait(.75, .75, "2") -- DIESIRAE.scr:26
    do return ctx:exit("") end -- DIESIRAE.scr:28
end

script.labels["2"] = function(ctx)
    -- DIESIRAE.scr:31
    ctx:object("C1"):trigger("use") -- DIESIRAE.scr:34-35
    ctx:wait(.75, .75, "3") -- DIESIRAE.scr:36
    do return ctx:exit("") end -- DIESIRAE.scr:38
end

-- RUN DOWN #1
script.labels["3"] = function(ctx)
    -- DIESIRAE.scr:43
    ctx:object("A1"):trigger("use") -- DIESIRAE.scr:46-47
    ctx:wait(.75, .75, "4") -- DIESIRAE.scr:48
    do return ctx:exit("") end -- DIESIRAE.scr:50
end

script.labels["4"] = function(ctx)
    -- DIESIRAE.scr:53
    ctx:object("B1"):trigger("use") -- DIESIRAE.scr:56-57
    ctx:wait(.75, .75, "5") -- DIESIRAE.scr:58
    do return ctx:exit("") end -- DIESIRAE.scr:60
end

script.labels["5"] = function(ctx)
    -- DIESIRAE.scr:64
    ctx:object("G1"):trigger("use") -- DIESIRAE.scr:67-68
    ctx:wait(.75, .75, "6") -- DIESIRAE.scr:69
    do return ctx:exit("") end -- DIESIRAE.scr:71
end

script.labels["6"] = function(ctx)
    -- DIESIRAE.scr:74
    ctx:object("A1"):trigger("use") -- DIESIRAE.scr:77-78
    ctx:wait(.75, .75, "7") -- DIESIRAE.scr:79
    do return ctx:exit("") end -- DIESIRAE.scr:80
end

script.labels["7"] = function(ctx)
    -- DIESIRAE.scr:85
    ctx:object("A1"):trigger("use") -- DIESIRAE.scr:88-89
    ctx:wait(.25, .25, "8") -- DIESIRAE.scr:90
    do return ctx:exit("") end -- DIESIRAE.scr:92
end

script.labels["8"] = function(ctx)
    -- DIESIRAE.scr:95
    ctx:object("A1"):trigger("use") -- DIESIRAE.scr:98-99
    -- Wait 1.5, Phrase2
    do return ctx:exit("") end -- DIESIRAE.scr:101
end

script.labels["Main"] = function(ctx)
    -- DIESIRAE.scr:115
    -- TRACEON
    ctx:state().counter = 0 -- DIESIRAE.scr:120
    ctx:addTrigger("Play", "OnPlay") -- DIESIRAE.scr:121
    do return ctx:exit("") end -- DIESIRAE.scr:122
end

return script
