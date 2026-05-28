-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_GUARD1.scr"
script.includes = {}
script.labels = {}


-- DP_Guard1.scr
-- Brett Yagi
-- Works in conjunction with IS_fickyflock.scr.
-- Generic function moves object randomly between markers in parameters
-- When given the "scatter" trigger, it will trigger the "birds"
-- specified in parameters.
-- Parameters
-- 0 - Marker Root name  (ie for Markers Mrk0, Mrk1, Mrk2  "Mrk" is the root name)
-- 1 - Number of Markers
-- 2 - Bird Root name  (ie for Birds Bird0, Bird01, Bird02  "Bird0" is the root name)
-- 3 - Number of Birds
script.labels["dn"] = function(ctx)
    -- DP_GUARD1.scr:38
    do return ctx:exit(1) end -- DP_GUARD1.scr:40
end

script.labels["LockCell"] = function(ctx)
    -- DP_GUARD1.scr:43
    ctx:command("playanim", "Fidget1 dn") -- DP_GUARD1.scr:46
    ctx:command("sguard", "= sGuardNameRoot + 0") -- DP_GUARD1.scr:47
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD1.scr:48
    ctx:trigger("hGuard", "CloseCellDoor") -- DP_GUARD1.scr:49
    ctx:command("ncount", "= nCount + 1") -- DP_GUARD1.scr:50
    ctx:command("target", "NULL 0") -- DP_GUARD1.scr:51
    if ctx:condition("nCount < nNumPrisoners") then -- DP_GUARD1.scr:52
        ctx:command("wait", "0 2 GetPrisoner") -- DP_GUARD1.scr:53
    end -- DP_GUARD1.scr:54
    do return ctx:exit(1) end -- DP_GUARD1.scr:56
end

script.labels["PutPrisonerInCell"] = function(ctx)
    -- DP_GUARD1.scr:60
    ctx:command("setidle", "") -- DP_GUARD1.scr:63
    ctx:command("sguard", "= sGuardNameRoot + 2") -- DP_GUARD1.scr:64
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD1.scr:65
    ctx:trigger("hGuard", "LockDown") -- DP_GUARD1.scr:66
    ctx:command("sguard", "= sGuardNameRoot + 0") -- DP_GUARD1.scr:67
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD1.scr:68
    ctx:trigger("hGuard", "OpenCellDoor") -- DP_GUARD1.scr:69
    ctx:command("sprisoner", "= sPrisonerNameRoot + nCount") -- DP_GUARD1.scr:71
    ctx:command("getobjecthandle", "sPrisoner hPrisoner") -- DP_GUARD1.scr:72
    ctx:command("target", "hPrisoner 1") -- DP_GUARD1.scr:73
    ctx:trigger("hPrisoner", "GetInCell") -- DP_GUARD1.scr:74
    do return ctx:exit(1) end -- DP_GUARD1.scr:76
end

script.labels["ReturnToCell"] = function(ctx)
    -- DP_GUARD1.scr:79
    ctx:command("nmarker", "= nCount * 3 + 4") -- DP_GUARD1.scr:82
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_GUARD1.scr:83
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_GUARD1.scr:84
    ctx:command("walkto", "hMarker 30 PutPrisonerInCell") -- DP_GUARD1.scr:85
    do return ctx:exit(1) end -- DP_GUARD1.scr:87
end

script.labels["GoOutside"] = function(ctx)
    -- DP_GUARD1.scr:92
    ctx:trigger("hDoor", "unlock") -- DP_GUARD1.scr:95
    ctx:trigger("hDoor", "use") -- DP_GUARD1.scr:96
    ctx:command("nmarker", "= 1") -- DP_GUARD1.scr:97
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_GUARD1.scr:98
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_GUARD1.scr:99
    ctx:command("walkto", "hMarker 30 ReturnToCell") -- DP_GUARD1.scr:101
    do return ctx:exit(1) end -- DP_GUARD1.scr:103
end

script.labels["Interrogate"] = function(ctx)
    -- DP_GUARD1.scr:108
    ctx:trigger("hDoor", "use") -- DP_GUARD1.scr:111
    ctx:trigger("hDoor", "lock") -- DP_GUARD1.scr:112
    ctx:command("playsound", "Sounds\\wahoo.wav GoOutside 0 1000 0 30") -- DP_GUARD1.scr:113
    do return ctx:exit(1) end -- DP_GUARD1.scr:116
