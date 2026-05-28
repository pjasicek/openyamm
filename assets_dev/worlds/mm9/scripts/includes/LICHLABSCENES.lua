-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHLABSCENES.inc"
script.includes = {}
script.labels = {}


-- LichLabScene.inc
-- by SJR
-- 11-10-01
-- Purpose:basic triggers for LichLab
-- cutscene
script.labels["InitLichLabScenes"] = function(ctx)
    -- LICHLABSCENES.inc:10
    ctx:addTrigger("Scene0", "OnScene0") -- LICHLABSCENES.inc:12
    ctx:addTrigger("Scene1", "OnScene1") -- LICHLABSCENES.inc:13
    ctx:addTrigger("Scene2", "OnScene2") -- LICHLABSCENES.inc:14
    ctx:addTrigger("Scene3", "OnScene3") -- LICHLABSCENES.inc:15
    ctx:addTrigger("Scene4", "OnScene4") -- LICHLABSCENES.inc:16
    ctx:addTrigger("Scene5", "OnScene5") -- LICHLABSCENES.inc:17
    ctx:addTrigger("Scene6", "OnScene6") -- LICHLABSCENES.inc:18
    do return ctx:exit(1) end -- LICHLABSCENES.inc:20
end

script.labels["OnScene0"] = function(ctx)
    -- LICHLABSCENES.inc:23
    do return ctx:exit(1) end -- LICHLABSCENES.inc:25
end

script.labels["OnScene1"] = function(ctx)
    -- LICHLABSCENES.inc:27
    do return ctx:exit(1) end -- LICHLABSCENES.inc:29
end

script.labels["OnScene2"] = function(ctx)
    -- LICHLABSCENES.inc:31
    do return ctx:exit(1) end -- LICHLABSCENES.inc:33
end

script.labels["OnScene3"] = function(ctx)
    -- LICHLABSCENES.inc:35
    do return ctx:exit(1) end -- LICHLABSCENES.inc:37
end

script.labels["OnScene4"] = function(ctx)
    -- LICHLABSCENES.inc:39
    do return ctx:exit(1) end -- LICHLABSCENES.inc:41
end

script.labels["OnScene5"] = function(ctx)
    -- LICHLABSCENES.inc:43
    do return ctx:exit(1) end -- LICHLABSCENES.inc:45
end

script.labels["OnScene6"] = function(ctx)
    -- LICHLABSCENES.inc:47
    do return ctx:exit(1) end -- LICHLABSCENES.inc:49
end

return script
