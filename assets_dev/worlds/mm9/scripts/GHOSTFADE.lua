-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GHOSTFADE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "flags.inc" }

-- GhostFade.scr
-- timmy
-- 12/6
-- fades ghosts in OnFoundTarget
script.labels["TurnSolid"] = function(ctx)
    -- GHOSTFADE.scr:14
    ctx:command("getmyhandle", "g_hobject") -- GHOSTFADE.scr:16
    ctx:command("setflag", "g_hobject, visible") -- GHOSTFADE.scr:17
    ctx:command("runscript", "ghost.scr") -- GHOSTFADE.scr:18
    ctx:command("exitscript", "") -- GHOSTFADE.scr:19
    do return ctx:exit("") end -- GHOSTFADE.scr:20
end

script.labels["OnFoundPlayer"] = function(ctx)
    -- GHOSTFADE.scr:23
    ctx:command("getplayerhandle", "hPlayer") -- GHOSTFADE.scr:25
    ctx:command("runto", "hPlayer, 0, TurnSolid") -- GHOSTFADE.scr:26
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:28
end

script.labels["InitGhostFade"] = function(ctx)
    -- GHOSTFADE.scr:31
    ctx:command("addfriend", "AIBase") -- GHOSTFADE.scr:33
    ctx:command("addenemy", "Player") -- GHOSTFADE.scr:34
    ctx:command("clearflag", "hMe, FLAG_GRAVITY") -- GHOSTFADE.scr:36
    ctx:command("setflag", "hMe, FLAG_GOTHRUWORLD") -- GHOSTFADE.scr:37
    ctx:command("onfoundplayer", "OnFoundPlayer") -- GHOSTFADE.scr:39
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:41
end

script.labels["Main"] = function(ctx)
    -- GHOSTFADE.scr:44
    ctx:command("wait", "0, 5, InitGhostFade") -- GHOSTFADE.scr:46
    -- traceon ;Delete
    mm9.gosub(script, ctx, "Init") -- GHOSTFADE.scr:49
    ctx:getParam(0, "nRange") -- GHOSTFADE.scr:50
    if ctx:condition("nRange==NULL") then -- GHOSTFADE.scr:51
        ctx:command("set", "nRange, 1024") -- GHOSTFADE.scr:52
    end -- GHOSTFADE.scr:54
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:56
end

return script
