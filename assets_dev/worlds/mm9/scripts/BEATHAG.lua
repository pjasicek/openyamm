-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BEATHAG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "nogold.inc" }

-- beathag.scr
-- By Timmy
-- handles the Kenneth Wartooth (#58) and breaking his window
-- Parameters
-- P1  # of times animation runs
-- P0  name of animation to loop
script.labels["OnExit"] = function(ctx)
    -- BEATHAG.scr:21
    ctx:hasKey(5002, "keycheck") -- BEATHAG.scr:24
    if ctx:condition("keycheck==1") then -- BEATHAG.scr:26
        ctx:hasKey(5003, "keycheck") -- BEATHAG.scr:27
        if ctx:condition("keycheck==1") then -- BEATHAG.scr:28
            ctx:command("hasgold", "700 g_ntemp") -- BEATHAG.scr:29
            if ctx:condition("g_ntemp==FALSE") then -- BEATHAG.scr:30
                mm9.gosub(script, ctx, "nogold") -- BEATHAG.scr:31
            else -- BEATHAG.scr:32
                ctx:command("takegold", "700") -- BEATHAG.scr:33
                ctx:takeKey(5002) -- BEATHAG.scr:34
                ctx:takeKey(5003) -- BEATHAG.scr:35
                do return ctx:exit("") end -- BEATHAG.scr:36
            end -- BEATHAG.scr:37
        end -- BEATHAG.scr:38
        do return ctx:exit("") end -- BEATHAG.scr:39
    end -- BEATHAG.scr:40
    do return ctx:exit("") end -- BEATHAG.scr:41
end

script.labels["OnBreak"] = function(ctx)
    -- BEATHAG.scr:44
    ctx:giveKey(5002) -- BEATHAG.scr:47
    do return ctx:exit("") end -- BEATHAG.scr:48
end

script.labels["Off"] = function(ctx)
    -- BEATHAG.scr:51
    do return ctx:exit("") end -- BEATHAG.scr:54
end

script.labels["OnUse"] = function(ctx)
    -- BEATHAG.scr:57
    ctx:command("playsound", "voices\\NPC\\NPC_058.wav, Off, 100, 240, FALSE, 100") -- BEATHAG.scr:60
    do return ctx:exit("") end -- BEATHAG.scr:61
end

script.labels["Main"] = function(ctx)
    -- BEATHAG.scr:65
    -- TraceOn ;delete me!!
    ctx:addTrigger("break", "Onbreak") -- BEATHAG.scr:69
    ctx:addTrigger("use", "Onuse") -- BEATHAG.scr:70
    ctx:onRudeExit("Onexit", script.labels["Onexit"]) -- BEATHAG.scr:71
    ctx:command("cachesound", "voices\\NPC\\NPC_058.wav") -- BEATHAG.scr:72
    -- barkeeper animation stuff
    ctx:getParam(0, "Params") -- BEATHAG.scr:76
    ctx:getParam(1, "g_ntemp") -- BEATHAG.scr:77
    ctx:command("loopanim", "Params,g_ntemp Off") -- BEATHAG.scr:78
    mm9.gosub(script, ctx, "voiceinit") -- BEATHAG.scr:79
    -- ExitScript
    do return ctx:exit("") end -- BEATHAG.scr:81
    do return ctx:exit("") end -- BEATHAG.scr:84
end

return script
