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
    ctx:command("getobjecthandle", "C1, g_hobject") -- DIESIRAE.scr:15
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:16
    ctx:command("wait", ".75, 1") -- DIESIRAE.scr:17
    do return ctx:exit("") end -- DIESIRAE.scr:18
end

script.labels["1"] = function(ctx)
    -- DIESIRAE.scr:21
    ctx:command("getobjecthandle", "B1, g_hobject") -- DIESIRAE.scr:24
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:25
    ctx:command("wait", ".75, 2") -- DIESIRAE.scr:26
    do return ctx:exit("") end -- DIESIRAE.scr:28
end

script.labels["2"] = function(ctx)
    -- DIESIRAE.scr:31
    ctx:command("getobjecthandle", "C1, g_hobject") -- DIESIRAE.scr:34
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:35
    ctx:command("wait", ".75, 3") -- DIESIRAE.scr:36
    do return ctx:exit("") end -- DIESIRAE.scr:38
end

-- RUN DOWN #1
script.labels["3"] = function(ctx)
    -- DIESIRAE.scr:43
    ctx:command("getobjecthandle", "A1, g_hobject") -- DIESIRAE.scr:46
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:47
    ctx:command("wait", ".75, 4") -- DIESIRAE.scr:48
    do return ctx:exit("") end -- DIESIRAE.scr:50
end

script.labels["4"] = function(ctx)
    -- DIESIRAE.scr:53
    ctx:command("getobjecthandle", "B1, g_hobject") -- DIESIRAE.scr:56
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:57
    ctx:command("wait", ".75, 5") -- DIESIRAE.scr:58
    do return ctx:exit("") end -- DIESIRAE.scr:60
end

script.labels["5"] = function(ctx)
    -- DIESIRAE.scr:64
    ctx:command("getobjecthandle", "G1, g_hobject") -- DIESIRAE.scr:67
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:68
    ctx:command("wait", ".75, 6") -- DIESIRAE.scr:69
    do return ctx:exit("") end -- DIESIRAE.scr:71
end

script.labels["6"] = function(ctx)
    -- DIESIRAE.scr:74
    ctx:command("getobjecthandle", "A1, g_hobject") -- DIESIRAE.scr:77
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:78
    ctx:command("wait", ".75, 7") -- DIESIRAE.scr:79
    do return ctx:exit("") end -- DIESIRAE.scr:80
end

script.labels["7"] = function(ctx)
    -- DIESIRAE.scr:85
    ctx:command("getobjecthandle", "A1, g_hobject") -- DIESIRAE.scr:88
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:89
    ctx:command("wait", ".25, 8") -- DIESIRAE.scr:90
    do return ctx:exit("") end -- DIESIRAE.scr:92
end

script.labels["8"] = function(ctx)
    -- DIESIRAE.scr:95
    ctx:command("getobjecthandle", "A1, g_hobject") -- DIESIRAE.scr:98
    ctx:trigger("g_hobject", "use") -- DIESIRAE.scr:99
    -- Wait 1.5, Phrase2
    do return ctx:exit("") end -- DIESIRAE.scr:101
end

script.labels["Main"] = function(ctx)
    -- DIESIRAE.scr:115
    -- TRACEON
    ctx:command("set", "counter, 0") -- DIESIRAE.scr:120
    ctx:addTrigger("Play", "OnPlay") -- DIESIRAE.scr:121
    do return ctx:exit("") end -- DIESIRAE.scr:122
end

return script
