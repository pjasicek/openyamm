-- MMMerge map supplement: William Setag's Tower.

-- OY-364: the Master of the Sword who carries the Villain's Blade (actor group 51) is a Fighter Plate, a class
-- hostile.txt keeps friendly to the party, so he stood by while the party took the tower. He fights for Setag.
RegisterMapOnLoadEvent(65010, "Setag's Master of the Sword fights the party", function()
    evt.SetMonGroupBit(51, MonsterBits.Hostile, 1) -- actor group 51: Master of the Sword
end)
