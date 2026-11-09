"""MM7 m182 native frame times (v2 clip tables) and their mapping onto the cdr1 clip clock used by v3.
Flight loop 0.9375 s -> cdr1 Standing/Walking 0.75 s (proportional); Attack: native impact 0.5 s of 0.875 s ->
cdr1 impact 0.75 s of 1.0 s (piecewise linear); Hit 0.875 -> 1.125 s and Death 1.25 -> 2.4167 s proportional."""
FLIGHT = [('sa', 0.), ('wa', .125), ('wb', .25), ('wc', .4375), ('wd', .625), ('we', .75), ('wf', .875)]
SHOTS = {'Standing': FLIGHT, 'Walking': FLIGHT, 'Fidget': FLIGHT,
         'Attack': [('sa', 0.), ('aa', .125), ('ab', .25), ('ac', .375), ('ad', .5), ('ae', .625), ('af', .75)],
         'Hit': [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('nd', .5), ('ne', .625), ('nf', .75)],
         'Death': [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('da', .5), ('db', .625), ('dc', .8125), ('xa', .9375), ('dd', 1.125)]}
FRONT_ONLY = {'da', 'db', 'dc', 'xa', 'dd'}
NATIVE = {'Standing': .9375, 'Walking': .9375, 'Fidget': .9375, 'Hit': .875, 'Death': 1.25}
CDR1 = {'Standing': .75, 'Walking': .75, 'Fidget': .75, 'Hit': 1.125, 'Death': 2.4166667}


def clip_time(clip, t):
    if clip == 'Attack':
        return t * .75 / .5 if t <= .5 else .75 + (t - .5) * (.25 / .375)
    return t * CDR1[clip] / NATIVE[clip]
