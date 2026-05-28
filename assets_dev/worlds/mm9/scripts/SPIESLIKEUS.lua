-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPIESLIKEUS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- Spieslikeus.scr
-- By Timmy
-- handles the completion of Spies like us quest.
script.labels["OnRude"] = function(ctx)
    -- SPIESLIKEUS.scr:17
    if not ctx:hasKey(471) then -- SPIESLIKEUS.scr:19-20
        if ctx:hasKey(18) then -- SPIESLIKEUS.scr:21-22
            ctx:giveExp(2000) -- SPIESLIKEUS.scr:23
            ctx:giveGold(500) -- SPIESLIKEUS.scr:24
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- SPIESLIKEUS.scr:25
            ctx:giveKey(471) -- SPIESLIKEUS.scr:26
            do return ctx:exit("") end -- SPIESLIKEUS.scr:27
        end -- SPIESLIKEUS.scr:28
    end -- SPIESLIKEUS.scr:29
    do return ctx:exit("") end -- SPIESLIKEUS.scr:30
end

script.labels["OnUse"] = function(ctx)
    -- SPIESLIKEUS.scr:34
    ctx:command("playsound", "voices\\NPC\\NPC_046.wav, Onexit, 100, 240, FALSE, 100") -- SPIESLIKEUS.scr:37
    do return ctx:exit("") end -- SPIESLIKEUS.scr:38
end

script.labels["OnExit"] = function(ctx)
    -- SPIESLIKEUS.scr:41
    do return ctx:exit("") end -- SPIESLIKEUS.scr:44
end

script.labels["Main"] = function(ctx)
    -- SPIESLIKEUS.scr:47
    -- TraceOn ;delete me!!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- SPIESLIKEUS.scr:51
    ctx:addTrigger("Use", "OnUse") -- SPIESLIKEUS.scr:52
    do return ctx:exit("") end -- SPIESLIKEUS.scr:54
end

return script
