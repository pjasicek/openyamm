-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC283.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "MonkHostility.inc" }

-- NPC283.scr
-- timmy
-- handles Leffery Caid's voice and stuff
script.labels["OnRude"] = function(ctx)
    -- NPC283.scr:13
    mm9.gosub(script, ctx, "MissingRelic") -- NPC283.scr:16
    do return ctx:exit("") end -- NPC283.scr:17
end

script.labels["MissingRelic"] = function(ctx)
    -- NPC283.scr:21
    if not ctx:hasKey(342) then -- NPC283.scr:24-25
        if ctx:hasKey(341) then -- NPC283.scr:26-27
            ctx:takeItem(368) -- NPC283.scr:28
            ctx:giveGold(3000) -- NPC283.scr:29
            ctx:giveExp(80000) -- NPC283.scr:30
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- NPC283.scr:31
            ctx:giveKey(342) -- NPC283.scr:32
            do return ctx:exit("") end -- NPC283.scr:33
        end -- NPC283.scr:34
    end -- NPC283.scr:35
    do return ctx:exit("") end -- NPC283.scr:36
end

script.labels["GiveKey"] = function(ctx)
    -- NPC283.scr:39
    if ctx:hasKey(255) then -- NPC283.scr:42-43
        do return ctx:exit("") end -- NPC283.scr:44
    end -- NPC283.scr:45
    if not ctx:hasKey(254) then -- NPC283.scr:47-48
        if ctx:hasKey(253) then -- NPC283.scr:49-50
            ctx:giveKey(254) -- NPC283.scr:51
            ctx:command("getobjecthandle", "CommonerHuman2MaleA1 g_hobject") -- NPC283.scr:52
            ctx:trigger("g_hobject", "Appear") -- NPC283.scr:53
            do return ctx:exit("") end -- NPC283.scr:54
        end -- NPC283.scr:55
    end -- NPC283.scr:56
    do return ctx:exit("") end -- NPC283.scr:57
end

script.labels["OnUse"] = function(ctx)
    -- NPC283.scr:61
    ctx:getParam(0, "g_hobject") -- NPC283.scr:64
    ctx:command("faceobject", "g_hobject 240 DoNothing") -- NPC283.scr:65
    ctx:doRude(283) -- NPC283.scr:66
    ctx:command("playsound", "voices\\NPC\\NPC_283.wav, DoNothing, 100, 240, FALSE, 100") -- NPC283.scr:67
    do return ctx:exit("") end -- NPC283.scr:68
end

script.labels["Init"] = function(ctx)
    -- NPC283.scr:71
    mm9.gosub(script, ctx, "InitMonkHostility") -- NPC283.scr:74
    ctx:command("@m", "5 : 00 Givekey Givekey") -- NPC283.scr:75
    do return ctx:exit("") end -- NPC283.scr:76
end

script.labels["Main"] = function(ctx)
    -- NPC283.scr:79
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC283.scr:85
    ctx:addTrigger("Use", "OnUse") -- NPC283.scr:86
    ctx:command("onpoststartworld", "Init") -- NPC283.scr:89
    ctx:command("onpostminisaveload", "Init") -- NPC283.scr:90
    ctx:command("onpostsaveload", "Init") -- NPC283.scr:91
    ctx:command("wait", "1 .1 Init") -- NPC283.scr:92
    do return ctx:exit("") end -- NPC283.scr:93
end

return script
