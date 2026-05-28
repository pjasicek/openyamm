-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOSEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- LoseMan.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnLose"] = function(ctx)
    -- LOSEMAN.scr:14
    ctx:command("screenfadeout", "1") -- LOSEMAN.scr:17
    ctx:command("wait", "1 2 OnStart") -- LOSEMAN.scr:18
    do return ctx:exit("") end -- LOSEMAN.scr:19
end

script.labels["OnStart"] = function(ctx)
    -- LOSEMAN.scr:22
    ctx:command("getobjecthandle", "Losecam1 g_hobject") -- LOSEMAN.scr:25
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- LOSEMAN.scr:27
    do return ctx:exit("") end -- LOSEMAN.scr:29
end

script.labels["OnCam2"] = function(ctx)
    -- LOSEMAN.scr:32
    ctx:command("screenfadeout", ".5") -- LOSEMAN.scr:36
    ctx:command("getobjecthandle", "losecam1 g_hobject") -- LOSEMAN.scr:37
    ctx:trigger("g_hobject", "off") -- LOSEMAN.scr:38
    ctx:command("getobjecthandle", "losecam2 g_hobject") -- LOSEMAN.scr:40
    ctx:trigger("g_hobject", "Play") -- LOSEMAN.scr:41
    do return ctx:exit("") end -- LOSEMAN.scr:42
end

script.labels["OnCam3"] = function(ctx)
    -- LOSEMAN.scr:45
    ctx:command("screenfadeout", ".5") -- LOSEMAN.scr:49
    ctx:command("getobjecthandle", "losecam2 g_hobject") -- LOSEMAN.scr:50
    ctx:trigger("g_hobject", "off") -- LOSEMAN.scr:51
    ctx:command("getobjecthandle", "losecam3 g_hobject") -- LOSEMAN.scr:53
    ctx:trigger("g_hobject", "on") -- LOSEMAN.scr:54
    ctx:command("screenfadein", ".5") -- LOSEMAN.scr:55
    ctx:command("wait", "1 1 Scene3") -- LOSEMAN.scr:56
    do return ctx:exit("") end -- LOSEMAN.scr:57
end

script.labels["Scene3"] = function(ctx)
    -- LOSEMAN.scr:60
    ctx:command("getobjecthandle", "Door0 g_hobject") -- LOSEMAN.scr:63
    ctx:trigger("g_hobject", "use") -- LOSEMAN.scr:64
    ctx:command("playsound", "\\Sounds\\events\\draweropenwood.wav, DoNothing, 100, 24000, FALSE, 100") -- LOSEMAN.scr:65
    ctx:command("wait", "1 1.5 Speak1") -- LOSEMAN.scr:66
    do return ctx:exit("") end -- LOSEMAN.scr:67
end

script.labels["Speak1"] = function(ctx)
    -- LOSEMAN.scr:70
    ctx:command("getobjecthandle", "hanndl g_hobject") -- LOSEMAN.scr:73
    ctx:trigger("g_hobject", "speak") -- LOSEMAN.scr:74
    do return ctx:exit("") end -- LOSEMAN.scr:76
end

script.labels["Close"] = function(ctx)
    -- LOSEMAN.scr:80
    ctx:command("getobjecthandle", "Door0 g_hobject") -- LOSEMAN.scr:83
    ctx:trigger("g_hobject", "use") -- LOSEMAN.scr:84
    ctx:command("playsound", "\\Sounds\\events\\draweropenwood.wav, DoNothing, 100, 24000, FALSE, 100") -- LOSEMAN.scr:85
    ctx:command("wait", "1 1 FadeOut") -- LOSEMAN.scr:86
    do return ctx:exit("") end -- LOSEMAN.scr:87
end

script.labels["FadeOut"] = function(ctx)
    -- LOSEMAN.scr:90
    ctx:command("screenfadeout", "1") -- LOSEMAN.scr:93
    ctx:command("wait", "1 4 fadein") -- LOSEMAN.scr:94
    do return ctx:exit("") end -- LOSEMAN.scr:95
end

script.labels["FadeIn"] = function(ctx)
    -- LOSEMAN.scr:98
    ctx:command("letterbox", "False") -- LOSEMAN.scr:101
    ctx:command("getobjecthandle", "losecam3 g_hobject") -- LOSEMAN.scr:102
    ctx:trigger("g_hobject", "off") -- LOSEMAN.scr:103
    ctx:command("screenfadein", "1") -- LOSEMAN.scr:104
    do return ctx:exit("") end -- LOSEMAN.scr:105
end

script.labels["Main"] = function(ctx)
    -- LOSEMAN.scr:108
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Lose", "OnLose") -- LOSEMAN.scr:113
    ctx:addTrigger("Cam2", "OnCam2") -- LOSEMAN.scr:114
    ctx:addTrigger("cam3", "OnCam3") -- LOSEMAN.scr:115
    ctx:addTrigger("FadeOut", "Close") -- LOSEMAN.scr:116
    do return ctx:exit("") end -- LOSEMAN.scr:117
end

return script
