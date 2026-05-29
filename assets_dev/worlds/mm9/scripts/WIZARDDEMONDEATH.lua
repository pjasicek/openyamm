-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDDEMONDEATH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }

script.labels["Main"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:4
    ctx:wait(0, .1, "PlayDeathAnim0") -- WIZARDDEMONDEATH.scr:6
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:8
end

script.labels["PlayDeathAnim0"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:11
    ctx:playSound("sounds\\animsounds\\dragon\\hattack1.wav", "DoNothing", 1, 5000, "FALSE", 200) -- WIZARDDEMONDEATH.scr:13
    ctx:self():playAnimation("aware", "PlayDeathAnim1") -- WIZARDDEMONDEATH.scr:14
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:16
end

script.labels["PlayDeathAnim1"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:19
    ctx:playSound("sounds\\animsounds\\dragon\\wingattack.wav", "DoNothing", 1, 5000, "FALSE", 200) -- WIZARDDEMONDEATH.scr:21
    ctx:self():playAnimation("hattack1", "PlayDeathAnim2") -- WIZARDDEMONDEATH.scr:22
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:24
end

script.labels["PlayDeathAnim2"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:27
    ctx:playSound("sounds\\animsounds\\dragon\\rattack1.wav", "DoNothing", 1, 5000, "FALSE", 200) -- WIZARDDEMONDEATH.scr:29
    ctx:self():playAnimation("rattack2", "PlayDeathAnim3") -- WIZARDDEMONDEATH.scr:30
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:32
end

script.labels["PlayDeathAnim3"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:35
    ctx:playSound("sounds\\animsounds\\dragon\\die1.wav", "DoNothing", 1, 5000, "FALSE", 200) -- WIZARDDEMONDEATH.scr:37
    ctx:self():playAnimation("wince1") -- WIZARDDEMONDEATH.scr:38
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:40
end

return script
