-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STURMGAARDINN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "nogold.inc" }

-- sturmgaardinn.scr
-- By Timmy
-- handles the Kenneth Wartooth (#57) and breaking his window
-- Parameters
-- P1  # of times animation runs
-- P0  name of animation to loop
script.labels["OnExit"] = function(ctx)
    -- STURMGAARDINN.scr:23
    ctx:hasKey(5000, "keycheck") -- STURMGAARDINN.scr:26
    if ctx:condition("keycheck==1") then -- STURMGAARDINN.scr:28
        ctx:hasKey(5001, "keycheck") -- STURMGAARDINN.scr:29
        if ctx:condition("keycheck==1") then -- STURMGAARDINN.scr:30
            ctx:command("hasgold", "500 g_ntemp") -- STURMGAARDINN.scr:31
            if ctx:condition("g_ntemp==FALSE") then -- STURMGAARDINN.scr:32
                mm9.gosub(script, ctx, "nogold") -- STURMGAARDINN.scr:33
            else -- STURMGAARDINN.scr:34
                ctx:command("takegold", "500") -- STURMGAARDINN.scr:35
                ctx:takeKey(5000) -- STURMGAARDINN.scr:36
                ctx:takeKey(5001) -- STURMGAARDINN.scr:37
                do return ctx:exit("") end -- STURMGAARDINN.scr:38
            end -- STURMGAARDINN.scr:39
        end -- STURMGAARDINN.scr:40
        do return ctx:exit("") end -- STURMGAARDINN.scr:41
    end -- STURMGAARDINN.scr:42
    do return ctx:exit("") end -- STURMGAARDINN.scr:43
end

script.labels["OnBreak"] = function(ctx)
    -- STURMGAARDINN.scr:46
    ctx:giveKey(5000) -- STURMGAARDINN.scr:49
    do return ctx:exit("") end -- STURMGAARDINN.scr:50
end

script.labels["Off"] = function(ctx)
    -- STURMGAARDINN.scr:53
    do return ctx:exit("") end -- STURMGAARDINN.scr:56
end

script.labels["OnUse"] = function(ctx)
    -- STURMGAARDINN.scr:59
    ctx:command("playsound", "voices\\NPC\\NPC_057.wav, Off, 100, 240, FALSE, 100") -- STURMGAARDINN.scr:62
    do return ctx:exit("") end -- STURMGAARDINN.scr:63
end

script.labels["Main"] = function(ctx)
    -- STURMGAARDINN.scr:67
    -- TraceOn ;delete me!!
    ctx:addTrigger("break", "Onbreak") -- STURMGAARDINN.scr:71
    ctx:addTrigger("use", "Onuse") -- STURMGAARDINN.scr:72
    ctx:onRudeExit("Onexit", script.labels["Onexit"]) -- STURMGAARDINN.scr:73
    ctx:command("cachesound", "voices\\NPC\\NPC_057.wav") -- STURMGAARDINN.scr:74
    -- barkeeper animation stuff
    mm9.gosub(script, ctx, "voiceinit") -- STURMGAARDINN.scr:77
    ctx:getParam(0, "Params") -- STURMGAARDINN.scr:78
    ctx:getParam(1, "g_ntemp") -- STURMGAARDINN.scr:79
    ctx:command("loopanim", "Params,g_ntemp Off") -- STURMGAARDINN.scr:80
    -- ExitScript
    do return ctx:exit("") end -- STURMGAARDINN.scr:83
    do return ctx:exit("") end -- STURMGAARDINN.scr:86
end

return script
