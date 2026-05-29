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
    ctx:state().g_hobject = ctx:self() -- GHOSTFADE.scr:16
    ctx:self():setFlag("visible", true) -- GHOSTFADE.scr:17
    ctx:runScript("ghost.scr") -- GHOSTFADE.scr:18
    ctx:exitScript() -- GHOSTFADE.scr:19
    do return ctx:exit("") end -- GHOSTFADE.scr:20
end

script.labels["OnFoundPlayer"] = function(ctx)
    -- GHOSTFADE.scr:23
    ctx:self():runTo(ctx:player(), 0, "TurnSolid") -- GHOSTFADE.scr:26
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:28
end

script.labels["InitGhostFade"] = function(ctx)
    -- GHOSTFADE.scr:31
    ctx:self():addFriend("AIBase") -- GHOSTFADE.scr:33
    ctx:self():addEnemy("Player") -- GHOSTFADE.scr:34
    ctx:self():setFlag("FLAG_GRAVITY", false) -- GHOSTFADE.scr:36
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- GHOSTFADE.scr:37
    ctx:onEvent("OnFoundPlayer", "OnFoundPlayer") -- GHOSTFADE.scr:39
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:41
end

script.labels["Main"] = function(ctx)
    -- GHOSTFADE.scr:44
    ctx:wait(0, 5, "InitGhostFade") -- GHOSTFADE.scr:46
    -- traceon ;Delete
    mm9.gosub(script, ctx, "Init") -- GHOSTFADE.scr:49
    ctx:getParam(0, "nRange") -- GHOSTFADE.scr:50
    if ctx:condition("nRange==NULL") then -- GHOSTFADE.scr:51
        ctx:state().nRange = 1024 -- GHOSTFADE.scr:52
    end -- GHOSTFADE.scr:54
    do return ctx:exit("TRUE") end -- GHOSTFADE.scr:56
end

return script
