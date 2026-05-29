-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THRONHEIMCITY_GUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "PoliceMan.inc" }

-- ThronHeimCity_Guard.scr
-- Jeff Leggett
-- 12/19/2001
-- These guards in ThronHeimCity are setup to
-- respawn after their deaths so they can
-- eventually go kill "BadAss"...
script.labels["GetBadAss"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:19
    ctx:state().hBadAss = ctx:objectOrNil("BadAss") -- THRONHEIMCITY_GUARD.scr:22
    if ctx:condition("hBadAss==NULL") then -- THRONHEIMCITY_GUARD.scr:24
        do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:25
    end -- THRONHEIMCITY_GUARD.scr:26
    ctx:set("g_hTarget", "hBadAss") -- THRONHEIMCITY_GUARD.scr:28
    mm9.gosub(script, ctx, "SetupTarget") -- THRONHEIMCITY_GUARD.scr:30
    mm9.gosub(script, ctx, "AggressiveStart") -- THRONHEIMCITY_GUARD.scr:31
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:33
end

script.labels["OnDeath"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:36
    ctx:object("GuardSpawn0"):trigger("Default") -- THRONHEIMCITY_GUARD.scr:38-39
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:40
end

script.labels["GotoSleep"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:43
    ctx:self():loopAnimation("Sleep", 0) -- THRONHEIMCITY_GUARD.scr:45
    ctx:onEvent("OnFoundTarget") -- THRONHEIMCITY_GUARD.scr:46
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:47
end

script.labels["OpenEyes"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:50
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- THRONHEIMCITY_GUARD.scr:52
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:53
end

script.labels["OnDamage"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:56
    -- Don't take our minds off our target...
    ctx:state().g_hObject = ctx:self():target() -- THRONHEIMCITY_GUARD.scr:62
    if ctx:condition("g_hObject==NULL") then -- THRONHEIMCITY_GUARD.scr:64
        do return mm9.gotoLabel(script, ctx, "OnDamage") end -- THRONHEIMCITY_GUARD.scr:65
    else -- THRONHEIMCITY_GUARD.scr:66
        do return mm9.gotoLabel(script, ctx, "OnDamage") end -- THRONHEIMCITY_GUARD.scr:67
    end -- THRONHEIMCITY_GUARD.scr:68
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:71
end

script.labels["Main"] = function(ctx)
    -- THRONHEIMCITY_GUARD.scr:74
    mm9.gosub(script, ctx, "PoliceManInit") -- THRONHEIMCITY_GUARD.scr:77
    ctx:addTrigger("ComeGetMe", "GetBadAss") -- THRONHEIMCITY_GUARD.scr:78
    ctx:addTrigger("OpenEyes", "OpenEyes") -- THRONHEIMCITY_GUARD.scr:79
    ctx:self():addFriend("Honk") -- THRONHEIMCITY_GUARD.scr:81
    ctx:self():setStat("GaveTreasure", "TRUE") -- THRONHEIMCITY_GUARD.scr:83
    ctx:getParam(0, "g_sTemp") -- THRONHEIMCITY_GUARD.scr:85
    if ctx:condition("g_sTemp==GetBadAss") then -- THRONHEIMCITY_GUARD.scr:87
        ctx:wait(1, 0.1, "GetBadAss") -- THRONHEIMCITY_GUARD.scr:88
    else -- THRONHEIMCITY_GUARD.scr:89
        mm9.gosub(script, ctx, "DisableWandering") -- THRONHEIMCITY_GUARD.scr:90
        ctx:wait(1, 0.1, "GotoSleep") -- THRONHEIMCITY_GUARD.scr:91
    end -- THRONHEIMCITY_GUARD.scr:92
    ctx:onEvent("OnDeath", "OnDeath") -- THRONHEIMCITY_GUARD.scr:94
    ctx:state().g_sTemp = ctx:self():name() -- THRONHEIMCITY_GUARD.scr:96
    if ctx:condition("g_sTemp==Guard2") then -- THRONHEIMCITY_GUARD.scr:97
        ctx:debugOut("g_sTemp") -- THRONHEIMCITY_GUARD.scr:98
    end -- THRONHEIMCITY_GUARD.scr:99
    do return ctx:exit("") end -- THRONHEIMCITY_GUARD.scr:101
end

return script