end

script.labels["GoInside"] = function(ctx)
    -- DP_GUARD1.scr:121
    ctx:command("nmarker", "= 0") -- DP_GUARD1.scr:124
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_GUARD1.scr:125
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_GUARD1.scr:126
    ctx:command("walkto", "hMarker 20 Interrogate") -- DP_GUARD1.scr:128
    do return ctx:exit(1) end -- DP_GUARD1.scr:131
end

script.labels["WalkToIR"] = function(ctx)
    -- DP_GUARD1.scr:135
    ctx:trigger("hGuard", "Follow") -- DP_GUARD1.scr:138
    ctx:trigger("hPrisoner", "Follow") -- DP_GUARD1.scr:139
    ctx:command("nmarker", "= 1") -- DP_GUARD1.scr:141
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_GUARD1.scr:142
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_GUARD1.scr:143
    ctx:command("getobjecthandle", "sDoor hDoor") -- DP_GUARD1.scr:145
    ctx:trigger("hDoor", "unlock") -- DP_GUARD1.scr:146
    ctx:trigger("hDoor", "open") -- DP_GUARD1.scr:147
    ctx:command("walkto", "hMarker 20 GoInside") -- DP_GUARD1.scr:148
    do return ctx:exit(1) end -- DP_GUARD1.scr:151
end

script.labels["OpenCell"] = function(ctx)
    -- DP_GUARD1.scr:155
    ctx:command("playanim", "Fidget1 dn") -- DP_GUARD1.scr:158
    ctx:command("sguard", "= sGuardNameRoot + 0") -- DP_GUARD1.scr:159
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD1.scr:160
    ctx:trigger("hGuard", "OpenCellDoor") -- DP_GUARD1.scr:161
    ctx:command("sprisoner", "= sPrisonerNameRoot + nCount") -- DP_GUARD1.scr:162
    ctx:command("getobjecthandle", "sPrisoner hPrisoner") -- DP_GUARD1.scr:163
    ctx:trigger("hPrisoner", "ExitCell") -- DP_GUARD1.scr:164
    do return ctx:exit(1) end -- DP_GUARD1.scr:166
end

script.labels["GetPrisoner"] = function(ctx)
    -- DP_GUARD1.scr:169
    ctx:command("nmarker", "= nCount * 3 + 2") -- DP_GUARD1.scr:172
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_GUARD1.scr:173
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_GUARD1.scr:174
    ctx:command("sguard", "= sGuardNameRoot + 2") -- DP_GUARD1.scr:175
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD1.scr:176
    ctx:trigger("hGuard", "GoToCell") -- DP_GUARD1.scr:177
    ctx:command("walkto", "hMarker 20 OpenCell") -- DP_GUARD1.scr:178
    do return ctx:exit(1) end -- DP_GUARD1.scr:180
end

script.labels["Main2"] = function(ctx)
    -- DP_GUARD1.scr:183
    -- do normal shit
    do return ctx:exit(1) end -- DP_GUARD1.scr:188
end

script.labels["Main"] = function(ctx)
    -- DP_GUARD1.scr:191
    ctx:getParam(0, "sGuardNameRoot") -- DP_GUARD1.scr:194
    ctx:getParam(1, "sPrisonerNameRoot") -- DP_GUARD1.scr:195
    ctx:getParam(2, "nNumPrisoners") -- DP_GUARD1.scr:196
    ctx:getParam(3, "sMarkerNameRoot") -- DP_GUARD1.scr:197
    ctx:getParam(4, "sDoor") -- DP_GUARD1.scr:198
    ctx:addTrigger("WalkToIR", "WalkToIR") -- DP_GUARD1.scr:200
    ctx:addTrigger("GetPrisoner", "GetPrisoner") -- DP_GUARD1.scr:202
    ctx:addTrigger("LockCell", "LockCell") -- DP_GUARD1.scr:203
    ctx:addTrigger("GoOutside", "GoOutside") -- DP_GUARD1.scr:204
    ctx:command("wait", "0 .1 main2") -- DP_GUARD1.scr:206
    do return ctx:exit(1) end -- DP_GUARD1.scr:209
end

return script
