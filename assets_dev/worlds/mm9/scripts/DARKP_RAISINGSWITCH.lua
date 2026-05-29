-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_RAISINGSWITCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- DarkP_RaisingSwitch.scr
-- kd
-- 11-9-01
-- Plays animation and then triggers ScriptObject
script.labels["StopHere"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:18
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:20
end

script.labels["TurnSwitchOff"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:23
    ctx:removeTrigger("Use") -- DARKP_RAISINGSWITCH.scr:25
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:26
end

script.labels["TriggerScrObj"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:28
    ctx:trigger("hPuzzleManager", "sMessage") -- DARKP_RAISINGSWITCH.scr:30
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:31
end

script.labels["MoveMe"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:33
    if ctx:condition("sModelType==Banshee") then -- DARKP_RAISINGSWITCH.scr:35
        ctx:self():playAnimation("FidgetAir1", "TriggerScrObj") -- DARKP_RAISINGSWITCH.scr:36
        ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_RAISINGSWITCH.scr:37
    else -- DARKP_RAISINGSWITCH.scr:38
        ctx:self():playAnimation("fidget1", "TriggerScrObj") -- DARKP_RAISINGSWITCH.scr:39
        ctx:playSound("Sounds\\spells\\EnchantItem.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_RAISINGSWITCH.scr:40
    end -- DARKP_RAISINGSWITCH.scr:41
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:43
end

script.labels["Main2"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:45
    ctx:state().hPuzzleManager = ctx:objectOrNil("sPuzzleManager") -- DARKP_RAISINGSWITCH.scr:47
    ctx:addTrigger("Use", "MoveMe") -- DARKP_RAISINGSWITCH.scr:48
    ctx:addTrigger("Stop", "TurnSwitchOff") -- DARKP_RAISINGSWITCH.scr:49
    if ctx:condition("sModelType==Banshee") then -- DARKP_RAISINGSWITCH.scr:51
        ctx:self():playAnimation("awareAir", "StopHere") -- DARKP_RAISINGSWITCH.scr:52
    else -- DARKP_RAISINGSWITCH.scr:53
        ctx:self():playAnimation("fidget1", "StopHere") -- DARKP_RAISINGSWITCH.scr:54
    end -- DARKP_RAISINGSWITCH.scr:55
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:56
end

script.labels["Main"] = function(ctx)
    -- DARKP_RAISINGSWITCH.scr:58
    ctx:getParam(0, "sPuzzleManager") -- DARKP_RAISINGSWITCH.scr:60
    ctx:getParam(1, "sMessage") -- DARKP_RAISINGSWITCH.scr:61
    ctx:getParam(2, "sModelType") -- DARKP_RAISINGSWITCH.scr:62
    ctx:wait(0, .1, "main2") -- DARKP_RAISINGSWITCH.scr:63
    ctx:state().g_hObject = ctx:self() -- DARKP_RAISINGSWITCH.scr:65
    -- Clear DontFollowStandingOn flag.
    ctx:self():setFlag("8388608", false) -- DARKP_RAISINGSWITCH.scr:67
    do return ctx:exit("TRUE") end -- DARKP_RAISINGSWITCH.scr:68
end

return script
