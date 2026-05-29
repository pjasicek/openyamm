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
    ctx:state().nFollowPathCount = 1 -- JUNK.scr:35
    ctx:set("sFollowPathTemp", "CameraPath") -- JUNK.scr:36
    ctx:add("sFollowPathTemp", "nFollowPathCount") -- JUNK.scr:37
    ctx:set("g_sOut", "[") -- JUNK.scr:39
    ctx:add("g_sOut", "sFollowPathTemp") -- JUNK.scr:40
    ctx:add("g_sOut", "]-->was not found! Total marker count=>") -- JUNK.scr:41
    ctx:add("g_sOut", "nFollowPathCount") -- JUNK.scr:42
    ctx:debugOut("g_sOut") -- JUNK.scr:44
    do return ctx:exit(1) end -- JUNK.scr:46
end

script.labels["Main"] = function(ctx)
    -- JUNK.scr:48
    ctx:addTrigger("ON", "Trigger_ON") -- JUNK.scr:51
    ctx:state().hMyObject = ctx:self() -- JUNK.scr:53
    ctx:state().nStartPosX, ctx:state().nStartPosY, ctx:state().nStartPosZ = ctx:self():pos() -- JUNK.scr:55
    -- ConsoleCommand ShowFrameRate 1
    do return ctx:exit("") end -- JUNK.scr:60
end

return script
