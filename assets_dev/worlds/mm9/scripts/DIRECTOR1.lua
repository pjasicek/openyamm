-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DIRECTOR1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "followpath.inc" }

script.labels["BeginMovie"] = function(ctx)
    -- DIRECTOR1.scr:9
    if ctx:condition("start = 1") then -- DIRECTOR1.scr:11
        do return ctx:exit("") end -- DIRECTOR1.scr:12
    end -- DIRECTOR1.scr:13
    ctx:command("getobjecthandle", "c0,hCamera1") -- DIRECTOR1.scr:15
    ctx:command("getobjecthandle", "Goblin0, hGoblin0") -- DIRECTOR1.scr:16
    ctx:trigger("hGoblin0", "BeginScene") -- DIRECTOR1.scr:18
    ctx:trigger("hCamera1", "Zoom") -- DIRECTOR1.scr:19
    ctx:command("set", "start,1") -- DIRECTOR1.scr:21
    do return ctx:exit("") end -- DIRECTOR1.scr:23
end

script.labels["Main"] = function(ctx)
    -- DIRECTOR1.scr:26
    -- This routine is automatically run
    -- at script startup...
    -- TraceOn
    ctx:addTrigger("Movie", "BeginMovie") -- DIRECTOR1.scr:33
    do return ctx:exit("") end -- DIRECTOR1.scr:35
end

return script
