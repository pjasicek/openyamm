-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ATTATCHTO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- AttatchTo.scr
-- Handles attatching props to Monsters
script.labels["Target"] = function(ctx)
    -- ATTATCHTO.scr:12
    ctx:state().g_hplayer = ctx:player() -- ATTATCHTO.scr:15
    ctx:self():setTarget(ctx:player()) -- ATTATCHTO.scr:16
    do return ctx:exit("") end -- ATTATCHTO.scr:17
end

script.labels["Main"] = function(ctx)
    -- ATTATCHTO.scr:20
    mm9.gosub(script, ctx, "Target") -- ATTATCHTO.scr:23
    mm9.gosub(script, ctx, "baseinit") -- ATTATCHTO.scr:24
    -- gosub RangeInit
    do return ctx:exit("") end -- ATTATCHTO.scr:27
end

return script
