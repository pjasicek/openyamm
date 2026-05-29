-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FLYINGICKY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseFly.inc" }

-- FlyingIcky.scr
-- Jeff Leggett
-- 10/01/2001
-- Custom script for the Flying icky's custom anims
script.labels["IckyDamage"] = function(ctx)
    -- FLYINGICKY.scr:18
    ctx:getParam(0, "g_hTarget") -- FLYINGICKY.scr:21
    ctx:self():setTarget(ctx:object("g_hTarget")) -- FLYINGICKY.scr:22
    mm9.gosub(script, ctx, "IckyLaunch") -- FLYINGICKY.scr:24
    do return ctx:exit("TRUE") end -- FLYINGICKY.scr:26
end

script.labels["Fidget"] = function(ctx)
    -- FLYINGICKY.scr:29
    ctx:self():playAnimation("hangfidget", "FidgetDone") -- FLYINGICKY.scr:32
    ctx:onEvent("OnFoundTarget", "IckyTarget") -- FLYINGICKY.scr:33
    do return ctx:exit("") end -- FLYINGICKY.scr:35
end

script.labels["FidgetDone"] = function(ctx)
    -- FLYINGICKY.scr:38
    if ctx:condition("g_bHanging==FALSE") then -- FLYINGICKY.scr:41
        do return ctx:exit("") end -- FLYINGICKY.scr:42
    end -- FLYINGICKY.scr:43
    ctx:self():loopAnimation("Hang", 0) -- FLYINGICKY.scr:45
    mm9.gosub(script, ctx, "FidgetSetup") -- FLYINGICKY.scr:46
    do return ctx:exit("") end -- FLYINGICKY.scr:48
end

script.labels["FidgetSetup"] = function(ctx)
    -- FLYINGICKY.scr:51
    ctx:onEvent("OnFoundTarget") -- FLYINGICKY.scr:54
    ctx:randomFloat(2, 10, "g_nRandom") -- FLYINGICKY.scr:55
    ctx:wait("FIDGET_WAIT", "g_nRandom", "Fidget") -- FLYINGICKY.scr:57
    do return ctx:exit("") end -- FLYINGICKY.scr:59
end

script.labels["FidgetCancel"] = function(ctx)
    -- FLYINGICKY.scr:62
    ctx:wait("FIDGET_WAIT", 0, "DoNothing") -- FLYINGICKY.scr:65
    do return ctx:exit("") end -- FLYINGICKY.scr:66
end

script.labels["IckyLaunchDone"] = function(ctx)
    -- FLYINGICKY.scr:69
    ctx:self():stop() -- FLYINGICKY.scr:72
    mm9.gosub(script, ctx, "BaseFlyInit") -- FLYINGICKY.scr:74
    -- gosub BaseFlyInitCallbacks
    mm9.gosub(script, ctx, "SetupTarget") -- FLYINGICKY.scr:76
    mm9.gosub(script, ctx, "AggressiveStart") -- FLYINGICKY.scr:77
    do return ctx:exit("") end -- FLYINGICKY.scr:79
end

script.labels["IckyLaunch"] = function(ctx)
    -- FLYINGICKY.scr:82
    ctx:self():moveDir(0, -1, 0, 0, 100) -- FLYINGICKY.scr:85
    mm9.gosub(script, ctx, "FidgetCancel") -- FLYINGICKY.scr:87
    ctx:self():playAnimation("Launch", "IckyLaunchDone") -- FLYINGICKY.scr:89
    do return ctx:exit("") end -- FLYINGICKY.scr:91
end

script.labels["IckyTarget"] = function(ctx)
    -- FLYINGICKY.scr:94
    -- We found a target when we fidgeted...
    ctx:getParam(0, "g_hTarget") -- FLYINGICKY.scr:99
    ctx:self():setTarget(ctx:object("g_hTarget")) -- FLYINGICKY.scr:100
    mm9.gosub(script, ctx, "IckyLaunch") -- FLYINGICKY.scr:102
    do return ctx:exit("") end -- FLYINGICKY.scr:104
end

script.labels["IckyAlert"] = function(ctx)
    -- FLYINGICKY.scr:107
    -- p0 - hAlerter
    -- p1 - hBadGuy
    ctx:getParam(1, "g_hObject") -- FLYINGICKY.scr:114
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- FLYINGICKY.scr:116
    if ctx:condition("g_bTemp==TRUE") then -- FLYINGICKY.scr:118
        do return ctx:exit("") end -- FLYINGICKY.scr:119
    end -- FLYINGICKY.scr:120
    ctx:set("g_hTarget", "g_hObject") -- FLYINGICKY.scr:122
    ctx:self():setTarget(ctx:object("g_hTarget")) -- FLYINGICKY.scr:124
    mm9.gosub(script, ctx, "IckyLaunch") -- FLYINGICKY.scr:125
    do return ctx:exit("") end -- FLYINGICKY.scr:127
end

