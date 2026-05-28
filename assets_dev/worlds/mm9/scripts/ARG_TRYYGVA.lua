-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_TRYYGVA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnAgree"] = function(ctx)
    -- ARG_TRYYGVA.scr:13
    ctx:command("playanim", "Agree Init") -- ARG_TRYYGVA.scr:15
    do return ctx:exit("") end -- ARG_TRYYGVA.scr:16
end

script.labels["OnApplause"] = function(ctx)
    -- ARG_TRYYGVA.scr:18
    ctx:command("playanim", "Applause Init") -- ARG_TRYYGVA.scr:21
    do return ctx:exit("") end -- ARG_TRYYGVA.scr:22
end

script.labels["Init"] = function(ctx)
    -- ARG_TRYYGVA.scr:24
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_TRYYGVA.scr:27
    do return ctx:exit("") end -- ARG_TRYYGVA.scr:28
end

script.labels["Onclap"] = function(ctx)
    -- ARG_TRYYGVA.scr:31
    ctx:command("getrandomint", "1, 7 g_ntemp") -- ARG_TRYYGVA.scr:33
    if ctx:condition("g_ntemp==1") then -- ARG_TRYYGVA.scr:35
        ctx:command("playsound", "\\sounds\\events\\clap01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:36
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:37
    end -- ARG_TRYYGVA.scr:38
    if ctx:condition("g_ntemp==2") then -- ARG_TRYYGVA.scr:40
        ctx:command("playsound", "\\sounds\\events\\clap02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:41
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:42
    end -- ARG_TRYYGVA.scr:43
    if ctx:condition("g_ntemp==3") then -- ARG_TRYYGVA.scr:45
        ctx:command("playsound", "\\sounds\\events\\clap03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:46
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:47
    end -- ARG_TRYYGVA.scr:48
    if ctx:condition("g_ntemp==4") then -- ARG_TRYYGVA.scr:50
        ctx:command("playsound", "\\sounds\\events\\clap04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:51
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:52
    end -- ARG_TRYYGVA.scr:53
    if ctx:condition("g_ntemp==5") then -- ARG_TRYYGVA.scr:55
        ctx:command("playsound", "\\sounds\\events\\clap05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:56
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:57
    end -- ARG_TRYYGVA.scr:58
    if ctx:condition("g_ntemp==6") then -- ARG_TRYYGVA.scr:60
        ctx:command("playsound", "\\sounds\\events\\clap06.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:61
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:62
    end -- ARG_TRYYGVA.scr:63
    if ctx:condition("g_ntemp==7") then -- ARG_TRYYGVA.scr:65
        ctx:command("playsound", "\\sounds\\events\\clap07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_TRYYGVA.scr:66
        do return ctx:exit("") end -- ARG_TRYYGVA.scr:67
    end -- ARG_TRYYGVA.scr:68
    do return ctx:exit("") end -- ARG_TRYYGVA.scr:70
end

script.labels["Main"] = function(ctx)
    -- ARG_TRYYGVA.scr:73
    -- TraceOn ;delete me!!
    ctx:command("onpoststartworld", "Init") -- ARG_TRYYGVA.scr:77
    ctx:command("onpostminisaveload", "Init") -- ARG_TRYYGVA.scr:78
    ctx:command("onpostsaveload", "Init") -- ARG_TRYYGVA.scr:79
    ctx:command("wait", "1 .1 Init") -- ARG_TRYYGVA.scr:80
    ctx:addTrigger("Clap", "ONApplause") -- ARG_TRYYGVA.scr:81
    ctx:command("addmodelkey", "Clap OnClap") -- ARG_TRYYGVA.scr:82
    ctx:addTrigger("Agree", "OnAgree") -- ARG_TRYYGVA.scr:83
    do return ctx:exit("") end -- ARG_TRYYGVA.scr:84
end

return script
