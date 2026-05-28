-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TELEPORTERMULTI.scr"
script.includes = {}
script.labels = {}


-- TeleporterMulti.scr
-- by SJR
-- 01-01-02
-- Purpose:function as a switchable
-- destination teleporter.
script.labels["Main"] = function(ctx)
    -- TELEPORTERMULTI.scr:17
    ctx:addTrigger("update", "UpdateDestination") -- TELEPORTERMULTI.scr:19
    ctx:command("getmyhandle", "hMe") -- TELEPORTERMULTI.scr:21
    ctx:command("ontouchnotify", "OnTouchNotify") -- TELEPORTERMULTI.scr:23
    do return ctx:exit(1) end -- TELEPORTERMULTI.scr:25
end

script.labels["UpdateDestination"] = function(ctx)
    -- TELEPORTERMULTI.scr:28
    ctx:getConsoleStrVar("TELEPORTER_DESTINATION", "DESTINATION_NAME") -- TELEPORTERMULTI.scr:30
    ctx:command("setpropstring", "TeleportDestination, DESTINATION_NAME") -- TELEPORTERMULTI.scr:31
    do return ctx:exit(1) end -- TELEPORTERMULTI.scr:33
end

script.labels["OnTouchNotify"] = function(ctx)
    -- TELEPORTERMULTI.scr:36
    ctx:getParam(0, "hContact") -- TELEPORTERMULTI.scr:38
    ctx:command("isplayer", "hContact, bIsPlayer") -- TELEPORTERMULTI.scr:39
    if ctx:condition("bIsPlayer==1") then -- TELEPORTERMULTI.scr:40
        ctx:command("wait", "0, .5, ResetDestination") -- TELEPORTERMULTI.scr:41
    end -- TELEPORTERMULTI.scr:42
    do return ctx:exit(0) end -- TELEPORTERMULTI.scr:44
end

script.labels["ResetDestination"] = function(ctx)
    -- TELEPORTERMULTI.scr:47
    ctx:trigger("hMe", "off") -- TELEPORTERMULTI.scr:49
    do return ctx:exit(1) end -- TELEPORTERMULTI.scr:51
end

return script
