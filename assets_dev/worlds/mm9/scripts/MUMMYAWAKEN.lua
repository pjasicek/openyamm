-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MUMMYAWAKEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "baseMelee.inc" }

-- MummyAwaken.scr
-- by SJR
-- 11-07-01
-- Purpose:mummy stands still until
-- triggered to be awake
-- ScriptParams:
-- p0 = 1 if you want to trigger next one OnDeath
-- 0 if you want to trigger next one immediately
-- p1 = name of next mummy to trigger
-- p2 = true for laying down, false for standing up
-- p3 = name of coffin to blow up
script.labels["Main"] = function(ctx)
    -- MUMMYAWAKEN.scr:26
    ctx:getParam(0, "bNoChain") -- MUMMYAWAKEN.scr:28
    ctx:getParam(1, "sNextName") -- MUMMYAWAKEN.scr:29
    ctx:command("onpoststartworld", "InitMummyAwaken") -- MUMMYAWAKEN.scr:31
    do return ctx:exit("TRUE") end -- MUMMYAWAKEN.scr:33
end

script.labels["InitMummyAwaken"] = function(ctx)
    -- MUMMYAWAKEN.scr:36
    ctx:command("getmyhandle", "hMe") -- MUMMYAWAKEN.scr:38
    ctx:command("getobjecthandle", "sNextName, hNext") -- MUMMYAWAKEN.scr:40
    if ctx:condition("hNext!=0") then -- MUMMYAWAKEN.scr:41
        ctx:command("createobjectlink", "hNext") -- MUMMYAWAKEN.scr:42
        ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- MUMMYAWAKEN.scr:43
    end -- MUMMYAWAKEN.scr:44
    ctx:command("isclass", "hMe, \"Mummy\", bAnimOk") -- MUMMYAWAKEN.scr:46
    if ctx:condition("bAnimOk==FALSE") then -- MUMMYAWAKEN.scr:47
        ctx:command("isclass", "hMe, \"Zombie\", bAnimOk") -- MUMMYAWAKEN.scr:48
    end -- MUMMYAWAKEN.scr:49
    if ctx:condition("bAnimOk==TRUE") then -- MUMMYAWAKEN.scr:51
        ctx:command("loopanim", "\"coffin\", 0") -- MUMMYAWAKEN.scr:52
    end -- MUMMYAWAKEN.scr:53
    if ctx:condition("bNoChain==TRUE") then -- MUMMYAWAKEN.scr:55
        ctx:command("ondeath", "OnDeath") -- MUMMYAWAKEN.scr:56
    else -- MUMMYAWAKEN.scr:57
        ctx:command("ondeath", "DoNothing") -- MUMMYAWAKEN.scr:58
    end -- MUMMYAWAKEN.scr:59
    ctx:addTrigger("awaken", "WakeUp") -- MUMMYAWAKEN.scr:61
    ctx:command("ondamage", "WakeUp") -- MUMMYAWAKEN.scr:62
    do return ctx:exit("TRUE") end -- MUMMYAWAKEN.scr:64
end

script.labels["WakeUp"] = function(ctx)
    -- MUMMYAWAKEN.scr:67
    -- start attack, setup OnDeath
    ctx:command("removetrigger", "awaken") -- MUMMYAWAKEN.scr:70
    ctx:command("ondamage", "DoNothing") -- MUMMYAWAKEN.scr:71
    mm9.gosub(script, ctx, "BaseInit") -- MUMMYAWAKEN.scr:73
    if ctx:condition("bNoChain==FALSE") then -- MUMMYAWAKEN.scr:75
        mm9.gosub(script, ctx, "OnDeath") -- MUMMYAWAKEN.scr:76
    end -- MUMMYAWAKEN.scr:77
    do return ctx:exit("TRUE") end -- MUMMYAWAKEN.scr:79
end

script.labels["OnDeath"] = function(ctx)
    -- MUMMYAWAKEN.scr:82
    -- trigger next mummy
    if ctx:condition("hNext!=0") then -- MUMMYAWAKEN.scr:85
        ctx:trigger("hNext", "awaken") -- MUMMYAWAKEN.scr:86
    end -- MUMMYAWAKEN.scr:87
    do return ctx:exit("TRUE") end -- MUMMYAWAKEN.scr:89
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- MUMMYAWAKEN.scr:92
    ctx:command("hnext", "= NULL") -- MUMMYAWAKEN.scr:94
    do return ctx:exit("TRUE") end -- MUMMYAWAKEN.scr:96
end

return script
