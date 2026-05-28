-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_STEAMWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TM_SteamWater.scr
-- Karl Drown 10-28-01
-- Super simple "Move My World Object" script.
-- Moves a water brush that breaks a board barrier.
script.labels["StopHere"] = function(ctx)
    -- TM_STEAMWATER.scr:20
    ctx:command("hblocker", "= NULL") -- TM_STEAMWATER.scr:22
    ctx:command("getobjecthandle", "ABMineBoards1, hBlocker") -- TM_STEAMWATER.scr:23
    ctx:trigger("hBlocker", "Destroy") -- TM_STEAMWATER.scr:24
    do return ctx:exit("TRUE") end -- TM_STEAMWATER.scr:25
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_STEAMWATER.scr:27
    ctx:command("getobjecthandle", "WaterMarker0, hMCMarker") -- TM_STEAMWATER.scr:29
    ctx:command("getpos", "hMCMarker, nVarX, nVarY, nVarZ") -- TM_STEAMWATER.scr:30
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 1500, StopHere") -- TM_STEAMWATER.scr:31
    do return ctx:exit(1) end -- TM_STEAMWATER.scr:32
end

script.labels["MoveBack"] = function(ctx)
    -- TM_STEAMWATER.scr:34
    ctx:command("getobjecthandle", "WaterMarker1, hMCMarker") -- TM_STEAMWATER.scr:36
    ctx:command("getpos", "hMCMarker, nVarX, nVarY, nVarZ") -- TM_STEAMWATER.scr:37
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 2000, DoNothing") -- TM_STEAMWATER.scr:38
    do return ctx:exit(1) end -- TM_STEAMWATER.scr:39
end

script.labels["Main2"] = function(ctx)
    -- TM_STEAMWATER.scr:41
    ctx:addTrigger("MoveWater", "MoveToMarker") -- TM_STEAMWATER.scr:43
    ctx:addTrigger("ReturnWater", "MoveBack") -- TM_STEAMWATER.scr:44
    do return ctx:exit(1) end -- TM_STEAMWATER.scr:45
end

script.labels["Main"] = function(ctx)
    -- TM_STEAMWATER.scr:47
    ctx:command("wait", "0, 0.1, Main2") -- TM_STEAMWATER.scr:49
    do return ctx:exit("") end -- TM_STEAMWATER.scr:50
end

return script
