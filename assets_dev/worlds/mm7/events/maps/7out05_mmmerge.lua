-- MMMerge supplement: Deyja local monster relations and post-NPC ambush.

-- MMMerge Scripts/Maps/7out05.lua: Goblins (faction 91) are peaceful toward the party here (faction 0).
SetLocalFactionRelations({
    {91, 0, 0},
})

RegisterMapOnLoadEvent(65005, "MMMerge Deyja local hostility", function()
    MM7.UpdateDeyjaOutdoorState()
end)

RegisterNpcExitHook(65006, "MMMerge Deyja ambush", function(context)
    MM7.SummonDeyjaAmbushIfNeeded(context)
end)
