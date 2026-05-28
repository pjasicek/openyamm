-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC312.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC309.scr
-- timmy
-- handles mary sheepherder voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC312.scr:12
    if ctx:condition("nTarget==TRUE") then -- NPC312.scr:15
        ctx:command("target", "g_htarget") -- NPC312.scr:16
        ctx:command("ontargetwithindist", "512 RuntoMe") -- NPC312.scr:17
        do return ctx:exit("") end -- NPC312.scr:18
    end -- NPC312.scr:19
    if ctx:hasKey(468) then -- NPC312.scr:21-22
        do return ctx:exit("") end -- NPC312.scr:23
    end -- NPC312.scr:24
    if ctx:hasKey(467) then -- NPC312.scr:27-28
        ctx:giveGold(2) -- NPC312.scr:29
        ctx:giveExp(20000) -- NPC312.scr:30
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC312.scr:31
        ctx:giveKey(468) -- NPC312.scr:32
        do return ctx:exit("") end -- NPC312.scr:33
    end -- NPC312.scr:34
    do return ctx:exit("") end -- NPC312.scr:36
end

script.labels["ONTarget"] = function(ctx)
    -- NPC312.scr:39
    ctx:command("set", "nTarget TRUE") -- NPC312.scr:41
    ctx:getParam(0, "g_htarget") -- NPC312.scr:42
    ctx:command("target", "g_htarget") -- NPC312.scr:43
    ctx:command("ontargetwithindist", "512 RuntoMe") -- NPC312.scr:44
    do return ctx:exit("") end -- NPC312.scr:45
end

script.labels["RuntoMe"] = function(ctx)
    -- NPC312.scr:48
    ctx:trigger("g_htarget", "RuntoMe") -- NPC312.scr:51
    ctx:giveKey(466) -- NPC312.scr:52
    ctx:command("set", "nTarget, False") -- NPC312.scr:53
    do return ctx:exit("") end -- NPC312.scr:54
end

script.labels["OnUse"] = function(ctx)
    -- NPC312.scr:57
    ctx:command("ontargetwithindist", "512 DoNothing") -- NPC312.scr:60
    ctx:command("playsound", "voices\\NPC\\NPC_312.wav, DoNothing, 100, 240, FALSE, 100") -- NPC312.scr:62
    do return ctx:exit("") end -- NPC312.scr:63
end

script.labels["OnLost"] = function(ctx)
    -- NPC312.scr:66
    do return ctx:exit("TRUE") end -- NPC312.scr:70
end

script.labels["Main"] = function(ctx)
    -- NPC312.scr:73
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("onlosttarget", "OnLost") -- NPC312.scr:79
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC312.scr:80
    ctx:addTrigger("Use", "OnUse") -- NPC312.scr:81
    ctx:addTrigger("Target", "ONTarget") -- NPC312.scr:82
    do return ctx:exit("") end -- NPC312.scr:83
end

return script
