-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STONESPLAYER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "ListMaker.inc" }

-- StonesPlayer.scr
-- by SJR
-- 12-12-01
-- Purpose:
script.labels["Main"] = function(ctx)
    -- STONESPLAYER.scr:16
    ctx:getParam(0, "LISTNAME") -- STONESPLAYER.scr:18
    ctx:getParam(1, "nTemp") -- STONESPLAYER.scr:19
    ctx:state().sMyName = ctx:self():name() -- STONESPLAYER.scr:22
    ctx:setConsoleStrVar("STONES_PLAYER", "sMyName") -- STONESPLAYER.scr:23
    ctx:state().LISTFIRST = 0 -- STONESPLAYER.scr:25
    ctx:set("LISTLAST", "nTemp * nTemp - 1") -- STONESPLAYER.scr:26
    ctx:addTrigger("play", "PlacePiece") -- STONESPLAYER.scr:28
    ctx:addTrigger("use", "OnRudeEnter") -- STONESPLAYER.scr:30
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- STONESPLAYER.scr:31
    do return ctx:exit("TRUE") end -- STONESPLAYER.scr:33
end

script.labels["OnRudeEnter"] = function(ctx)
    -- STONESPLAYER.scr:36
    ctx:giveKey(7002) -- STONESPLAYER.scr:38
    ctx:doRude(428) -- STONESPLAYER.scr:40
    do return ctx:exit("TRUE") end -- STONESPLAYER.scr:42
end

script.labels["OnRudeExit"] = function(ctx)
    -- STONESPLAYER.scr:45
    ctx:takeKey(7002) -- STONESPLAYER.scr:47
    do return ctx:exit("TRUE") end -- STONESPLAYER.scr:49
end

script.labels["PlacePiece"] = function(ctx)
    -- STONESPLAYER.scr:52
    -- try a random square
    ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- STONESPLAYER.scr:55
    mm9.gosub(script, ctx, "GetCurrentObject") -- STONESPLAYER.scr:56
    ctx:trigger("LISTOBJECT", "use") -- STONESPLAYER.scr:58
    do return ctx:exit("TRUE") end -- STONESPLAYER.scr:60
end

return script
