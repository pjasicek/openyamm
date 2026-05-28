-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HUCKSTERMOD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "ThjorgardGamesCommon.inc" }

-- HucksterMod.scr
-- by SJR
-- Purpose:sells tickets, explains games
script.labels["OnRudeExit"] = function(ctx)
    -- HUCKSTERMOD.scr:13
    -- looks to see if they want to play a game (key 1001)
    -- and takes their gold and gives them the ticket
    ctx:hasKey(1001, "nTemp") -- HUCKSTERMOD.scr:17
    if ctx:condition("nTemp==1") then -- HUCKSTERMOD.scr:18
        ctx:takeKey(1001) -- HUCKSTERMOD.scr:19
        mm9.gosub(script, ctx, "SellGameTicket") -- HUCKSTERMOD.scr:20
    else -- HUCKSTERMOD.scr:21
        ctx:hasKey(1010, "nTemp") -- HUCKSTERMOD.scr:22
        if ctx:condition("nTemp==1") then -- HUCKSTERMOD.scr:23
            ctx:takeKey(1010) -- HUCKSTERMOD.scr:24
            mm9.gosub(script, ctx, "SellBatchTickets") -- HUCKSTERMOD.scr:25
        end -- HUCKSTERMOD.scr:26
    end -- HUCKSTERMOD.scr:27
    do return ctx:exit(0) end -- HUCKSTERMOD.scr:29
end

script.labels["Main"] = function(ctx)
    -- HUCKSTERMOD.scr:32
    ctx:command("oncachefiles", "CacheFiles") -- HUCKSTERMOD.scr:34
    -- register map win type
    ctx:getParam(0, "bGuberland") -- HUCKSTERMOD.scr:37
    if ctx:condition("bGuberland==1") then -- HUCKSTERMOD.scr:38
        ctx:setConsoleNumVar("GUBERLAND_WIN_TYPE", 1) -- HUCKSTERMOD.scr:39
    else -- HUCKSTERMOD.scr:40
        ctx:setConsoleNumVar("GUBERLAND_WIN_TYPE", 0) -- HUCKSTERMOD.scr:41
    end -- HUCKSTERMOD.scr:42
    mm9.gosub(script, ctx, "VoiceInit") -- HUCKSTERMOD.scr:44
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- HUCKSTERMOD.scr:46
    do return ctx:exit(1) end -- HUCKSTERMOD.scr:48
end

script.labels["CacheFiles"] = function(ctx)
    -- HUCKSTERMOD.scr:51
    ctx:command("cachesound", "\"sounds\\events\\dingbell.wav\"") -- HUCKSTERMOD.scr:53
    ctx:command("cachesound", "\"sounds\\events\\gold01.wav\"") -- HUCKSTERMOD.scr:54
    ctx:command("cachesound", "\"sounds\\events\\quest.wav\"") -- HUCKSTERMOD.scr:55
    ctx:command("cachesound", "\"sounds\\door\\doorlock01.wav\"") -- HUCKSTERMOD.scr:56
    ctx:command("cachesound", "\"sounds\\events\\trumpets02.wav\"") -- HUCKSTERMOD.scr:57
    ctx:command("cachesound", "\"sounds\\spells\\bless.wav\"") -- HUCKSTERMOD.scr:58
    do return ctx:exit(1) end -- HUCKSTERMOD.scr:60
end

return script
