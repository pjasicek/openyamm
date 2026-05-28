-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC55.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "nogold.inc" }

-- NPC55.scr
-- timmy
-- handles Mad Wizard Robinsson voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC55.scr:12
    mm9.gosub(script, ctx, "BlackOrb") -- NPC55.scr:15
    do return ctx:exit("") end -- NPC55.scr:17
end

script.labels["BlackOrb"] = function(ctx)
    -- NPC55.scr:21
    -- BlackOrb Quest
    if not ctx:hasKey(313) then -- NPC55.scr:26-27
        if ctx:hasKey(312) then -- NPC55.scr:28-29
            ctx:command("hasgold", "2000 g_ntemp") -- NPC55.scr:30
            if ctx:condition("g_ntemp==1") then -- NPC55.scr:31
                ctx:command("takegold", "2000") -- NPC55.scr:32
                ctx:giveKey(313) -- NPC55.scr:33
                ctx:giveItem(250) -- NPC55.scr:34
                ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC55.scr:35
                do return ctx:exit("") end -- NPC55.scr:36
            else -- NPC55.scr:37
                ctx:takeKey(312) -- NPC55.scr:38
                mm9.gosub(script, ctx, "NoGold") -- NPC55.scr:39
                -- playsound "you don't have enough"
                do return ctx:exit("") end -- NPC55.scr:41
            end -- NPC55.scr:42
        end -- NPC55.scr:43
    end -- NPC55.scr:44
    do return ctx:exit("") end -- NPC55.scr:45
    -- End BlackOrb quest
    do return ctx:exit("") end -- NPC55.scr:53
end

script.labels["OnUse"] = function(ctx)
    -- NPC55.scr:58
    ctx:command("playsound", "voices\\NPC\\NPC_055.wav, Onexit, 100, 240, FALSE, 100") -- NPC55.scr:61
    ctx:doRude(55) -- NPC55.scr:62
    do return ctx:exit("") end -- NPC55.scr:63
end

script.labels["OnExit"] = function(ctx)
    -- NPC55.scr:66
    do return ctx:exit("") end -- NPC55.scr:69
end

script.labels["Main"] = function(ctx)
    -- NPC55.scr:72
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC55.scr:79
    ctx:addTrigger("Use", "OnUse") -- NPC55.scr:81
    mm9.gosub(script, ctx, "VoiceInit") -- NPC55.scr:82
    do return ctx:exit("") end -- NPC55.scr:83
end

return script
