-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BLOWUPTHEBOARDS.scr"
script.includes = {}
script.labels = {}


-- BlowUpTheBoards.scr
-- kd
-- 10-30-01
-- Makes the torch fall to the ground.
-- Nothing slick or fancy
script.labels["DoTheDamage"] = function(ctx)
    -- BLOWUPTHEBOARDS.scr:16
    if ctx:condition("hBlocker==0") then -- BLOWUPTHEBOARDS.scr:18
        ctx:state().hBlocker = ctx:objectOrNil("sBlocker") -- BLOWUPTHEBOARDS.scr:19
        if ctx:condition("hBlocker==0") then -- BLOWUPTHEBOARDS.scr:20
            do return ctx:exit(1) end -- BLOWUPTHEBOARDS.scr:21
        end -- BLOWUPTHEBOARDS.scr:22
    end -- BLOWUPTHEBOARDS.scr:23
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, 0, 100) -- BLOWUPTHEBOARDS.scr:25
    ctx:playSound("Sounds\\Events\\crate_smash.wav", "DoNothing", 500, 2000, 0, 100) -- BLOWUPTHEBOARDS.scr:26
    ctx:trigger("hBlocker", "destroy") -- BLOWUPTHEBOARDS.scr:28
    do return ctx:exit(1) end -- BLOWUPTHEBOARDS.scr:30
end

script.labels["Main"] = function(ctx)
    -- BLOWUPTHEBOARDS.scr:33
    ctx:getParam(0, "sBlocker") -- BLOWUPTHEBOARDS.scr:35
    ctx:addTrigger("HitMe", "DoTheDamage") -- BLOWUPTHEBOARDS.scr:37
    do return ctx:exit(1) end -- BLOWUPTHEBOARDS.scr:39
end

script.labels["DoNothing"] = function(ctx)
    -- BLOWUPTHEBOARDS.scr:41
    do return ctx:exit(1) end -- BLOWUPTHEBOARDS.scr:42
end

return script
