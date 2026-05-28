-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDDEMONDEATH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }

script.labels["Main"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:4
    ctx:command("wait", "0, .1, PlayDeathAnim0") -- WIZARDDEMONDEATH.scr:6
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:8
end

script.labels["PlayDeathAnim0"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:11
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\hattack1.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDDEMONDEATH.scr:13
    ctx:command("playanim", "aware, PlayDeathAnim1") -- WIZARDDEMONDEATH.scr:14
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:16
end

script.labels["PlayDeathAnim1"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:19
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\wingattack.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDDEMONDEATH.scr:21
    ctx:command("playanim", "hattack1, PlayDeathAnim2") -- WIZARDDEMONDEATH.scr:22
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:24
end

script.labels["PlayDeathAnim2"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:27
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\rattack1.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDDEMONDEATH.scr:29
    ctx:command("playanim", "rattack2, PlayDeathAnim3") -- WIZARDDEMONDEATH.scr:30
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:32
end

script.labels["PlayDeathAnim3"] = function(ctx)
    -- WIZARDDEMONDEATH.scr:35
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\die1.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDDEMONDEATH.scr:37
    ctx:command("playanim", "wince1") -- WIZARDDEMONDEATH.scr:38
    do return ctx:exit(1) end -- WIZARDDEMONDEATH.scr:40
end

return script
