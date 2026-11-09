return Behavior.define{
    version = 1,
    onDeath = function(self, s)
        self:effect('openyamm:fx/arcane_pulse', 1.5)
        self:summon(10003, 4, 300)
    end,
}
