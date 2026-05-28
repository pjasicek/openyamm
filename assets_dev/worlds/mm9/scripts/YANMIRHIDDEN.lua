-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRHIDDEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "flags.inc" }

-- YanmirHidden.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- YANMIRHIDDEN.scr:15
    ctx:getParam(0, "sYanmirName") -- YANMIRHIDDEN.scr:17
    ctx:command("onpoststartworld", "InitYanmirHidden") -- YANMIRHIDDEN.scr:19
    ctx:command("onpostminisaveload", "InitYanmirHidden") -- YANMIRHIDDEN.scr:20
    do return ctx:exit("TRUE") end -- YANMIRHIDDEN.scr:22
end

script.labels["InitYanmirHidden"] = function(ctx)
    -- YANMIRHIDDEN.scr:25
    ctx:command("getmyhandle", "hMe") -- YANMIRHIDDEN.scr:27
    ctx:command("getobjecthandle", "sYanmirName, hYanmir") -- YANMIRHIDDEN.scr:29
    if ctx:condition("hYanmir==0") then -- YANMIRHIDDEN.scr:30
        ctx:command("setflag", "hMe, FLAG_VISIBLE") -- YANMIRHIDDEN.scr:31
        ctx:command("setflag", "hMe, FLAG_SOLID") -- YANMIRHIDDEN.scr:32
        ctx:command("runscript", "\"titan.scr\"") -- YANMIRHIDDEN.scr:34
    else -- YANMIRHIDDEN.scr:35
        ctx:command("clearflag", "hMe, FLAG_VISIBLE") -- YANMIRHIDDEN.scr:36
        ctx:command("clearflag", "hMe, FLAG_SOLID") -- YANMIRHIDDEN.scr:37
    end -- YANMIRHIDDEN.scr:38
    do return ctx:exit("TRUE") end -- YANMIRHIDDEN.scr:40
end

return script
