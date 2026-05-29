-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "INTEGRIS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Integris.scr
-- By Timmy
-- gives the player integris (item 181) for assassin promo
-- Ludwig's RudeID is 47
script.labels["Onuse"] = function(ctx)
    -- INTEGRIS.scr:14
    if ctx:hasKey(222) then -- INTEGRIS.scr:18-19
        ctx:hasKey(223, "keycheck") -- INTEGRIS.scr:21
        if ctx:condition("keycheck==0") then -- INTEGRIS.scr:22
            -- gives player finished quest key
            ctx:giveKey("", 223) -- INTEGRIS.scr:24
            ctx:giveItem(181) -- INTEGRIS.scr:25
            ctx:self():remove() -- INTEGRIS.scr:27
            do return ctx:exit("") end -- INTEGRIS.scr:28
        end -- INTEGRIS.scr:30
    end -- INTEGRIS.scr:31
    do return ctx:exit("") end -- INTEGRIS.scr:35
end

script.labels["Main"] = function(ctx)
    -- INTEGRIS.scr:41
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- INTEGRIS.scr:45
    ctx:hasKey(223, "keycheck") -- INTEGRIS.scr:46
    if ctx:condition("g_ntemp==1") then -- INTEGRIS.scr:47
        ctx:self():remove() -- INTEGRIS.scr:49
        ctx:exitScript() -- INTEGRIS.scr:50
        do return ctx:exit("") end -- INTEGRIS.scr:51
    end -- INTEGRIS.scr:52
    do return ctx:exit("") end -- INTEGRIS.scr:54
end

return script
