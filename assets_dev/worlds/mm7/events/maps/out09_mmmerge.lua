-- MMMerge supplement: Evenmorn obelisk treasure.

RegisterMapOnLoadEvent(65009, "MMMerge Evenmorn obelisk treasure", function()
    MM7.UpdateEvenmornObeliskTreasure()
end)

-- Every half hour, as MMerge's Timer(SetTrViz, const.Hour/2).
RegisterMapTimerEvent(65011, 1800, function()
    MM7.UpdateEvenmornObeliskTreasure()
end, "MMMerge Evenmorn obelisk treasure clock")

