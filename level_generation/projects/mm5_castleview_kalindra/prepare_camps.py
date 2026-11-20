"""Purposeful temporary shelters and caravan geometry within the four reserved pads."""

IDS={'dreyfus','justine','yog','kramer'}
PALETTE={'cloth':'gnecclg2','wood':'t06a10','crosswood':'t06c11','trim':'t06a10',
         'metal':'gn_mtl03','crate':'crate_w64'}


def configure(identity,venue,origin,tangent,normal):
    if identity in ['dreyfus','justine']:
        refuge=identity=='dreyfus'
        bounds=[-352,96,352,544] if refuge else [-256,64,256,512]
        parts=[{'id':'cloth_shelter','bounds':bounds,'roof':'camp_shelter',
                'eave':288 if refuge else 256,'top':352 if refuge else 288,
                'sideScreen':refuge}]
    elif identity=='yog':
        parts=[{'id':'chief_tent','bounds':[-320,128,320,544],'roof':'camp_tent','eave':0,'top':432}]
    else:
        parts=[{'id':'covered_wagon','bounds':[-320,196,256,476],'roof':'camp_wagon','eave':256,'top':392}]
    if identity=='yog':
        venue.update({'interactionSurface':'tent flap','localDepth':124})
        venue['door']=[origin[i]-normal[i]*124 for i in range(2)]
    else:
        venue.update({'interactionSurface':'camp counter','doorSize':[256,96]})
    notes=[
        'New temporary construction using inspected Garrote canvas/timber artwork; no donor mesh or generic house.',
        'Keep source resident identities on the existing single venue. No actors, services, travel or rewards.',
        'The camp counter is a visible interaction surface, not an enlarged door; Yog instead uses an ordinary tent flap.'
    ]
    if identity=='justine':
        notes.append('Raise low cover from the preliminary 192/256 heights to 256/288 for usable headroom.')
    if identity=='kramer':
        notes.append('Covered wagon fits wholly within the existing pad; four spoked wheels meet native ground. '
                     'Loading counter and packed supplies represent caravan activity without inventing scheduled transport.')
    return parts,notes
