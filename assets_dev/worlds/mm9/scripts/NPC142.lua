-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC142.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC142.scr
-- timmy
-- handles Skarphedinn Njallssen voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC142.scr:15
    mm9.gosub(script, ctx, "PotionWait") -- NPC142.scr:18
    mm9.gosub(script, ctx, "givePotion") -- NPC142.scr:19
    do return ctx:exit("") end -- NPC142.scr:21
end

script.labels["givePotion"] = function(ctx)
    -- NPC142.scr:24
    if ctx:hasKey(210) then -- NPC142.scr:26-27
        if not ctx:hasKey(373) then -- NPC142.scr:28-29
            ctx:object("RotatingDoor3"):trigger("unlock") -- NPC142.scr:30-31
            ctx:giveItem(558) -- NPC142.scr:32
            ctx:giveKey(373) -- NPC142.scr:33
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC142.scr:34
            do return ctx:exit("") end -- NPC142.scr:35
        end -- NPC142.scr:36
    end -- NPC142.scr:37
    do return ctx:exit("") end -- NPC142.scr:38
end

script.labels["PotionWait"] = function(ctx)
    -- NPC142.scr:41
    -- Nurtigan Quest
    if ctx:hasKey(208) then -- NPC142.scr:47-48
        ctx:takeItem(240) -- NPC142.scr:50
        ctx:getGameTime("nHour", "nMinute") -- NPC142.scr:51
        ctx:set("nHour", "nHour + 2") -- NPC142.scr:52
        ctx:atTime("nHour", "nMinute", "Givekey", "Givekey") -- NPC142.scr:53
        do return ctx:exit("") end -- NPC142.scr:54
    end -- NPC142.scr:55
    -- NOTE: this gives the waiting key outright.
    -- The player should have to wait 2 hrs before getting key
    -- End Nurtigan quest
    do return ctx:exit("") end -- NPC142.scr:62
end

script.labels["Givekey"] = function(ctx)
    -- NPC142.scr:66
    if not ctx:hasKey(209) then -- NPC142.scr:68-69
        ctx:giveKey(209) -- NPC142.scr:70
        do return ctx:exit("") end -- NPC142.scr:71
    end -- NPC142.scr:72
    do return ctx:exit("") end -- NPC142.scr:73
end

script.labels["OnUse"] = function(ctx)
    -- NPC142.scr:76
    if ctx:hasItem(240) then -- NPC142.scr:79-80
        if ctx:hasKey(206) then -- NPC142.scr:81-82
            ctx:giveKey(207) -- NPC142.scr:83
        end -- NPC142.scr:85
    end -- NPC142.scr:86
    ctx:playSound("voices\\NPC\\NPC_142.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC142.scr:88
    do return ctx:exit("") end -- NPC142.scr:89
end

script.labels["OnExit"] = function(ctx)
    -- NPC142.scr:92
    do return ctx:exit("") end -- NPC142.scr:95
end

script.labels["Main"] = function(ctx)
    -- NPC142.scr:98
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC142.scr:105
    ctx:addTrigger("Use", "OnUse") -- NPC142.scr:107
    do return ctx:exit("") end -- NPC142.scr:109
end

return script
