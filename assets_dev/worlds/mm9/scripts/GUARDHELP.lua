-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDHELP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "BaseDoor.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "guardsounds.inc" }

-- Guardhelp.scr
-- timmy
-- helps anrito when he calles for help.
script.labels["OnGiveHelp"] = function(ctx)
    -- GUARDHELP.scr:22
    ctx:getParam(0, "g_hobject") -- GUARDHELP.scr:25
    ctx:command("runto", "g_hobject 32 DoNothing") -- GUARDHELP.scr:26
    do return ctx:exit("") end -- GUARDHELP.scr:27
end

script.labels["OnTarget"] = function(ctx)
    -- GUARDHELP.scr:30
    ctx:getParam(0, "hParam") -- GUARDHELP.scr:35
    ctx:command("isplayer", "hParam, bIsPlayer") -- GUARDHELP.scr:36
    ctx:hasKey("nKeyValue", "bHasKey") -- GUARDHELP.scr:37
    ctx:command("bresult", "= bIsPlayer * bHasKey") -- GUARDHELP.scr:38
    if ctx:condition("bResult != TRUE") then -- GUARDHELP.scr:39
        ctx:command("runto", "hParam, 25, BaseInit") -- GUARDHELP.scr:40
    end -- GUARDHELP.scr:41
    do return ctx:exit("TRUE") end -- GUARDHELP.scr:42
end

script.labels["OnDamage"] = function(ctx)
    -- GUARDHELP.scr:46
    ctx:getParam(0, "g_hobject") -- GUARDHELP.scr:50
    ctx:command("isplayer", "g_hobject, bIsPlayer") -- GUARDHELP.scr:51
    if ctx:condition("bIsPlayer==TRUE") then -- GUARDHELP.scr:52
        ctx:giveKey(5006) -- GUARDHELP.scr:53
        ctx:command("removefriend", "Player") -- GUARDHELP.scr:54
        mm9.gosub(script, ctx, "Help") -- GUARDHELP.scr:55
        mm9.gosub(script, ctx, "BaseInit") -- GUARDHELP.scr:56
    else -- GUARDHELP.scr:57
        ctx:command("addfriend", "player") -- GUARDHELP.scr:58
        mm9.gosub(script, ctx, "baseinit") -- GUARDHELP.scr:59
    end -- GUARDHELP.scr:60
    do return ctx:exit("") end -- GUARDHELP.scr:61
end

script.labels["Help"] = function(ctx)
    -- GUARDHELP.scr:64
    ctx:command("getobjecthandle", "Help1 g_hobject") -- GUARDHELP.scr:68
    ctx:trigger("g_hobject", "help") -- GUARDHELP.scr:69
    ctx:command("getobjecthandle", "Help2 g_hobject") -- GUARDHELP.scr:71
    ctx:trigger("g_hobject", "help") -- GUARDHELP.scr:72
    ctx:command("getobjecthandle", "Help3 g_hobject") -- GUARDHELP.scr:74
    ctx:trigger("g_hobject", "help") -- GUARDHELP.scr:75
    do return ctx:exit("") end -- GUARDHELP.scr:77
end

script.labels["OnExit"] = function(ctx)
    -- GUARDHELP.scr:80
    do return ctx:exit("") end -- GUARDHELP.scr:83
end

script.labels["Main"] = function(ctx)
    -- GUARDHELP.scr:86
    -- Traceon
    ctx:command("addfriend", "CommonerHuman2MaleA") -- GUARDHELP.scr:90
    ctx:addTrigger("help", "OnGiveHelp") -- GUARDHELP.scr:91
    ctx:command("onfoundtarget", "OnTarget") -- GUARDHELP.scr:92
    ctx:command("ondamage", "OnDamage") -- GUARDHELP.scr:93
    mm9.gosub(script, ctx, "BaseDoorInit") -- GUARDHELP.scr:94
    mm9.gosub(script, ctx, "GS_Init") -- GUARDHELP.scr:95
    do return ctx:exit("") end -- GUARDHELP.scr:96
end

return script
