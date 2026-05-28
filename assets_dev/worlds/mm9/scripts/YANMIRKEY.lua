-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRKEY.scr"
script.includes = {}
script.labels = {}


-- YanmirKey.scr
-- by SJR
-- 01-16-02
-- Purpose:yanmirs key to unlock
-- the teleporter room
script.labels["Main"] = function(ctx)
    -- YANMIRKEY.scr:16
    ctx:getParam(0, "sDoorRightName") -- YANMIRKEY.scr:18
    ctx:getParam(1, "sDoorLeftName") -- YANMIRKEY.scr:19
    ctx:addTrigger("use", "GiveKeyToPlayer") -- YANMIRKEY.scr:21
    ctx:command("onpoststartworld", "CheckForKey") -- YANMIRKEY.scr:23
    ctx:command("onpostminisaveload", "CheckForKey") -- YANMIRKEY.scr:24
    do return ctx:exit(1) end -- YANMIRKEY.scr:26
end

script.labels["CheckForKey"] = function(ctx)
    -- YANMIRKEY.scr:29
    ctx:hasKey(7001, "bHasKey") -- YANMIRKEY.scr:31
    if ctx:condition("bHasKey==1") then -- YANMIRKEY.scr:32
        mm9.gosub(script, ctx, "UnlockCages") -- YANMIRKEY.scr:33
        mm9.gosub(script, ctx, "RemoveMe") -- YANMIRKEY.scr:34
    end -- YANMIRKEY.scr:35
    do return ctx:exit(1) end -- YANMIRKEY.scr:37
end

script.labels["GiveKeyToPlayer"] = function(ctx)
    -- YANMIRKEY.scr:40
    ctx:command("removetrigger", "use") -- YANMIRKEY.scr:42
    ctx:giveItem(570) -- YANMIRKEY.scr:44
    ctx:giveKey(7001) -- YANMIRKEY.scr:45
    mm9.gosub(script, ctx, "UnlockCages") -- YANMIRKEY.scr:47
    mm9.gosub(script, ctx, "RemoveMe") -- YANMIRKEY.scr:48
    do return ctx:exit(1) end -- YANMIRKEY.scr:50
end

script.labels["UnlockCages"] = function(ctx)
    -- YANMIRKEY.scr:53
    -- unlock the teleporter doors
    ctx:command("getobjecthandle", "sDoorRightName, hObject") -- YANMIRKEY.scr:56
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:57
    ctx:command("getobjecthandle", "sDoorLeftName, hObject") -- YANMIRKEY.scr:58
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:59
    -- unlock all the cages
    ctx:command("getobjecthandle", "RotatingDoor61, hObject") -- YANMIRKEY.scr:62
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:63
    ctx:command("getobjecthandle", "RotatingDoor62, hObject") -- YANMIRKEY.scr:64
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:65
    ctx:command("getobjecthandle", "RotatingDoor63, hObject") -- YANMIRKEY.scr:66
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:67
    ctx:command("getobjecthandle", "RotatingDoor64, hObject") -- YANMIRKEY.scr:68
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:69
    ctx:command("getobjecthandle", "RotatingDoor65, hObject") -- YANMIRKEY.scr:70
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:71
    ctx:command("getobjecthandle", "RotatingDoor66, hObject") -- YANMIRKEY.scr:72
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:73
    ctx:command("getobjecthandle", "RotatingDoor67, hObject") -- YANMIRKEY.scr:74
    ctx:trigger("hObject", "unlock") -- YANMIRKEY.scr:75
    do return ctx:exit(1) end -- YANMIRKEY.scr:77
end

script.labels["RemoveMe"] = function(ctx)
    -- YANMIRKEY.scr:80
    ctx:command("getmyhandle", "hObject") -- YANMIRKEY.scr:82
    ctx:command("removeobject", "hObject") -- YANMIRKEY.scr:83
    do return ctx:exit(1) end -- YANMIRKEY.scr:85
end

return script
