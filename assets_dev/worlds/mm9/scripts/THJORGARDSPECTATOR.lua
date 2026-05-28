-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORGARDSPECTATOR.scr"
script.includes = {}
script.labels = {}


-- ThjorgardSpectator.scr
-- by SJR
-- 01-04-02
-- Purpose:a low-impact cheering guy
-- to take up space in Thjorgard
-- ScriptParams:
-- p0 = age (-1,0,1)->(AdultF,Child,AdultM)
script.labels["Main"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:15
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:17
    ctx:getParam(0, "nAge") -- THJORGARDSPECTATOR.scr:18
    -- CacheSound
    ctx:command("wait", "0, 1, InitThjorgardSpectator") -- THJORGARDSPECTATOR.scr:21
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:23
end

script.labels["InitThjorgardSpectator"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:26
    ctx:command("setidle", "") -- THJORGARDSPECTATOR.scr:28
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:30
end

script.labels["Cheer"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:33
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:35
end

script.labels["Boo"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:38
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:40
end

script.labels["Jump"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:43
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:45
end

script.labels["LookAround"] = function(ctx)
    -- THJORGARDSPECTATOR.scr:48
    do return ctx:exit(1) end -- THJORGARDSPECTATOR.scr:50
end

return script
