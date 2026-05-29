-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAM1000.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "njam1000.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "range.inc" }

-- NjamFreeze.scr
-- By Timmy
-- 11/16
-- Manager for Njam in 1000 terrors;
script.labels["Main"] = function(ctx)
    -- NJAM1000.scr:19
    -- TraceOn ;delete me!!
    ctx:state().g_hplayer = ctx:player() -- NJAM1000.scr:24
    ctx:self():setTarget(ctx:player()) -- NJAM1000.scr:25
    ctx:self():addEnemy("Player") -- NJAM1000.scr:27
    ctx:onEvent("OnPostMiniSaveLoad", "Vanish2c") -- NJAM1000.scr:29
    mm9.gosub(script, ctx, "baseinit") -- NJAM1000.scr:31
    mm9.gosub(script, ctx, "RangeInit") -- NJAM1000.scr:32
    mm9.gosub(script, ctx, "Init") -- NJAM1000.scr:33
    do return ctx:exit("") end -- NJAM1000.scr:36
end

return script
