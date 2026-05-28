-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC141.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC141.scr
-- timmy
-- handles Akl'ai D'orka voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC141.scr:11
    mm9.gosub(script, ctx, "takekeg") -- NPC141.scr:14
    do return ctx:exit("") end -- NPC141.scr:17
end

script.labels["takeKeg"] = function(ctx)
    -- NPC141.scr:24
    -- takeKeg Quest
    if not ctx:hasKey(306) then -- NPC141.scr:30-31
        if ctx:hasKey(304) then -- NPC141.scr:32-33
            ctx:giveKey(306) -- NPC141.scr:34
            ctx:takeItem(249) -- NPC141.scr:35
            ctx:giveGold(500) -- NPC141.scr:36
            ctx:giveExp(5000) -- NPC141.scr:37
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC141.scr:38
            do return ctx:exit("") end -- NPC141.scr:39
        end -- NPC141.scr:40
    end -- NPC141.scr:41
    do return ctx:exit("") end -- NPC141.scr:42
    -- End takeKeg quest
    do return ctx:exit("") end -- NPC141.scr:47
end

script.labels["OnUse"] = function(ctx)
    -- NPC141.scr:54
    ctx:command("playsound", "voices\\NPC\\NPC_141.wav, Onexit, 100, 240, FALSE, 100") -- NPC141.scr:57
    do return ctx:exit("") end -- NPC141.scr:58
end

script.labels["OnExit"] = function(ctx)
    -- NPC141.scr:61
    do return ctx:exit("") end -- NPC141.scr:64
end

script.labels["Main"] = function(ctx)
    -- NPC141.scr:67
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC141.scr:72
    do return ctx:exit("") end -- NPC141.scr:73
end

return script
