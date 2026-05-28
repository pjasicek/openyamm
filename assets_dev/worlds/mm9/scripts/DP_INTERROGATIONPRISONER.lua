-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_INTERROGATIONPRISONER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseMelee.inc" }

-- DP_InterrogationPrisoner.scr
-- kd
-- 10-24-01
-- Simple following guard
-- Nothing slick or fancy
script.labels["DoTheWalk"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:37
    ctx:command("nreset", "= nReset + 1") -- DP_INTERROGATIONPRISONER.scr:40
    if ctx:condition("nCount==0") then -- DP_INTERROGATIONPRISONER.scr:41
        ctx:command("wait", "0, 0.5 LeaveCell") -- DP_INTERROGATIONPRISONER.scr:42
    end -- DP_INTERROGATIONPRISONER.scr:43
    if ctx:condition("nCount==1") then -- DP_INTERROGATIONPRISONER.scr:45
        ctx:command("wait", "0, 0.5 ToTheInterrogation") -- DP_INTERROGATIONPRISONER.scr:46
    end -- DP_INTERROGATIONPRISONER.scr:47
    if ctx:condition("nCount==2") then -- DP_INTERROGATIONPRISONER.scr:49
        ctx:command("wait", "0, 0.5 ToTheWarden") -- DP_INTERROGATIONPRISONER.scr:50
    end -- DP_INTERROGATIONPRISONER.scr:51
    if ctx:condition("nCount==3") then -- DP_INTERROGATIONPRISONER.scr:53
        ctx:command("wait", "0, 0.5 GoInCell") -- DP_INTERROGATIONPRISONER.scr:54
    end -- DP_INTERROGATIONPRISONER.scr:55
    if ctx:condition("nCount==4") then -- DP_INTERROGATIONPRISONER.scr:57
        ctx:command("wait", "0, 0.5 SitStill") -- DP_INTERROGATIONPRISONER.scr:58
    end -- DP_INTERROGATIONPRISONER.scr:59
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:60
end

script.labels["SitStill"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:63
    ctx:command("ncount", "= 0") -- DP_INTERROGATIONPRISONER.scr:65
    ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:66
    ctx:command("playanim", "Cower, DoNothing") -- DP_INTERROGATIONPRISONER.scr:67
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:68
end

script.labels["LeaveCell"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:71
    ctx:command("hmarker", "= NULL") -- DP_INTERROGATIONPRISONER.scr:73
    ctx:command("nmarker", "= 4") -- DP_INTERROGATIONPRISONER.scr:74
    if ctx:condition("sCellMarker==CellMarker0") then -- DP_INTERROGATIONPRISONER.scr:75
        ctx:command("getobjecthandle", "PrisonerPathA4, hMarker") -- DP_INTERROGATIONPRISONER.scr:76
    else -- DP_INTERROGATIONPRISONER.scr:77
        if ctx:condition("sCellMarker==CellMarker1") then -- DP_INTERROGATIONPRISONER.scr:78
            ctx:command("getobjecthandle", "PrisonerPathA5, hMarker") -- DP_INTERROGATIONPRISONER.scr:79
        else -- DP_INTERROGATIONPRISONER.scr:80
            if ctx:condition("sCellMarker==CellMarker2") then -- DP_INTERROGATIONPRISONER.scr:81
                ctx:command("getobjecthandle", "PrisonerPathA6, hMarker") -- DP_INTERROGATIONPRISONER.scr:82
            end -- DP_INTERROGATIONPRISONER.scr:83
        end -- DP_INTERROGATIONPRISONER.scr:84
    end -- DP_INTERROGATIONPRISONER.scr:85
    ctx:command("walkto", "hMarker 10 SignalWardenAgain") -- DP_INTERROGATIONPRISONER.scr:87
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:88
end

script.labels["SignalWardenAgain"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:90
    ctx:command("ncount", "= 1") -- DP_INTERROGATIONPRISONER.scr:92
    ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:93
    ctx:command("wait", "1, 2, DoNothing") -- DP_INTERROGATIONPRISONER.scr:94
    ctx:command("playanim", "Fidget3, DoNothing") -- DP_INTERROGATIONPRISONER.scr:95
    ctx:trigger("hWarden", "CloseCell") -- DP_INTERROGATIONPRISONER.scr:96
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:97
end

script.labels["GoInCell"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:103
    ctx:command("hmarker", "= NULL") -- DP_INTERROGATIONPRISONER.scr:105
    ctx:command("wait", "1, 2, DoNothing") -- DP_INTERROGATIONPRISONER.scr:106
    ctx:command("getobjecthandle", "sCellMarker, hMarker") -- DP_INTERROGATIONPRISONER.scr:107
    ctx:command("walkto", "hMarker 10 SignalWarden") -- DP_INTERROGATIONPRISONER.scr:108
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:109
end

script.labels["SignalWarden"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:112
    ctx:command("ncount", "= 4") -- DP_INTERROGATIONPRISONER.scr:114
    ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:115
    ctx:trigger("hWarden", "CloseCell") -- DP_INTERROGATIONPRISONER.scr:116
    ctx:command("wait", "1, 2, DoNothing") -- DP_INTERROGATIONPRISONER.scr:117
    ctx:command("playanim", "Fidget4, DoNothing") -- DP_INTERROGATIONPRISONER.scr:118
    ctx:command("faceobject", "hCellDoor, 180, DoNothing") -- DP_INTERROGATIONPRISONER.scr:119
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:120
end

script.labels["ToTheWarden"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:124
    ctx:command("ncount", "= 3") -- DP_INTERROGATIONPRISONER.scr:126
    if ctx:condition("nMarker < nNumMarkers") then -- DP_INTERROGATIONPRISONER.scr:127
        ctx:command("nmarker", "= nMarker + 1") -- DP_INTERROGATIONPRISONER.scr:128
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONPRISONER.scr:129
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONPRISONER.scr:130
        ctx:command("walkto", "hMarker 10 ToTheWarden") -- DP_INTERROGATIONPRISONER.scr:131
    else -- DP_INTERROGATIONPRISONER.scr:132
        ctx:command("walkto", "hMarker 10 WalkToLastMarker") -- DP_INTERROGATIONPRISONER.scr:133
    end -- DP_INTERROGATIONPRISONER.scr:134
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:135
end

script.labels["WardenWait"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:137
    ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:139
    ctx:command("playanim", "Fidget2, DoNothing") -- DP_INTERROGATIONPRISONER.scr:140
    ctx:command("wait", "1, 1, DoNothing") -- DP_INTERROGATIONPRISONER.scr:141
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:142
end

script.labels["ToTheInterrogation"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:146
    if ctx:condition("nMarker != 0") then -- DP_INTERROGATIONPRISONER.scr:148
        ctx:command("nmarker", "= nMarker - 1") -- DP_INTERROGATIONPRISONER.scr:149
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONPRISONER.scr:150
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONPRISONER.scr:151
        ctx:command("walkto", "hMarker 10 ToTheInterrogation") -- DP_INTERROGATIONPRISONER.scr:152
    else -- DP_INTERROGATIONPRISONER.scr:153
        mm9.gosub(script, ctx, "InterrogationRoom") -- DP_INTERROGATIONPRISONER.scr:154
    end -- DP_INTERROGATIONPRISONER.scr:155
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:156
end

script.labels["InterrogationRoom"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:158
    if ctx:condition("nReset==5") then -- DP_INTERROGATIONPRISONER.scr:160
        ctx:command("nreset", "= 0") -- DP_INTERROGATIONPRISONER.scr:161
        ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:162
    else -- DP_INTERROGATIONPRISONER.scr:163
        ctx:command("ncount", "= 2") -- DP_INTERROGATIONPRISONER.scr:164
        ctx:command("nmarker", "= 0") -- DP_INTERROGATIONPRISONER.scr:165
        ctx:command("stop", "") -- DP_INTERROGATIONPRISONER.scr:166
        ctx:command("playanim", "Aware, DoNothing") -- DP_INTERROGATIONPRISONER.scr:167
        ctx:command("wait", "1, 15, DoTheWalk") -- DP_INTERROGATIONPRISONER.scr:168
    end -- DP_INTERROGATIONPRISONER.scr:169
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:171
end

script.labels["WalkToLastMarker"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:176
    ctx:command("hmarker", "= NULL") -- DP_INTERROGATIONPRISONER.scr:178
    if ctx:condition("sCellMarker==CellMarker0") then -- DP_INTERROGATIONPRISONER.scr:179
        ctx:command("getobjecthandle", "PrisonerPathA4, hMarker") -- DP_INTERROGATIONPRISONER.scr:180
    else -- DP_INTERROGATIONPRISONER.scr:181
        if ctx:condition("sCellMarker==CellMarker1") then -- DP_INTERROGATIONPRISONER.scr:182
            ctx:command("getobjecthandle", "PrisonerPathA5, hMarker") -- DP_INTERROGATIONPRISONER.scr:183
        else -- DP_INTERROGATIONPRISONER.scr:184
            if ctx:condition("sCellMarker==CellMarker2") then -- DP_INTERROGATIONPRISONER.scr:185
                ctx:command("getobjecthandle", "PrisonerPathA6, hMarker") -- DP_INTERROGATIONPRISONER.scr:186
            end -- DP_INTERROGATIONPRISONER.scr:187
        end -- DP_INTERROGATIONPRISONER.scr:188
    end -- DP_INTERROGATIONPRISONER.scr:189
    ctx:command("walkto", "hMarker 10 WardenWait") -- DP_INTERROGATIONPRISONER.scr:191
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:192
end

script.labels["AlertCall"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:195
    -- If ( == )
    -- PlaySound sounds\VO\Charrrge.wav, DoNothing, 100, 500, FALSE, 90
    -- Else
    -- PlaySound sounds\VO\TheyAreHere.wav, DoNothing, 100, 500, FALSE, 90
    -- endif
    -- Gosub InitBase
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:204
end

script.labels["Main2"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:207
    ctx:command("getobjecthandle", "InterrWarden, hWarden") -- DP_INTERROGATIONPRISONER.scr:210
    ctx:command("getobjecthandle", "sCellDoor, hCellDoor") -- DP_INTERROGATIONPRISONER.scr:211
    ctx:command("nnummarkers", "= nNumMarkers - 2") -- DP_INTERROGATIONPRISONER.scr:212
    ctx:addTrigger("LetsGo", "DoTheWalk") -- DP_INTERROGATIONPRISONER.scr:214
    ctx:addTrigger("Start", "InterrogationRoom") -- DP_INTERROGATIONPRISONER.scr:215
    -- OnFoundTarget AlertCall
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:220
end

script.labels["Main"] = function(ctx)
    -- DP_INTERROGATIONPRISONER.scr:223
    ctx:getParam(0, "sWayPoint") -- DP_INTERROGATIONPRISONER.scr:226
    ctx:getParam(1, "nNumMarkers") -- DP_INTERROGATIONPRISONER.scr:227
    ctx:getParam(2, "sCellMarker") -- DP_INTERROGATIONPRISONER.scr:228
    ctx:getParam(3, "nStartingDirection") -- DP_INTERROGATIONPRISONER.scr:229
    ctx:getParam(4, "sCellDoor") -- DP_INTERROGATIONPRISONER.scr:230
    ctx:getParam(5, "nCount") -- DP_INTERROGATIONPRISONER.scr:231
    ctx:command("wait", "0 .1 main2") -- DP_INTERROGATIONPRISONER.scr:233
    do return ctx:exit(1) end -- DP_INTERROGATIONPRISONER.scr:235
end

return script
