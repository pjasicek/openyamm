-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_TRYYGVASCR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["Init"] = function(ctx)
    -- ARG_TRYYGVASCR.scr:15
    ctx:self():loopAnimation("Sc2_Kirashot5", 0, "DoNothing") -- ARG_TRYYGVASCR.scr:18
    do return ctx:exit("") end -- ARG_TRYYGVASCR.scr:19
end

script.labels["Main"] = function(ctx)
    -- ARG_TRYYGVASCR.scr:22
    -- TraceOn ;delete me!!
    ctx:onEvent("OnPostStartWorld", "Init") -- ARG_TRYYGVASCR.scr:26
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ARG_TRYYGVASCR.scr:27
    do return ctx:exit("") end -- ARG_TRYYGVASCR.scr:29
end

return script
