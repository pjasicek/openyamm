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
    ctx:onEvent("OnPostStartWorld", "CheckForKey") -- YANMIRKEY.scr:23
    ctx:onEvent("OnPostMiniSaveLoad", "CheckForKey") -- YANMIRKEY.scr:24
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
    ctx:removeTrigger("use") -- YANMIRKEY.scr:42
    ctx:giveItem(570) -- YANMIRKEY.scr:44
    ctx:giveKey(7001) -- YANMIRKEY.scr:45
    mm9.gosub(script, ctx, "UnlockCages") -- YANMIRKEY.scr:47
    mm9.gosub(script, ctx, "RemoveMe") -- YANMIRKEY.scr:48
    do return ctx:exit(1) end -- YANMIRKEY.scr:50
end

script.labels["UnlockCages"] = function(ctx)
    -- YANMIRKEY.scr:53
    -- unlock the teleporter doors
    ctx:object("sDoorRightName"):trigger("unlock") -- YANMIRKEY.scr:56-57
    ctx:object("sDoorLeftName"):trigger("unlock") -- YANMIRKEY.scr:58-59
    -- unlock all the cages
    ctx:object("RotatingDoor61"):trigger("unlock") -- YANMIRKEY.scr:62-63
    ctx:object("RotatingDoor62"):trigger("unlock") -- YANMIRKEY.scr:64-65
    ctx:object("RotatingDoor63"):trigger("unlock") -- YANMIRKEY.scr:66-67
    ctx:object("RotatingDoor64"):trigger("unlock") -- YANMIRKEY.scr:68-69
    ctx:object("RotatingDoor65"):trigger("unlock") -- YANMIRKEY.scr:70-71
    ctx:object("RotatingDoor66"):trigger("unlock") -- YANMIRKEY.scr:72-73
    ctx:object("RotatingDoor67"):trigger("unlock") -- YANMIRKEY.scr:74-75
    do return ctx:exit(1) end -- YANMIRKEY.scr:77
end

script.labels["RemoveMe"] = function(ctx)
    -- YANMIRKEY.scr:80
    ctx:state().hObject = ctx:self() -- YANMIRKEY.scr:82
    ctx:object("hObject"):remove() -- YANMIRKEY.scr:83
    do return ctx:exit(1) end -- YANMIRKEY.scr:85
end

return script
