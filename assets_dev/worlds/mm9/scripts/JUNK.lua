-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JUNK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- CameraTest.scr
-- Jeff Leggett
-- Parameters:
-- none
-- #include FollowPath.inc
script.labels["Trigger_ON"] = function(ctx)
    -- JUNK.scr:32
    ctx:command("set", "nFollowPathCount, 1") -- JUNK.scr:35
    ctx:command("set", "sFollowPathTemp,CameraPath") -- JUNK.scr:36
    ctx:command("add", "sFollowPathTemp,nFollowPathCount") -- JUNK.scr:37
    ctx:command("set", "g_sOut, [") -- JUNK.scr:39
    ctx:command("add", "g_sOut, sFollowPathTemp") -- JUNK.scr:40
    ctx:command("add", "g_sOut, ]-->was not found! Total marker count=>") -- JUNK.scr:41
    ctx:command("add", "g_sOut, nFollowPathCount") -- JUNK.scr:42
    ctx:command("debugout", "g_sOut") -- JUNK.scr:44
    do return ctx:exit(1) end -- JUNK.scr:46
end

script.labels["Main"] = function(ctx)
    -- JUNK.scr:48
    ctx:addTrigger("ON", "Trigger_ON") -- JUNK.scr:51
    ctx:command("getmyhandle", "hMyObject") -- JUNK.scr:53
    ctx:command("getpos", "hMyObject,nStartPosX,nStartPosY,nStartPosZ") -- JUNK.scr:55
    -- ConsoleCommand ShowFrameRate 1
    do return ctx:exit("") end -- JUNK.scr:60
end

return script
