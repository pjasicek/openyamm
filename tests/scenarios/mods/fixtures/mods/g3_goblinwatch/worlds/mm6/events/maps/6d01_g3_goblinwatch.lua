-- A named mod's script overlay of Goblinwatch (tests/scenarios/mods): event 990 gives the party 7 gold.
RegisterEvent(990, "G3 coin", function()
    AddValue(Gold, 7)
end)
