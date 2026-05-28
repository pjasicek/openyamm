-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AW_SHOOT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- AW_Shoot.scr
-- timmy
-- handles the Six Fires of Penance stuff
script.labels["Init"] = function(ctx)
    -- AW_SHOOT.scr:15
    if ctx:condition("sTarget==NULL") then -- AW_SHOOT.scr:18
        do return ctx:exit("") end -- AW_SHOOT.scr:19
    end -- AW_SHOOT.scr:20
    ctx:command("getobjecthandle", "sTarget g_hobject") -- AW_SHOOT.scr:22
    ctx:command("target", "g_hobject") -- AW_SHOOT.scr:23
    do return ctx:exit("") end -- AW_SHOOT.scr:24
end

script.labels["Main"] = function(ctx)
    -- AW_SHOOT.scr:27
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sTarget") -- AW_SHOOT.scr:33
    ctx:command("onpoststartworld", "Init") -- AW_SHOOT.scr:34
    ctx:command("onpostminisaveload", "Init") -- AW_SHOOT.scr:35
    do return ctx:exit("") end -- AW_SHOOT.scr:36
end

return script
