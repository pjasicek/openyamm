-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }
script.includes[#script.includes + 1] = { line = 3, path = "LichLabScenes.inc" }

script.labels["Main"] = function(ctx)
    -- GUARDACTOR.scr:8
    mm9.gosub(script, ctx, "InitLichLabScenes") -- GUARDACTOR.scr:10
    do return ctx:exit(1) end -- GUARDACTOR.scr:12
end

script.labels["OnScene1"] = function(ctx)
    -- GUARDACTOR.scr:15
    ctx:self():playAnimation("search", "EndScene") -- GUARDACTOR.scr:17
    do return ctx:exit(1) end -- GUARDACTOR.scr:19
end

script.labels["OnScene3"] = function(ctx)
    -- GUARDACTOR.scr:22
    -- PlayAnim aware, Attack
    do return ctx:exit(1) end -- GUARDACTOR.scr:26
end

script.labels["OnScene5"] = function(ctx)
    -- GUARDACTOR.scr:29
    ctx:state().g_hTarget = ctx:objectOrNil("MarkerTarget2") -- GUARDACTOR.scr:31
    ctx:self():runTo(ctx:object("g_hTarget"), 25, "DoNothing") -- GUARDACTOR.scr:32
    do return ctx:exit(1) end -- GUARDACTOR.scr:34
end

script.labels["Attack"] = function(ctx)
    -- GUARDACTOR.scr:37
    mm9.gosub(script, ctx, "EndScene") -- GUARDACTOR.scr:39
    ctx:state().g_hTarget = ctx:objectOrNil("MarkerTarget2") -- GUARDACTOR.scr:40
    mm9.gosub(script, ctx, "BaseInit") -- GUARDACTOR.scr:41
    mm9.gosub(script, ctx, "SetupTarget") -- GUARDACTOR.scr:42
    mm9.gosub(script, ctx, "AggressiveStart") -- GUARDACTOR.scr:43
    do return ctx:exit(1) end -- GUARDACTOR.scr:45
end

return script
