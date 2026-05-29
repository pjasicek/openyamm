-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SUNTEMPLEENTRANCE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- SunTemplePrison.scr
-- Tony Evans
-- This script controls the Altar Doors in the
-- Grand Temple of the Sun
-- Parameters: none
script.labels["HandleMoon"] = function(ctx)
    -- SUNTEMPLEENTRANCE.scr:17
    if ctx:condition("MoonBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:20
        ctx:state().MoonBut = false -- SUNTEMPLEENTRANCE.scr:21
    else -- SUNTEMPLEENTRANCE.scr:22
        ctx:state().MoonBut = true -- SUNTEMPLEENTRANCE.scr:23
    end -- SUNTEMPLEENTRANCE.scr:24
    if ctx:condition("MoonBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:26
        if ctx:condition("StarBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:27
            mm9.gosub(script, ctx, "HandleDoorsOpen") -- SUNTEMPLEENTRANCE.scr:28
            ctx:state().MoonBut = false -- SUNTEMPLEENTRANCE.scr:29
            ctx:state().StarBut = false -- SUNTEMPLEENTRANCE.scr:30
        end -- SUNTEMPLEENTRANCE.scr:31
    end -- SUNTEMPLEENTRANCE.scr:32
    do return ctx:exit("") end -- SUNTEMPLEENTRANCE.scr:34
end

script.labels["HandleStar"] = function(ctx)
    -- SUNTEMPLEENTRANCE.scr:37
    if ctx:condition("StarBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:40
        ctx:state().StarBut = false -- SUNTEMPLEENTRANCE.scr:41
    else -- SUNTEMPLEENTRANCE.scr:42
        ctx:state().StarBut = true -- SUNTEMPLEENTRANCE.scr:43
    end -- SUNTEMPLEENTRANCE.scr:44
    if ctx:condition("StarBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:46
        if ctx:condition("MoonBut==TRUE") then -- SUNTEMPLEENTRANCE.scr:47
            mm9.gosub(script, ctx, "HandleDoorsOpen") -- SUNTEMPLEENTRANCE.scr:48
            ctx:state().MoonBut = false -- SUNTEMPLEENTRANCE.scr:49
            ctx:state().StarBut = false -- SUNTEMPLEENTRANCE.scr:50
        end -- SUNTEMPLEENTRANCE.scr:51
    end -- SUNTEMPLEENTRANCE.scr:52
    do return ctx:exit("") end -- SUNTEMPLEENTRANCE.scr:54
end

script.labels["HandleDoorsOpen"] = function(ctx)
    -- SUNTEMPLEENTRANCE.scr:58
    -- make Doors open
    ctx:object("AltarDoorLeft"):trigger("unlock") -- SUNTEMPLEENTRANCE.scr:62-63
    ctx:object("AltarDoorRight"):trigger("unlock") -- SUNTEMPLEENTRANCE.scr:64-65
    do return ctx:exit("") end -- SUNTEMPLEENTRANCE.scr:66
end

script.labels["Main"] = function(ctx)
    -- SUNTEMPLEENTRANCE.scr:70
    ctx:addTrigger("Moon", "HandleMoon") -- SUNTEMPLEENTRANCE.scr:73
    ctx:addTrigger("Star", "HandleStar") -- SUNTEMPLEENTRANCE.scr:74
    do return ctx:exit("") end -- SUNTEMPLEENTRANCE.scr:76
end

return script
