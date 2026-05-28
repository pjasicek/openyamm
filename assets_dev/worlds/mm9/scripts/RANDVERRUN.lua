-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RANDVERRUN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basedoor.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "baserun.inc" }

-- Randverrun.scr
-- By Timmy
-- Makes Randver the Storm (NPC 51) run away
-- after he's exposed himself as a spy
-- flag variables
script.labels["OnRudeExit2"] = function(ctx)
    -- RANDVERRUN.scr:24
    ctx:hasKey(15, "g_ntemp") -- RANDVERRUN.scr:27
    if ctx:condition("g_ntemp==1") then -- RANDVERRUN.scr:29
        if not ctx:hasKey(495) then -- RANDVERRUN.scr:30-31
            ctx:giveKey(495) -- RANDVERRUN.scr:32
            ctx:giveExp(800) -- RANDVERRUN.scr:33
        end -- RANDVERRUN.scr:34
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- RANDVERRUN.scr:35
        -- this is where Randver starts running
        ctx:setPropNumber("DoRude", "False") -- RANDVERRUN.scr:37
        ctx:command("wait", "25,0.1,OnRun") -- RANDVERRUN.scr:38
        -- Gosub OnRun
        do return ctx:exit("TRUE") end -- RANDVERRUN.scr:40
    end -- RANDVERRUN.scr:41
    do return ctx:exit("") end -- RANDVERRUN.scr:43
end

script.labels["OnRun"] = function(ctx)
    -- RANDVERRUN.scr:46
    mm9.gosub(script, ctx, "Basedoorinit") -- RANDVERRUN.scr:49
    ctx:command("getobjecthandle", "RandverHide g_hobject") -- RANDVERRUN.scr:50
    ctx:command("runto", "g_hobject 16 OnRun2") -- RANDVERRUN.scr:51
    -- wait 1 1 OnRun2
    ctx:command("wait", "3 10 Vanish") -- RANDVERRUN.scr:53
    do return ctx:exit("") end -- RANDVERRUN.scr:54
end

script.labels["OnRun2"] = function(ctx)
    -- RANDVERRUN.scr:57
    ctx:command("getplayerhandle", "g_htarget") -- RANDVERRUN.scr:62
    ctx:command("target", "g_hTarget, FALSE") -- RANDVERRUN.scr:64
    ctx:command("g_hrunawaytrigger", "= g_hTarget") -- RANDVERRUN.scr:66
    mm9.gosub(script, ctx, "BaseRunAway") -- RANDVERRUN.scr:68
    do return ctx:exit("TRUE") end -- RANDVERRUN.scr:73
end

script.labels["Vanish"] = function(ctx)
    -- RANDVERRUN.scr:76
    ctx:command("getmyhandle", "g_hmyobject") -- RANDVERRUN.scr:78
    -- play vanish effect here
    ctx:command("doclientfx", "g_hmyObject,Ceffect") -- RANDVERRUN.scr:81
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- RANDVERRUN.scr:82
    ctx:command("wait", "1 1 Vanish2b") -- RANDVERRUN.scr:83
    do return ctx:exit("") end -- RANDVERRUN.scr:84
end

script.labels["Vanish2b"] = function(ctx)
    -- RANDVERRUN.scr:87
    ctx:command("clearflag", "g_hmyobject visible") -- RANDVERRUN.scr:90
    ctx:command("playsound", "\\Sounds\\spells\\townportal.wav, DoNothing, 100, 24000, FALSE, 100") -- RANDVERRUN.scr:91
    ctx:command("wait", "1 1 Vanish2c") -- RANDVERRUN.scr:92
    do return ctx:exit("") end -- RANDVERRUN.scr:93
end

script.labels["Vanish2c"] = function(ctx)
    -- RANDVERRUN.scr:97
    ctx:command("removeobject", "g_hmyobject") -- RANDVERRUN.scr:99
    do return ctx:exit("") end -- RANDVERRUN.scr:100
end

script.labels["OnUse"] = function(ctx)
    -- RANDVERRUN.scr:104
    -- gosub OnRun
    -- Playsound voices\NPC\NPC_051.wav, DoNothing, 100, 240, FALSE, 100
    do return ctx:exit("") end -- RANDVERRUN.scr:109
end

script.labels["Init"] = function(ctx)
    -- RANDVERRUN.scr:112
    if ctx:hasKey(15) then -- RANDVERRUN.scr:115-116
        ctx:command("getmyhandle", "g_hmyobject") -- RANDVERRUN.scr:117
        ctx:command("removeobject", "g_hmyobject") -- RANDVERRUN.scr:118
    end -- RANDVERRUN.scr:119
    do return ctx:exit("") end -- RANDVERRUN.scr:120
end

script.labels["Main"] = function(ctx)
    -- RANDVERRUN.scr:124
    -- TraceOn ;delete me!!
    ctx:addTrigger("run", "OnRudeExit2") -- RANDVERRUN.scr:128
    ctx:onRudeExit("OnRudeExit2", script.labels["OnRudeExit2"]) -- RANDVERRUN.scr:129
    ctx:addTrigger("use", "Onuse") -- RANDVERRUN.scr:130
    mm9.gosub(script, ctx, "BaseRunInit") -- RANDVERRUN.scr:131
    ctx:command("onpoststartworld", "Init") -- RANDVERRUN.scr:133
    ctx:command("onpostminisaveload", "Init") -- RANDVERRUN.scr:134
    ctx:command("onpostsaveload", "Init") -- RANDVERRUN.scr:135
    ctx:command("wait", "1 .1 Init") -- RANDVERRUN.scr:136
    -- OnStuck Stuck
    do return ctx:exit("") end -- RANDVERRUN.scr:138
end

return script
