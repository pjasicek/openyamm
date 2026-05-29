-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKKEY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "flags.inc" }

-- HonkKey.scr
-- by SJR
-- 10-09-01
-- Purpose:take and remove
-- accountant's key
-- to the treasury
-- Triggers:
-- "GetKey" = will remove key
-- "PutKey" = will replace key
-- "Use"    = gives key to player
script.labels["Main"] = function(ctx)
    -- HONKKEY.scr:27
    ctx:getParam(0, "sDoorName") -- HONKKEY.scr:29
    ctx:getParam(1, "sAcctName") -- HONKKEY.scr:30
    ctx:onEvent("OnPostStartWorld", "InitHonkKey") -- HONKKEY.scr:32
    ctx:onEvent("OnPostMiniSaveLoad", "InitHonkKey") -- HONKKEY.scr:33
    do return ctx:exit("TRUE") end -- HONKKEY.scr:35
end

script.labels["InitHonkKey"] = function(ctx)
    -- HONKKEY.scr:38
    ctx:state().hDoor = ctx:objectOrNil("sDoorName") -- HONKKEY.scr:41
    ctx:state().hAcct = ctx:objectOrNil("sAcctName") -- HONKKEY.scr:42
    if ctx:condition("hAcct!=0") then -- HONKKEY.scr:43
        ctx:self():link(ctx:object("hAcct")) -- HONKKEY.scr:44
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- HONKKEY.scr:45
    end -- HONKKEY.scr:46
    ctx:hasKey("KEY_HONKKEY", "bKeyGone") -- HONKKEY.scr:48
    if ctx:condition("bKeyGone==TRUE") then -- HONKKEY.scr:49
        ctx:self():remove() -- HONKKEY.scr:50
        do return ctx:exit("TRUE") end -- HONKKEY.scr:51
    end -- HONKKEY.scr:52
    ctx:addTrigger("use", "GivePlayerKey") -- HONKKEY.scr:54
    ctx:addTrigger("getkey", "RemoveKey") -- HONKKEY.scr:55
    ctx:addTrigger("putkey", "ReplaceKey") -- HONKKEY.scr:56
    do return ctx:exit("TRUE") end -- HONKKEY.scr:58
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- HONKKEY.scr:61
    ctx:state().hAcct = nil -- HONKKEY.scr:63
    do return ctx:exit("TRUE") end -- HONKKEY.scr:65
end

script.labels["GivePlayerKey"] = function(ctx)
    -- HONKKEY.scr:68
    ctx:giveKey("KEY_HONKKEY") -- HONKKEY.scr:70
    ctx:giveItem("ITEM_HONKKEY") -- HONKKEY.scr:71
    ctx:trigger("hDoor", "unlockbuttons") -- HONKKEY.scr:72
    if ctx:condition("hAcct!=0") then -- HONKKEY.scr:74
        ctx:state().bKeyGone = ctx:self():distanceTo(ctx:object("hAcct")) -- HONKKEY.scr:75
        if ctx:condition("bKeyGone<200") then -- HONKKEY.scr:76
            ctx:trigger("hAcct", "stolen") -- HONKKEY.scr:77
        end -- HONKKEY.scr:78
    end -- HONKKEY.scr:79
    ctx:self():remove() -- HONKKEY.scr:81
    do return ctx:exit("TRUE") end -- HONKKEY.scr:83
end

script.labels["RemoveKey"] = function(ctx)
    -- HONKKEY.scr:86
    ctx:self():setFlag("FLAG_VISIBLE", false) -- HONKKEY.scr:88
    ctx:removeTrigger("use") -- HONKKEY.scr:89
    do return ctx:exit("TRUE") end -- HONKKEY.scr:91
end

script.labels["ReplaceKey"] = function(ctx)
    -- HONKKEY.scr:94
    ctx:self():setFlag("FLAG_VISIBLE", true) -- HONKKEY.scr:96
    ctx:addTrigger("use", "GivePlayerKey") -- HONKKEY.scr:97
    do return ctx:exit("TRUE") end -- HONKKEY.scr:99
end

return script
