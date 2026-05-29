-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_SVEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnAgree"] = function(ctx)
    -- ARG_SVEN.scr:12
    ctx:self():playAnimation("Agree", "Init") -- ARG_SVEN.scr:14
    do return ctx:exit("") end -- ARG_SVEN.scr:15
end

script.labels["OnApplause"] = function(ctx)
    -- ARG_SVEN.scr:18
    ctx:self():playAnimation("Applause", "Init") -- ARG_SVEN.scr:21
    do return ctx:exit("") end -- ARG_SVEN.scr:22
end

script.labels["Init"] = function(ctx)
    -- ARG_SVEN.scr:24
    ctx:self():loopAnimation("Sitting", 0, "DoNothing") -- ARG_SVEN.scr:27
    do return ctx:exit("") end -- ARG_SVEN.scr:28
end

script.labels["Onclap"] = function(ctx)
    -- ARG_SVEN.scr:31
    ctx:randomInt(1, 7, "g_ntemp") -- ARG_SVEN.scr:33
    if ctx:condition("g_ntemp==1") then -- ARG_SVEN.scr:35
        ctx:playSound("\\sounds\\events\\clap01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:36
        do return ctx:exit("") end -- ARG_SVEN.scr:37
    end -- ARG_SVEN.scr:38
    if ctx:condition("g_ntemp==2") then -- ARG_SVEN.scr:40
        ctx:playSound("\\sounds\\events\\clap02.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:41
        do return ctx:exit("") end -- ARG_SVEN.scr:42
    end -- ARG_SVEN.scr:43
    if ctx:condition("g_ntemp==3") then -- ARG_SVEN.scr:45
        ctx:playSound("\\sounds\\events\\clap03.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:46
        do return ctx:exit("") end -- ARG_SVEN.scr:47
    end -- ARG_SVEN.scr:48
    if ctx:condition("g_ntemp==4") then -- ARG_SVEN.scr:50
        ctx:playSound("\\sounds\\events\\clap04.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:51
        do return ctx:exit("") end -- ARG_SVEN.scr:52
    end -- ARG_SVEN.scr:53
    if ctx:condition("g_ntemp==5") then -- ARG_SVEN.scr:55
        ctx:playSound("\\sounds\\events\\clap05.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:56
        do return ctx:exit("") end -- ARG_SVEN.scr:57
    end -- ARG_SVEN.scr:58
    if ctx:condition("g_ntemp==6") then -- ARG_SVEN.scr:60
        ctx:playSound("\\sounds\\events\\clap06.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:61
        do return ctx:exit("") end -- ARG_SVEN.scr:62
    end -- ARG_SVEN.scr:63
    if ctx:condition("g_ntemp==7") then -- ARG_SVEN.scr:65
        ctx:playSound("\\sounds\\events\\clap07.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_SVEN.scr:66
        do return ctx:exit("") end -- ARG_SVEN.scr:67
    end -- ARG_SVEN.scr:68
    do return ctx:exit("") end -- ARG_SVEN.scr:70
end

script.labels["Main"] = function(ctx)
    -- ARG_SVEN.scr:73
    -- TraceOn ;delete me!!
    ctx:onEvent("OnPostStartWorld", "Init") -- ARG_SVEN.scr:77
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ARG_SVEN.scr:78
    ctx:onEvent("OnPostSaveLoad", "Init") -- ARG_SVEN.scr:79
    ctx:wait(1, .1, "Init") -- ARG_SVEN.scr:80
    ctx:addTrigger("Clap", "OnApplause") -- ARG_SVEN.scr:81
    ctx:addModelKey("Clap", "OnClap") -- ARG_SVEN.scr:82
    ctx:addTrigger("Agree", "OnAgree") -- ARG_SVEN.scr:83
    do return ctx:exit("") end -- ARG_SVEN.scr:84
end

return script
