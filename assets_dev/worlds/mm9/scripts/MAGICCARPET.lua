-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MAGICCARPET.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }

-- MagicCarpet.scr
-- by SJR
-- 11-08-01
-- Purpose:to add something cool
-- to DarkPassageway
script.labels["Main"] = function(ctx)
    -- MAGICCARPET.scr:24
    ctx:getParam(0, "nHeight") -- MAGICCARPET.scr:26
    -- GetParam 1, nLiftSpeed
    ctx:onEvent("OnPostStartWorld", "InitMagicCarpet") -- MAGICCARPET.scr:29
    ctx:onEvent("OnPostMiniSaveLoad", "InitMagicCarpet") -- MAGICCARPET.scr:30
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:32
end

script.labels["InitMagicCarpet"] = function(ctx)
    -- MAGICCARPET.scr:35
    ctx:addTrigger("Use", "StartRising") -- MAGICCARPET.scr:37
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- MAGICCARPET.scr:42
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:44
end

script.labels["StartRising"] = function(ctx)
    -- MAGICCARPET.scr:50
    ctx:removeTrigger("Use") -- MAGICCARPET.scr:52
    ctx:state().nVel = 800 -- MAGICCARPET.scr:53
    ctx:state().nVely = 500 -- MAGICCARPET.scr:54
    mm9.gosub(script, ctx, "RiseLoop") -- MAGICCARPET.scr:55
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:56
end

script.labels["RiseLoop"] = function(ctx)
    -- MAGICCARPET.scr:59
    -- check height and obstacle
    if ctx:condition("nVel>0") then -- MAGICCARPET.scr:62
        mm9.gosub(script, ctx, "CheckPOS") -- MAGICCARPET.scr:63
    end -- MAGICCARPET.scr:64
    ctx:state().nVelx, ctx:state().nTemp, ctx:state().nVelz = ctx:player():rotation() -- MAGICCARPET.scr:65
    ctx:state().nVelx, ctx:state().nTemp, ctx:state().nVelz = ctx:vecNorm("nVelx", "nTemp", "nVelz") -- MAGICCARPET.scr:66
    ctx:state().nVelx, ctx:state().nTemp, ctx:state().nVelz = ctx:vecScale("nVelx", "nTemp", "nVelz", "nVel") -- MAGICCARPET.scr:67
    ctx:self():setVelocity("nVelx", "nVely", "nVelz") -- MAGICCARPET.scr:68
    -- tick direction
    ctx:wait(0, .1, "RiseLoop") -- MAGICCARPET.scr:70
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:72
end

script.labels["CheckPOS"] = function(ctx)
    -- MAGICCARPET.scr:82
    ctx:state().xNow, ctx:state().yNow, ctx:state().zNow = ctx:self():pos() -- MAGICCARPET.scr:84
    -- if we got too high, drop
    if ctx:condition("yNow>=nHeight") then -- MAGICCARPET.scr:86
        mm9.gosub(script, ctx, "ResetLift") -- MAGICCARPET.scr:87
        do return ctx:exit("TRUE") end -- MAGICCARPET.scr:88
    end -- MAGICCARPET.scr:89
    ctx:state().dist = ctx:vecDist("xNow", "yNow", "zNow", "xPrev", "yPrev", "zPrev") -- MAGICCARPET.scr:90
    -- if now~prev, then must be stuck, so drop
    if ctx:condition("dist<4") then -- MAGICCARPET.scr:92
        mm9.gosub(script, ctx, "ResetLift") -- MAGICCARPET.scr:93
    end -- MAGICCARPET.scr:94
    -- make prev = now
    ctx:state().xPrev, ctx:state().yPrev, ctx:state().zPrev = ctx:vecScale("xPrev", "yPrev", "zPrev", 0) -- MAGICCARPET.scr:96
    ctx:state().xPrev, ctx:state().yPrev, ctx:state().zPrev = ctx:vecAdd("xPrev", "yPrev", "zPrev", "xNow", "yNow", "zNow") -- MAGICCARPET.scr:97
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:99
end

script.labels["ResetLift"] = function(ctx)
    -- MAGICCARPET.scr:102
    ctx:playSound("sounds\\default.wav", "DoNothing", 1, 500, "FALSE", 100) -- MAGICCARPET.scr:104
    ctx:state().nVely = -4096 -- MAGICCARPET.scr:105
    ctx:state().nVel = 0 -- MAGICCARPET.scr:106
    ctx:addTrigger("Use", "StartRising") -- MAGICCARPET.scr:107
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:109
end

return script
