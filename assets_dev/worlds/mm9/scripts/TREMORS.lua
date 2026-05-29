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
            ctx:object("hHandle"):damage(100, 4, 0) -- TREMORS.scr:19
            ctx:set("Destroyed", "a") -- TREMORS.scr:20
            ctx:set("done", "done + 1") -- TREMORS.scr:21
        end -- TREMORS.scr:22
    else -- TREMORS.scr:23
        ctx:object("Vampir0"):trigger("done") -- TREMORS.scr:24-25
        ctx:self():die() -- TREMORS.scr:27
    end -- TREMORS.scr:28
    do return ctx:exit(1) end -- TREMORS.scr:29
end

script.labels["ab"] = function(ctx)
    -- TREMORS.scr:32
    if ctx:condition("a == 0") then -- TREMORS.scr:34
        ctx:state().hHandle = ctx:objectOrNil("DestructableBrush0") -- TREMORS.scr:36
        ctx:state().a = 1 -- TREMORS.scr:37
    else -- TREMORS.scr:38
        ctx:state().hHandle = ctx:objectOrNil("DestructableBrush1") -- TREMORS.scr:39
        ctx:state().a = 0 -- TREMORS.scr:40
    end -- TREMORS.scr:41
    do return ctx:exit(1) end -- TREMORS.scr:43
end

script.labels["Main"] = function(ctx)
    -- TREMORS.scr:45
    ctx:state().hHandle = ctx:objectOrNil("DestructableBrush0") -- TREMORS.scr:48
    ctx:onEvent("OnDamage", "DoIta") -- TREMORS.scr:49
    ctx:addTrigger("abc", "ab") -- TREMORS.scr:50
    do return ctx:exit("") end -- TREMORS.scr:54
end

return script
