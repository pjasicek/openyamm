-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENAFIGHTPLAYER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ArenaFightPlayer.scr
-- timmy
-- handles arena monsters fighting player stuff
script.labels["GetOutThere"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:16
    ctx:state().g_hobject = ctx:objectOrNil("marker2") -- ARENAFIGHTPLAYER.scr:18
    ctx:self():runTo(ctx:object("g_hobject"), 128, "OnArrive") -- ARENAFIGHTPLAYER.scr:19
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- ARENAFIGHTPLAYER.scr:20
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:22
end

script.labels["Startup"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:25
    ctx:state().g_ntemp = ctx:self():getStat("HitPoints") -- ARENAFIGHTPLAYER.scr:28
    ctx:set("nMinHP", "g_ntemp * .7") -- ARENAFIGHTPLAYER.scr:29
    ctx:set("nMaxHP", "g_ntemp * 1.5") -- ARENAFIGHTPLAYER.scr:30
    ctx:randomInt("nMinHP", "nMaxHP", "nHitPoints") -- ARENAFIGHTPLAYER.scr:31
    ctx:self():setStat("Hitpoints", "nHitPoints") -- ARENAFIGHTPLAYER.scr:32
    ctx:self():setStat("GaveTreasure", "TRUE") -- ARENAFIGHTPLAYER.scr:33
    ctx:object("RotatingDoor2"):trigger("Use") -- ARENAFIGHTPLAYER.scr:35-36
    ctx:object("RotatingDoor4"):trigger("Use") -- ARENAFIGHTPLAYER.scr:38-39
    ctx:wait(24, 0.2, "GetOutThere") -- ARENAFIGHTPLAYER.scr:41
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:43
end

script.labels["OnArrive"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:46
    ctx:state().g_hObject = ctx:player() -- ARENAFIGHTPLAYER.scr:50
    ctx:self():setTarget(ctx:object("g_hObject")) -- ARENAFIGHTPLAYER.scr:52
    ctx:state().sScript = ctx:self():stringProperty("ScriptName") -- ARENAFIGHTPLAYER.scr:54
    ctx:runScript("sScript") -- ARENAFIGHTPLAYER.scr:55
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:56
end

script.labels["OnFoundTarget"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:59
    do return mm9.gotoLabel(script, ctx, "OnArrive") end -- ARENAFIGHTPLAYER.scr:61
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:63
end

script.labels["WaitForSignal"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:66
    ctx:getConsoleNumVar("WaitingForPlayer", "bWaitingForPlayer") -- ARENAFIGHTPLAYER.scr:70
    if ctx:condition("bWaitingForPlayer==FALSE") then -- ARENAFIGHTPLAYER.scr:72
        do return mm9.gotoLabel(script, ctx, "Startup") end -- ARENAFIGHTPLAYER.scr:73
        do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:74
    end -- ARENAFIGHTPLAYER.scr:75
    ctx:wait(24, 1.5, "WaitForSignal") -- ARENAFIGHTPLAYER.scr:77
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:79
end

script.labels["Main"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:82
    ctx:self():addFriend("AIBase") -- ARENAFIGHTPLAYER.scr:87
    ctx:self():addEnemy("Player") -- ARENAFIGHTPLAYER.scr:88
    -- traceon
    -- Don't Forget to Delete this!
    ctx:giveKey(1011) -- ARENAFIGHTPLAYER.scr:92
    ctx:self():setStringProperty("DeathTriggerTarget", "ArenaFight") -- ARENAFIGHTPLAYER.scr:94
    ctx:self():setStringProperty("DeathTriggerMessage", "Dead") -- ARENAFIGHTPLAYER.scr:95
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- ARENAFIGHTPLAYER.scr:97
    ctx:cacheScript("g_sTemp") -- ARENAFIGHTPLAYER.scr:98
    mm9.gosub(script, ctx, "WaitForSignal") -- ARENAFIGHTPLAYER.scr:100
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:104
end

return script
