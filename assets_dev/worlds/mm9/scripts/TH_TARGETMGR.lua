-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_TARGETMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 4, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 5, path = "ListMaker.inc" }

-- by SJR
script.labels["Main"] = function(ctx)
    -- TH_TARGETMGR.scr:13
    ctx:getParam(0, "LISTNAME") -- TH_TARGETMGR.scr:15
    ctx:getParam(1, "LISTFIRST") -- TH_TARGETMGR.scr:16
    ctx:getParam(2, "LISTLAST") -- TH_TARGETMGR.scr:17
    mm9.gosub(script, ctx, "InitTargetMgr") -- TH_TARGETMGR.scr:19
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:21
end

script.labels["InitTargetMgr"] = function(ctx)
    -- TH_TARGETMGR.scr:24
    ctx:setConsoleNumVar("TARGET_LEVEL", 0) -- TH_TARGETMGR.scr:26
    ctx:setConsoleNumVar("TARGET_INDEX", 0) -- TH_TARGETMGR.scr:27
    ctx:addTrigger("hit", "OnTargetHit") -- TH_TARGETMGR.scr:29
    ctx:addTrigger("openall", "RaiseTargets") -- TH_TARGETMGR.scr:31
    ctx:addTrigger("closeall", "LowerTargets") -- TH_TARGETMGR.scr:32
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:34
end

script.labels["OnTargetHit"] = function(ctx)
    -- TH_TARGETMGR.scr:37
    ctx:getConsoleNumVar("TARGET_LEVEL", "PRIZE_LEVEL") -- TH_TARGETMGR.scr:39
    ctx:getConsoleNumVar("TARGET_INDEX", "LISTINDEX") -- TH_TARGETMGR.scr:40
    if ctx:condition("PRIZE_LEVEL>0") then -- TH_TARGETMGR.scr:42
        ctx:playSound("HIT_TARGET", "GiveGold", 1, 5000, "FALSE", 100) -- TH_TARGETMGR.scr:43
    else -- TH_TARGETMGR.scr:44
        ctx:playSound("HIT_TARGET", "DoNothing", 1, 5000, "FALSE", 100) -- TH_TARGETMGR.scr:45
    end -- TH_TARGETMGR.scr:46
    mm9.gosub(script, ctx, "GetCurrentObject") -- TH_TARGETMGR.scr:48
    if ctx:condition("LISTOBJECT!=0") then -- TH_TARGETMGR.scr:49
        ctx:trigger("LISTOBJECT", "open") -- TH_TARGETMGR.scr:50
        ctx:trigger("LISTOBJECT", "lock") -- TH_TARGETMGR.scr:51
    end -- TH_TARGETMGR.scr:52
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:54
end

script.labels["LowerTargets"] = function(ctx)
    -- TH_TARGETMGR.scr:57
    mm9.gosub(script, ctx, "GetFirstObject") -- TH_TARGETMGR.scr:59
    while ctx:condition("LISTINDEX<LISTLAST") do -- TH_TARGETMGR.scr:60
        if ctx:condition("LISTOBJECT!=0") then -- TH_TARGETMGR.scr:61
            ctx:trigger("LISTOBJECT", "open") -- TH_TARGETMGR.scr:62
        end -- TH_TARGETMGR.scr:63
        mm9.gosub(script, ctx, "GetNextObject") -- TH_TARGETMGR.scr:64
    end -- TH_TARGETMGR.scr:65
    if ctx:condition("LISTOBJECT!=0") then -- TH_TARGETMGR.scr:66
        ctx:trigger("LISTOBJECT", "open") -- TH_TARGETMGR.scr:67
    end -- TH_TARGETMGR.scr:68
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:70
end

script.labels["RaiseTargets"] = function(ctx)
    -- TH_TARGETMGR.scr:73
    mm9.gosub(script, ctx, "GetFirstObject") -- TH_TARGETMGR.scr:75
    while ctx:condition("LISTINDEX<LISTLAST") do -- TH_TARGETMGR.scr:76
        if ctx:condition("LISTOBJECT!=0") then -- TH_TARGETMGR.scr:77
            ctx:trigger("LISTOBJECT", "close") -- TH_TARGETMGR.scr:78
        end -- TH_TARGETMGR.scr:79
        mm9.gosub(script, ctx, "GetNextObject") -- TH_TARGETMGR.scr:80
    end -- TH_TARGETMGR.scr:81
    if ctx:condition("LISTOBJECT!=0") then -- TH_TARGETMGR.scr:82
        ctx:trigger("LISTOBJECT", "close") -- TH_TARGETMGR.scr:83
    end -- TH_TARGETMGR.scr:84
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:86
end

script.labels["GiveGold"] = function(ctx)
    -- TH_TARGETMGR.scr:89
    ctx:playSound("WON_MONEY", "DoNothing", 1, 5000, "FALSE", 100) -- TH_TARGETMGR.scr:91
    ctx:giveGold("PRIZE_LEVEL") -- TH_TARGETMGR.scr:93
    do return ctx:exit("TRUE") end -- TH_TARGETMGR.scr:95
end

return script
