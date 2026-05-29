-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_CAGEMONSTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "baseMelee.inc" }

-- DP_CageMonster.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- DP_CAGEMONSTER.scr:14
    ctx:getParam(0, "sDoorName") -- DP_CAGEMONSTER.scr:16
    ctx:onEvent("OnPostStartWorld", "InitCageMonster") -- DP_CAGEMONSTER.scr:18
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:20
end

script.labels["InitCageMonster"] = function(ctx)
    -- DP_CAGEMONSTER.scr:23
    ctx:addTrigger("on", "TurnOn") -- DP_CAGEMONSTER.scr:25
    ctx:addTrigger("off", "TurnOff") -- DP_CAGEMONSTER.scr:26
    ctx:addTrigger("go", "OpenCage") -- DP_CAGEMONSTER.scr:28
    ctx:state().hDoor = ctx:objectOrNil("sDoorName") -- DP_CAGEMONSTER.scr:30
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:32
end

script.labels["OpenCage"] = function(ctx)
    -- DP_CAGEMONSTER.scr:35
    ctx:trigger("hDoor", "unlock") -- DP_CAGEMONSTER.scr:37
    ctx:trigger("hDoor", "use") -- DP_CAGEMONSTER.scr:38
    ctx:state().WAIT_TIME = ctx:object("hDoor"):getStat("DoorOpenTime") -- DP_CAGEMONSTER.scr:40
    ctx:wait(0, "WAIT_TIME", "LeaveCage") -- DP_CAGEMONSTER.scr:42
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:44
end

script.labels["LeaveCage"] = function(ctx)
    -- DP_CAGEMONSTER.scr:47
    mm9.gosub(script, ctx, "BaseInit") -- DP_CAGEMONSTER.scr:49
    ctx:state().g_hTarget = ctx:player() -- DP_CAGEMONSTER.scr:50
    mm9.gosub(script, ctx, "SetupTarget") -- DP_CAGEMONSTER.scr:51
    mm9.gosub(script, ctx, "AggressiveStart") -- DP_CAGEMONSTER.scr:52
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:54
end

script.labels["TurnOn"] = function(ctx)
    -- DP_CAGEMONSTER.scr:57
    ctx:addTrigger("go", "OpenCage") -- DP_CAGEMONSTER.scr:59
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:61
end

script.labels["TurnOff"] = function(ctx)
    -- DP_CAGEMONSTER.scr:64
    ctx:removeTrigger("go") -- DP_CAGEMONSTER.scr:66
    do return ctx:exit("TRUE") end -- DP_CAGEMONSTER.scr:68
end

return script
