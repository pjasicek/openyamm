-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IS_DYINGNPC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- IS_DyingNpc.scr
-- kd
-- 11-7-01
-- Makes the Stationary NPC Adventure die after
-- Lich deals killing blow.
script.labels["NpcDie"] = function(ctx)
    -- IS_DYINGNPC.scr:11
    ctx:self():stop() -- IS_DYINGNPC.scr:13
    do return ctx:exit("TRUE") end -- IS_DYINGNPC.scr:14
end

script.labels["KillNpc"] = function(ctx)
    -- IS_DYINGNPC.scr:16
    ctx:self():playAnimation("Wince2", "NpcDie") -- IS_DYINGNPC.scr:18
    do return ctx:exit("TRUE") end -- IS_DYINGNPC.scr:19
end

script.labels["Main2"] = function(ctx)
    -- IS_DYINGNPC.scr:21
    ctx:addTrigger("Die", "NpcDie") -- IS_DYINGNPC.scr:24
    do return ctx:exit("TRUE") end -- IS_DYINGNPC.scr:25
end

script.labels["Main"] = function(ctx)
    -- IS_DYINGNPC.scr:27
    ctx:wait(0, .1, "main2") -- IS_DYINGNPC.scr:29
    do return ctx:exit("TRUE") end -- IS_DYINGNPC.scr:30
end

return script
