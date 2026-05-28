-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TREMORS.scr"
script.includes = {}
script.labels = {}


-- Tremor.SCR
-- Brett Yagi
script.labels["DoIta"] = function(ctx)
    -- TREMORS.scr:14
    if ctx:condition("done < 2") then -- TREMORS.scr:17
        if ctx:condition("Destroyed != a") then -- TREMORS.scr:18
            ctx:command("damage", "hHandle 100 4 0") -- TREMORS.scr:19
            ctx:command("destroyed", "= a") -- TREMORS.scr:20
            ctx:command("done", "= done + 1") -- TREMORS.scr:21
        end -- TREMORS.scr:22
    else -- TREMORS.scr:23
        ctx:command("getobjecthandle", "Vampir0 hHandle") -- TREMORS.scr:24
        ctx:trigger("hHandle", "done") -- TREMORS.scr:25
        ctx:command("die", "") -- TREMORS.scr:27
    end -- TREMORS.scr:28
    do return ctx:exit(1) end -- TREMORS.scr:29
end

script.labels["ab"] = function(ctx)
    -- TREMORS.scr:32
    if ctx:condition("a == 0") then -- TREMORS.scr:34
        ctx:command("getobjecthandle", "DestructableBrush0 hHandle") -- TREMORS.scr:36
        ctx:command("a", "= 1") -- TREMORS.scr:37
    else -- TREMORS.scr:38
        ctx:command("getobjecthandle", "DestructableBrush1 hHandle") -- TREMORS.scr:39
        ctx:command("a", "= 0") -- TREMORS.scr:40
    end -- TREMORS.scr:41
    do return ctx:exit(1) end -- TREMORS.scr:43
end

script.labels["Main"] = function(ctx)
    -- TREMORS.scr:45
    ctx:command("getobjecthandle", "DestructableBrush0 hHandle") -- TREMORS.scr:48
    ctx:command("ondamage", "DoIta") -- TREMORS.scr:49
    ctx:addTrigger("abc", "ab") -- TREMORS.scr:50
    do return ctx:exit("") end -- TREMORS.scr:54
end

return script
