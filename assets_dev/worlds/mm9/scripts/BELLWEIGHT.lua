-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BELLWEIGHT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 5, path = "BaseGlobals.inc" }

-- BellWeight.scr
-- by SJR
script.labels["Main"] = function(ctx)
    -- BELLWEIGHT.scr:12
    ctx:getParam(0, "MAX_HEIGHT") -- BELLWEIGHT.scr:14
    ctx:addTrigger("open", "AdjustHeight") -- BELLWEIGHT.scr:16
    do return ctx:exit("TRUE") end -- BELLWEIGHT.scr:18
end

script.labels["AdjustHeight"] = function(ctx)
    -- BELLWEIGHT.scr:21
    ctx:getConsoleNumVar("GAME_BELL_HEIGHT", "nTemp") -- BELLWEIGHT.scr:23
    if ctx:condition("nTemp>1") then -- BELLWEIGHT.scr:24
        ctx:state().nTemp = 1 -- BELLWEIGHT.scr:25
    else -- BELLWEIGHT.scr:26
        if ctx:condition("nTemp<0") then -- BELLWEIGHT.scr:27
            ctx:state().nTemp = 0 -- BELLWEIGHT.scr:28
        end -- BELLWEIGHT.scr:29
    end -- BELLWEIGHT.scr:30
    -- scale height
    ctx:set("nHeight", "MAX_HEIGHT * nTemp") -- BELLWEIGHT.scr:33
    ctx:self():setNumberProperty("MoveDist", "nHeight") -- BELLWEIGHT.scr:35
    do return ctx:exit("FALSE") end -- BELLWEIGHT.scr:37
end

return script