script.labels["IckyHelp"] = function(ctx)
    -- FLYINGICKY.scr:131
    -- p0 - hPoorSlob
    -- p1 - hBadGuy
    ctx:getParam(0, "g_hObject") -- FLYINGICKY.scr:136
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- FLYINGICKY.scr:138
    if ctx:condition("g_bTemp==FALSE") then -- FLYINGICKY.scr:140
        do return ctx:exit("") end -- FLYINGICKY.scr:141
    end -- FLYINGICKY.scr:142
    ctx:getParam(1, "g_hTarget") -- FLYINGICKY.scr:144
    ctx:self():setTarget(ctx:object("g_hTarget")) -- FLYINGICKY.scr:145
    mm9.gosub(script, ctx, "IckyLaunch") -- FLYINGICKY.scr:147
    do return ctx:exit("") end -- FLYINGICKY.scr:149
end

script.labels["IckyProjectile"] = function(ctx)
    -- FLYINGICKY.scr:153
    ctx:getParam(1, "g_hTarget") -- FLYINGICKY.scr:156
    ctx:self():setTarget(ctx:object("g_hTarget")) -- FLYINGICKY.scr:157
    mm9.gosub(script, ctx, "IckyLaunch") -- FLYINGICKY.scr:158
    do return ctx:exit("") end -- FLYINGICKY.scr:160
end

script.labels["IckyWanderStartup"] = function(ctx)
    -- FLYINGICKY.scr:163
    mm9.gosub(script, ctx, "BaseWanderStartup") -- FLYINGICKY.scr:166
    mm9.gosub(script, ctx, "DisableWandering") -- FLYINGICKY.scr:167
    do return ctx:exit("") end -- FLYINGICKY.scr:169
end

script.labels["AirborneIckyInit"] = function(ctx)
    -- FLYINGICKY.scr:172
    ctx:self():setIdle() -- FLYINGICKY.scr:175
    mm9.gosub(script, ctx, "BaseWanderStartup") -- FLYINGICKY.scr:176
    do return ctx:exit("") end -- FLYINGICKY.scr:178
end

script.labels["BaseWanderGo"] = function(ctx)
    -- FLYINGICKY.scr:181
    ctx:self():setStat("FlyVel", 150) -- FLYINGICKY.scr:183
    mm9.gosub(script, ctx, "BaseWanderGo") -- FLYINGICKY.scr:184
    do return ctx:exit("") end -- FLYINGICKY.scr:185
end

script.labels["BaseWanderStop"] = function(ctx)
    -- FLYINGICKY.scr:188
    mm9.gosub(script, ctx, "BaseWanderStop") -- FLYINGICKY.scr:190
    do return ctx:exit("") end -- FLYINGICKY.scr:191
end

script.labels["Sleep"] = function(ctx)
    -- FLYINGICKY.scr:194
    ctx:onEvent("OnDamage", "IckyDamage") -- FLYINGICKY.scr:196
    ctx:onEvent("OnAlert", "IckyAlert") -- FLYINGICKY.scr:197
    ctx:onEvent("OnHelp", "IckyHelp") -- FLYINGICKY.scr:198
    ctx:onEvent("OnProjectile", "IckyProjectile") -- FLYINGICKY.scr:199
    ctx:onEvent("OnFoundTarget") -- FLYINGICKY.scr:200
    ctx:wait(0, 0.1, "IckyWanderStartup") -- FLYINGICKY.scr:202
    mm9.gosub(script, ctx, "FidgetSetup") -- FLYINGICKY.scr:203
    ctx:self():loopAnimation("Hang", 0) -- FLYINGICKY.scr:204
    do return ctx:exit("") end -- FLYINGICKY.scr:205
end

script.labels["BeAwake"] = function(ctx)
    -- FLYINGICKY.scr:208
    mm9.gosub(script, ctx, "BaseFlyInit") -- FLYINGICKY.scr:210
    ctx:wait(0, 0.1, "AirborneIckyInit") -- FLYINGICKY.scr:211
    do return ctx:exit("") end -- FLYINGICKY.scr:213
end

script.labels["Main"] = function(ctx)
    -- FLYINGICKY.scr:216
    -- The flying icky is supposed to start asleep and
    -- upside-down (like a bat...)
    ctx:getParam(0, "g_nTemp") -- FLYINGICKY.scr:225
    if ctx:condition("g_nTemp==1") then -- FLYINGICKY.scr:227
        -- Force sleeping
        mm9.gosub(script, ctx, "Sleep") -- FLYINGICKY.scr:229
        do return ctx:exit("") end -- FLYINGICKY.scr:230
    else -- FLYINGICKY.scr:231
        if ctx:condition("g_nTemp==2") then -- FLYINGICKY.scr:232
            -- Force Flying
            mm9.gosub(script, ctx, "BeAwake") -- FLYINGICKY.scr:234
            do return ctx:exit("") end -- FLYINGICKY.scr:235
        end -- FLYINGICKY.scr:236
    end -- FLYINGICKY.scr:237
    ctx:state().g_sTemp = ctx:self():className() -- FLYINGICKY.scr:239
    if ctx:condition("g_sTemp==AirborneIcky") then -- FLYINGICKY.scr:241
        mm9.gosub(script, ctx, "BeAwake") -- FLYINGICKY.scr:242
    else -- FLYINGICKY.scr:243
        mm9.gosub(script, ctx, "Sleep") -- FLYINGICKY.scr:244
    end -- FLYINGICKY.scr:245
    do return ctx:exit("") end -- FLYINGICKY.scr:247
end

return script
