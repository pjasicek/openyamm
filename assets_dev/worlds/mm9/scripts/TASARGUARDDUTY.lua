-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARGUARDDUTY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- TaSarGuardDuty.scr
-- 9/19
-- timmy
-- handles TaSar Academy guard walking to bed
script.labels["OnOffDuty"] = function(ctx)
    -- TASARGUARDDUTY.scr:31
    -- checks to see if the guard is coming or going,
    -- then sends them to the right place
    if ctx:condition("OffDuty==False") then -- TASARGUARDDUTY.scr:36
        if ctx:condition("counter==0") then -- TASARGUARDDUTY.scr:37
            ctx:command("set", "Current_Marker L_Marker") -- TASARGUARDDUTY.scr:38
            do return mm9.gotoLabel(script, ctx, "Walk") end -- TASARGUARDDUTY.scr:39
            do return ctx:exit("") end -- TASARGUARDDUTY.scr:40
        end -- TASARGUARDDUTY.scr:41
        if ctx:condition("counter==1") then -- TASARGUARDDUTY.scr:43
            ctx:command("set", "OffDuty TRUE") -- TASARGUARDDUTY.scr:44
            ctx:command("set", "Current_Marker L_Marker2") -- TASARGUARDDUTY.scr:45
            do return mm9.gotoLabel(script, ctx, "Walk") end -- TASARGUARDDUTY.scr:46
            do return ctx:exit("") end -- TASARGUARDDUTY.scr:48
        end -- TASARGUARDDUTY.scr:49
    else -- TASARGUARDDUTY.scr:50
        if ctx:condition("counter==0") then -- TASARGUARDDUTY.scr:51
            ctx:command("set", "Current_Marker Start_Marker") -- TASARGUARDDUTY.scr:52
            do return mm9.gotoLabel(script, ctx, "Walk") end -- TASARGUARDDUTY.scr:53
            do return ctx:exit("") end -- TASARGUARDDUTY.scr:54
        end -- TASARGUARDDUTY.scr:55
        if ctx:condition("counter==1") then -- TASARGUARDDUTY.scr:57
            ctx:command("getobjecthandle", "Face_Dir g_hobject") -- TASARGUARDDUTY.scr:58
            ctx:command("faceobject", "g_hobject 32 DoNothing") -- TASARGUARDDUTY.scr:59
            ctx:command("set", "OffDuty FALSE") -- TASARGUARDDUTY.scr:60
            do return ctx:exit("") end -- TASARGUARDDUTY.scr:61
        end -- TASARGUARDDUTY.scr:62
    end -- TASARGUARDDUTY.scr:63
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:64
end

script.labels["Walk"] = function(ctx)
    -- TASARGUARDDUTY.scr:68
    -- walks to current marker
    ctx:command("getobjecthandle", "Current_Marker g_hobject") -- TASARGUARDDUTY.scr:72
    ctx:command("walkto", "g_hobject 0 OnArrive") -- TASARGUARDDUTY.scr:73
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:74
end

script.labels["OffDuty"] = function(ctx)
    -- TASARGUARDDUTY.scr:77
    -- missed the go to bed time
    ctx:command("getobjecthandle", "L_Marker2 G_hobject") -- TASARGUARDDUTY.scr:81
    ctx:command("getpos", "g_hobject PosX PosY PosZ") -- TASARGUARDDUTY.scr:82
    ctx:command("getmyhandle", "g_hobject") -- TASARGUARDDUTY.scr:83
    ctx:command("setpos", "g_hobject PosX PosY PosZ") -- TASARGUARDDUTY.scr:84
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:85
end

script.labels["OnArrive"] = function(ctx)
    -- TASARGUARDDUTY.scr:88
    -- made it to marker...going to next
    ctx:command("add", "counter, 1") -- TASARGUARDDUTY.scr:92
    ctx:command("wait", "0 1 OnOffDuty") -- TASARGUARDDUTY.scr:93
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:94
end

script.labels["OnOnDuty"] = function(ctx)
    -- TASARGUARDDUTY.scr:97
    -- if it's time to go to work & I am at work, do nothing
    ctx:command("getmyhandle", "g_hobject") -- TASARGUARDDUTY.scr:102
    ctx:command("getpos", "g_hobject PosX PosY PosZ") -- TASARGUARDDUTY.scr:103
    if ctx:condition("PosX!=StartPosX") then -- TASARGUARDDUTY.scr:104
        do return mm9.gotoLabel(script, ctx, "OnOffDuty") end -- TASARGUARDDUTY.scr:105
        do return ctx:exit("") end -- TASARGUARDDUTY.scr:106
    end -- TASARGUARDDUTY.scr:107
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:109
end

script.labels["OnDuty"] = function(ctx)
    -- TASARGUARDDUTY.scr:111
    -- late to work...teleport there
    ctx:command("getmyhandle", "g_hobject") -- TASARGUARDDUTY.scr:115
    ctx:command("setpos", "g_hobject StartPosX StartPosY StartPosZ") -- TASARGUARDDUTY.scr:116
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:117
end

script.labels["GetPos"] = function(ctx)
    -- TASARGUARDDUTY.scr:120
    -- get my current position.
    ctx:command("getmyhandle", "g_hobject") -- TASARGUARDDUTY.scr:124
    ctx:command("getpos", "g_hobject StartPosX StartPosY StartPosZ") -- TASARGUARDDUTY.scr:125
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:126
end

script.labels["Main"] = function(ctx)
    -- TASARGUARDDUTY.scr:129
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("onstuck", "Walk") -- TASARGUARDDUTY.scr:134
    mm9.gosub(script, ctx, "GetPos") -- TASARGUARDDUTY.scr:137
    ctx:addTrigger("use", "OnOffDuty") -- TASARGUARDDUTY.scr:138
    ctx:getParam(0, "L_Marker") -- TASARGUARDDUTY.scr:139
    ctx:getParam(1, "L_Marker2") -- TASARGUARDDUTY.scr:140
    ctx:getParam(2, "Start_Marker") -- TASARGUARDDUTY.scr:141
    ctx:getParam(3, "L_time") -- TASARGUARDDUTY.scr:142
    ctx:getParam(4, "Face_Dir") -- TASARGUARDDUTY.scr:143
    ctx:command("@m", "20 : L_time OnOffDuty OffDuty") -- TASARGUARDDUTY.scr:145
    ctx:command("@m", "6 : L_Time OnOnDuty OnDuty") -- TASARGUARDDUTY.scr:146
    mm9.gosub(script, ctx, "BaseInit") -- TASARGUARDDUTY.scr:147
    do return ctx:exit("") end -- TASARGUARDDUTY.scr:148
end

return script
