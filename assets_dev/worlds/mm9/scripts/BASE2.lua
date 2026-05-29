-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASE2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "newbase.inc" }

script.labels["Main"] = function(ctx)
    -- BASE2.scr:4
    ctx:state().g_hObject = ctx:player() -- BASE2.scr:6
    mm9.gosub(script, ctx, "BaseInit") -- BASE2.scr:7
    do return ctx:exit("") end -- BASE2.scr:9
end

return script
