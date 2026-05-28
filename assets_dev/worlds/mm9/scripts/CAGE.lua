-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- cage.scr
-- John Machin
-- This script will swing a cage when used
-- It will also have a models leg fall off
-- when the cage is swung.;
-- Rotation vars
script.labels["DoFirstRotate"] = function(ctx)
    -- CAGE.scr:35
    if ctx:condition("g_bRotating == TRUE") then -- CAGE.scr:38
        do return ctx:exit("") end -- CAGE.scr:39
    end -- CAGE.scr:40
    ctx:command("set", "g_nRotDegrees, 30") -- CAGE.scr:42
    ctx:command("set", "g_nRotPerSec, 30") -- CAGE.scr:43
    ctx:command("set", "g_bFirstRot, TRUE") -- CAGE.scr:44
    ctx:command("set", "g_faceY, 0") -- CAGE.scr:46
    ctx:command("normalizevector(", "g_faceX, g_faceY, g_faceZ )") -- CAGE.scr:48
    ctx:command("getcrossproduct(", "g_faceX, g_faceY, g_faceZ, g_upX, g_upY, g_upZ, g_rotX, g_rotY, g_rotZ )") -- CAGE.scr:49
    ctx:command("rotate(", "g_rotX, g_rotY, g_rotZ, g_nRotDegrees, g_nRotPerSec, SwingDone )") -- CAGE.scr:50
    ctx:command("set", "g_bRotating, TRUE") -- CAGE.scr:52
    do return ctx:exit("") end -- CAGE.scr:54
end

script.labels["OnUse"] = function(ctx)
    -- CAGE.scr:57
    if ctx:condition("g_bRotating == TRUE") then -- CAGE.scr:59
        do return ctx:exit("") end -- CAGE.scr:60
    end -- CAGE.scr:61
    ctx:getParam(0, "g_hUsedBy") -- CAGE.scr:63
    -- Get the players forward vector drop the Y and normalize
    -- We assume the the force always comes from the X,Z plane
    -- so there is no upward motion
    ctx:command("getfacedir(", "g_hUsedBy, g_faceX, g_faceY, g_faceZ )") -- CAGE.scr:69
    mm9.gosub(script, ctx, "DoFirstRotate") -- CAGE.scr:71
    do return ctx:exit("") end -- CAGE.scr:73
end

script.labels["SwingDone"] = function(ctx)
    -- CAGE.scr:76
    ctx:command("multiply", "g_nRotDegrees, -1") -- CAGE.scr:78
    if ctx:condition("g_bFirstRot == TRUE") then -- CAGE.scr:80
        ctx:command("multiply", "g_nRotDegrees, 2") -- CAGE.scr:81
        ctx:command("set", "g_bFirstRot, FALSE") -- CAGE.scr:82
    end -- CAGE.scr:83
    if ctx:condition("g_nRotDegrees < 0") then -- CAGE.scr:85
        ctx:command("add", "g_nRotDegrees, 5") -- CAGE.scr:86
    else -- CAGE.scr:87
        ctx:command("subtract", "g_nRotDegrees, 5") -- CAGE.scr:88
    end -- CAGE.scr:89
    ctx:command("subtract", "g_nRotPerSec, 2") -- CAGE.scr:91
    if ctx:condition("g_nRotDegrees != 0") then -- CAGE.scr:93
        ctx:command("rotate(", "g_rotX, g_rotY, g_rotZ, g_nRotDegrees, g_nRotPerSec, SwingDone )") -- CAGE.scr:94
    else -- CAGE.scr:95
        ctx:command("set", "g_bRotating, FALSE") -- CAGE.scr:96
        ctx:command("set", "g_bFirstRot, FALSE") -- CAGE.scr:97
    end -- CAGE.scr:98
    do return ctx:exit("") end -- CAGE.scr:100
end

script.labels["OnDamage"] = function(ctx)
    -- CAGE.scr:103
    -- p0 - Who did the damage
    -- p1 - How much damage
    -- p2 - Damage Type code
    -- p3 - DamageDirX
    -- p4 - DamageDirY
    -- p5 - DamageDirZ
    ctx:getParam(3, "g_faceX") -- CAGE.scr:114
    ctx:getParam(4, "g_faceY") -- CAGE.scr:115
    ctx:getParam(5, "g_faceZ") -- CAGE.scr:116
    mm9.gosub(script, ctx, "DoFirstRotate") -- CAGE.scr:118
    do return ctx:exit("") end -- CAGE.scr:120
end

script.labels["Main"] = function(ctx)
    -- CAGE.scr:123
    -- First Get my objects handle
    ctx:command("getmyhandle", "g_hMyObject") -- CAGE.scr:126
    -- Get the position of the object
    ctx:command("getpos(", "g_hMyObject, g_posX, g_posY, g_posZ )") -- CAGE.scr:129
    -- Get the rotation of the object
    ctx:command("getrotation(", "g_hMyObject, g_rotX, g_rotY, g_rotZ, g_nSpin )") -- CAGE.scr:132
    -- Monitor these triggers
    ctx:addTrigger("Use", "OnUse") -- CAGE.scr:135
    ctx:command("ondamage", "OnDamage") -- CAGE.scr:136
    do return ctx:exit("") end -- CAGE.scr:138
end

return script
