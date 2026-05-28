-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEFLY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseFly.inc" }

-- basefly.scr
-- Jeff Leggett
-- 10/01/2001
-- Base script for creatures that stay in the air and attack.
script.labels["Init"] = function(ctx)
    -- BASEFLY.scr:14
    ctx:command("setidle", "") -- BASEFLY.scr:16
    do return ctx:exit("") end -- BASEFLY.scr:18
end

script.labels["Main"] = function(ctx)
    -- BASEFLY.scr:21
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "BaseFlyInit") -- BASEFLY.scr:26
    ctx:command("wait", "30, 0.01, Init") -- BASEFLY.scr:28
    do return ctx:exit("") end -- BASEFLY.scr:30
end

return script
