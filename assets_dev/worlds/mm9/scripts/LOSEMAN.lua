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
    ctx:screenFadeOut(1) -- LOSEMAN.scr:17
    ctx:wait(1, 2, "OnStart") -- LOSEMAN.scr:18
    do return ctx:exit("") end -- LOSEMAN.scr:19
end

script.labels["OnStart"] = function(ctx)
    -- LOSEMAN.scr:22
    ctx:state().g_hobject = ctx:objectOrNil("Losecam1") -- LOSEMAN.scr:25
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- LOSEMAN.scr:27
    do return ctx:exit("") end -- LOSEMAN.scr:29
end

script.labels["OnCam2"] = function(ctx)
    -- LOSEMAN.scr:32
    ctx:screenFadeOut(.5) -- LOSEMAN.scr:36
    ctx:object("losecam1"):trigger("off") -- LOSEMAN.scr:37-38
    ctx:object("losecam2"):trigger("Play") -- LOSEMAN.scr:40-41
    do return ctx:exit("") end -- LOSEMAN.scr:42
end

script.labels["OnCam3"] = function(ctx)
    -- LOSEMAN.scr:45
    ctx:screenFadeOut(.5) -- LOSEMAN.scr:49
    ctx:object("losecam2"):trigger("off") -- LOSEMAN.scr:50-51
    ctx:object("losecam3"):trigger("on") -- LOSEMAN.scr:53-54
    ctx:screenFadeIn(.5) -- LOSEMAN.scr:55
    ctx:wait(1, 1, "Scene3") -- LOSEMAN.scr:56
    do return ctx:exit("") end -- LOSEMAN.scr:57
end

script.labels["Scene3"] = function(ctx)
    -- LOSEMAN.scr:60
    ctx:object("Door0"):trigger("use") -- LOSEMAN.scr:63-64
    ctx:playSound("\\Sounds\\events\\draweropenwood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- LOSEMAN.scr:65
    ctx:wait(1, 1.5, "Speak1") -- LOSEMAN.scr:66
    do return ctx:exit("") end -- LOSEMAN.scr:67
end

script.labels["Speak1"] = function(ctx)
    -- LOSEMAN.scr:70
    ctx:object("hanndl"):trigger("speak") -- LOSEMAN.scr:73-74
    do return ctx:exit("") end -- LOSEMAN.scr:76
end

script.labels["Close"] = function(ctx)
    -- LOSEMAN.scr:80
    ctx:object("Door0"):trigger("use") -- LOSEMAN.scr:83-84
    ctx:playSound("\\Sounds\\events\\draweropenwood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- LOSEMAN.scr:85
    ctx:wait(1, 1, "FadeOut") -- LOSEMAN.scr:86
    do return ctx:exit("") end -- LOSEMAN.scr:87
end

script.labels["FadeOut"] = function(ctx)
    -- LOSEMAN.scr:90
    ctx:screenFadeOut(1) -- LOSEMAN.scr:93
    ctx:wait(1, 4, "fadein") -- LOSEMAN.scr:94
    do return ctx:exit("") end -- LOSEMAN.scr:95
end

script.labels["FadeIn"] = function(ctx)
    -- LOSEMAN.scr:98
    ctx:letterBox("False") -- LOSEMAN.scr:101
    ctx:object("losecam3"):trigger("off") -- LOSEMAN.scr:102-103
    ctx:screenFadeIn(1) -- LOSEMAN.scr:104
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
