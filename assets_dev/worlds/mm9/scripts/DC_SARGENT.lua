-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DC_SARGENT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "DookHostility.inc" }

-- DC_sargent.scr
-- Brett Yagi
-- Parameters
-- 0 Name of Sleeping Guards w/o number
-- 1 Number of sleeping guards
-- 2 Name of the 2 markers w/o number
-- SJR( added all hostility stuff)
-- endSJR
script.labels["dn"] = function(ctx)
    -- DC_SARGENT.scr:33
    ctx:command("setidle", "") -- DC_SARGENT.scr:35
    do return ctx:exit(1) end -- DC_SARGENT.scr:37
end

script.labels["WakeGuardUp"] = function(ctx)
    -- DC_SARGENT.scr:40
    ctx:command("setidle", "") -- DC_SARGENT.scr:43
    ctx:command("playanim", "aware dn") -- DC_SARGENT.scr:44
    ctx:trigger("hMoveToObject", "WakeUp") -- DC_SARGENT.scr:45
    ctx:command("wait", "0 3 WakeGuards") -- DC_SARGENT.scr:46
    do return ctx:exit(1) end -- DC_SARGENT.scr:48
end

script.labels["WakeGuards"] = function(ctx)
    -- DC_SARGENT.scr:51
    if ctx:condition("nCount < nNumGuards") then -- DC_SARGENT.scr:55
        ctx:command("sguard", "= sGuardName + nCount") -- DC_SARGENT.scr:57
        ctx:command("getobjecthandle", "sGuard hMoveToObject") -- DC_SARGENT.scr:58
        ctx:command("walkto", "hMoveToObject 10 WakeGuardUp") -- DC_SARGENT.scr:59
        ctx:command("ncount", "= nCount + 1") -- DC_SARGENT.scr:60
    else -- DC_SARGENT.scr:62
        ctx:command("smarker", "= sMarkerName + 1") -- DC_SARGENT.scr:64
        ctx:command("getobjecthandle", "sMarker hMoveToObject") -- DC_SARGENT.scr:65
        ctx:command("walkto", "hMoveToObject 10 dn") -- DC_SARGENT.scr:66
    end -- DC_SARGENT.scr:68
    do return ctx:exit(1) end -- DC_SARGENT.scr:70
end

script.labels["StartUp"] = function(ctx)
    -- DC_SARGENT.scr:73
    ctx:command("walkto", "hMoveToObject 10 WakeGuards") -- DC_SARGENT.scr:76
    do return ctx:exit(1) end -- DC_SARGENT.scr:78
end

script.labels["ClearofDoor"] = function(ctx)
    -- DC_SARGENT.scr:81
    ctx:command("ndoor", "= 0") -- DC_SARGENT.scr:84
    do return ctx:exit(1) end -- DC_SARGENT.scr:86
end

script.labels["GoThruDoor"] = function(ctx)
    -- DC_SARGENT.scr:89
    ctx:getParam(0, "hDoor") -- DC_SARGENT.scr:92
    if ctx:condition("nDoor == 0") then -- DC_SARGENT.scr:93
        ctx:command("setidle", "") -- DC_SARGENT.scr:94
        ctx:command("ndoor", "= 1") -- DC_SARGENT.scr:95
        ctx:trigger("hDoor", "use") -- DC_SARGENT.scr:96
        ctx:command("wait", "0 1 StartUp") -- DC_SARGENT.scr:97
        ctx:command("wait", "1 5 ClearofDoor") -- DC_SARGENT.scr:98
    end -- DC_SARGENT.scr:99
    do return ctx:exit(1) end -- DC_SARGENT.scr:101
end

script.labels["Main2"] = function(ctx)
    -- DC_SARGENT.scr:104
    mm9.gosub(script, ctx, "InitDookHostility") -- DC_SARGENT.scr:106
    ctx:command("smarker", "= sMarkerName + 0") -- DC_SARGENT.scr:108
    ctx:command("getobjecthandle", "sMarker hMoveToObject") -- DC_SARGENT.scr:109
    do return ctx:exit(1) end -- DC_SARGENT.scr:111
end

script.labels["Main"] = function(ctx)
    -- DC_SARGENT.scr:114
    ctx:command("ncount", "= 0") -- DC_SARGENT.scr:117
    ctx:getParam(0, "sGuardName") -- DC_SARGENT.scr:118
    ctx:getParam(1, "nNumGuards") -- DC_SARGENT.scr:119
    ctx:getParam(2, "sMarkerName") -- DC_SARGENT.scr:120
    ctx:addTrigger("StartUp", "StartUp") -- DC_SARGENT.scr:122
    ctx:command("ondoor", "GoThruDoor") -- DC_SARGENT.scr:123
    ctx:command("onstuck", "StartUp") -- DC_SARGENT.scr:124
    ctx:command("onpoststartworld", "Main2") -- DC_SARGENT.scr:126
    do return ctx:exit(1) end -- DC_SARGENT.scr:129
end

return script
