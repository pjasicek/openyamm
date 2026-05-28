-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_TARGETRING.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 4, path = "BaseGlobals.inc" }

-- by SJR
script.labels["Main"] = function(ctx)
    -- TH_TARGETRING.scr:16
    ctx:getParam(0, "RING_INDEX") -- TH_TARGETRING.scr:18
    ctx:getParam(1, "PRIZE_LEVEL") -- TH_TARGETRING.scr:19
    ctx:command("key_won", "= KEY_WON + RING_INDEX") -- TH_TARGETRING.scr:21
    ctx:command("getmyhandle", "hMe") -- TH_TARGETRING.scr:23
    ctx:command("ondamage", "OnDamage") -- TH_TARGETRING.scr:25
    ctx:addTrigger("on", "TurnOn") -- TH_TARGETRING.scr:27
    ctx:addTrigger("off", "TurnOff") -- TH_TARGETRING.scr:28
    do return ctx:exit("TRUE") end -- TH_TARGETRING.scr:30
end

script.labels["OnDamage"] = function(ctx)
    -- TH_TARGETRING.scr:33
    ctx:hasKey("KEY_WON", "bHasKey") -- TH_TARGETRING.scr:35
    if ctx:condition("bHasKey==TRUE") then -- TH_TARGETRING.scr:36
        ctx:setConsoleNumVar("TARGET_LEVEL", 0) -- TH_TARGETRING.scr:37
    else -- TH_TARGETRING.scr:38
        ctx:giveKey("KEY_WON") -- TH_TARGETRING.scr:39
        ctx:setConsoleNumVar("TARGET_LEVEL", "PRIZE_LEVEL") -- TH_TARGETRING.scr:40
    end -- TH_TARGETRING.scr:41
    ctx:setConsoleNumVar("TARGET_INDEX", "RING_INDEX") -- TH_TARGETRING.scr:43
    ctx:command("getobjecthandle", "\"TargetMgr\", hMgr") -- TH_TARGETRING.scr:45
    if ctx:condition("hMgr!=0") then -- TH_TARGETRING.scr:47
        ctx:trigger("hMgr", "hit") -- TH_TARGETRING.scr:48
    end -- TH_TARGETRING.scr:49
    do return ctx:exit("TRUE") end -- TH_TARGETRING.scr:51
end

script.labels["TurnOn"] = function(ctx)
    -- TH_TARGETRING.scr:54
    ctx:command("setflag", "hMe, 8192") -- TH_TARGETRING.scr:56
    ctx:command("ondamage", "OnDamage") -- TH_TARGETRING.scr:58
    do return ctx:exit("TRUE") end -- TH_TARGETRING.scr:60
end

script.labels["TurnOff"] = function(ctx)
    -- TH_TARGETRING.scr:63
    ctx:command("clearflag", "hMe, 8192") -- TH_TARGETRING.scr:65
    ctx:command("ondamage", "DoNothing") -- TH_TARGETRING.scr:67
    do return ctx:exit("TRUE") end -- TH_TARGETRING.scr:69
end

return script
