-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOLLOWPATH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "followpath.inc" }

-- FollowPath.scr
-- p0	- Base name of path to follow...
-- p1	- Speed
-- p2	- Num Loops
script.labels["Main"] = function(ctx)
    -- FOLLOWPATH.scr:16
    mm9.gosub(script, ctx, "FollowPathInit") -- FOLLOWPATH.scr:19
    ctx:getParam(0, "g_sFollowPathName") -- FOLLOWPATH.scr:21
    ctx:getParam(1, "g_nFollowPathSpeed") -- FOLLOWPATH.scr:22
    ctx:getParam(2, "g_nFollowPathLoops") -- FOLLOWPATH.scr:23
    mm9.gosub(script, ctx, "FollowPath") -- FOLLOWPATH.scr:25
    do return ctx:exit("") end -- FOLLOWPATH.scr:27
end

return script
