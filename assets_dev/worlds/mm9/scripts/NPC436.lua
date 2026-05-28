-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC436.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC436.scr
-- timmy
-- handles Boot Camp stuff
script.labels["OnRude"] = function(ctx)
    -- NPC436.scr:12
    if ctx:hasKey(475) then -- NPC436.scr:15-16
        if not ctx:hasKey(496) then -- NPC436.scr:17-18
            ctx:giveItem(589) -- NPC436.scr:19
            ctx:giveItem(298) -- NPC436.scr:20
            ctx:giveItem(302) -- NPC436.scr:21
            ctx:giveKey(496) -- NPC436.scr:22
            do return ctx:exit("") end -- NPC436.scr:23
        end -- NPC436.scr:24
    end -- NPC436.scr:25
    if ctx:hasItem(579) then -- NPC436.scr:27-28
        do return ctx:exit("") end -- NPC436.scr:29
    end -- NPC436.scr:30
    ctx:giveItem(579) -- NPC436.scr:32
    ctx:giveItem(580) -- NPC436.scr:33
    do return ctx:exit("") end -- NPC436.scr:35
end

script.labels["OnUse"] = function(ctx)
    -- NPC436.scr:43
    do return ctx:exit("") end -- NPC436.scr:46
end

script.labels["DoRude"] = function(ctx)
    -- NPC436.scr:49
    if ctx:condition("bSpokeTo==FALSE") then -- NPC436.scr:52
        ctx:command("set", "bSpokeTo, TRUE") -- NPC436.scr:53
        ctx:doRude(436) -- NPC436.scr:54
        ctx:command("playsound", "\\voices\\npc\\NPC_249.wav, DoNothing, 100, 240, FALSE, 100") -- NPC436.scr:55
        do return ctx:exit("") end -- NPC436.scr:56
    end -- NPC436.scr:57
    do return ctx:exit("") end -- NPC436.scr:58
end

script.labels["Init"] = function(ctx)
    -- NPC436.scr:61
    ctx:command("onfoundplayer", "DoRude") -- NPC436.scr:64
    do return ctx:exit("") end -- NPC436.scr:66
end

script.labels["OnLeave"] = function(ctx)
    -- NPC436.scr:69
    ctx:giveKey(473) -- NPC436.scr:72
    do return ctx:exit("") end -- NPC436.scr:74
end

script.labels["Main"] = function(ctx)
    -- NPC436.scr:77
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC436.scr:84
    ctx:addTrigger("Leave", "OnLeave") -- NPC436.scr:85
    ctx:addTrigger("Use", "OnUse") -- NPC436.scr:86
    ctx:command("onpoststartworld", "Init") -- NPC436.scr:87
    ctx:command("onpostminisaveload", "Init") -- NPC436.scr:88
    ctx:command("onpostsaveload", "Init") -- NPC436.scr:89
    ctx:command("wait", "1 .1 Init") -- NPC436.scr:90
    do return ctx:exit("") end -- NPC436.scr:91
end

return script
