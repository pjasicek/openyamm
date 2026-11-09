"""Original wall-mounted notice displays in existing clear facade bays.

These identify civic, membership and paid-work activity without scripting a service.
The mayor's display sits left of the first door; its central bay is a window.
"""

PALETTE = {'guild': 'mm5guild', 'mayor': 'mm5civic', 'workyard': 'mm5hiring'}
BOARDS = {
    'guild': {'bounds': [-240,-12,88,-96,2,232], 'artBounds': [-232,-13,96,-104,-13,224],
              'purpose': 'Membership and public notices beside the guild entrance; forecourt contact remains reserved.'},
    'mayor': {'bounds': [-528,-12,88,-240,2,248], 'artBounds': [-512,-13,104,-256,-13,232],
              'purpose': 'Shared civic/editorial public display in the clear bay left of the mayor doorway.'},
    'workyard': {'bounds': [96,-12,88,240,2,232], 'artBounds': [104,-13,96,232,-13,224],
                 'purpose': 'Paid-work notice on the unwindowed side of the hiring-office doorway.'},
}


def author_notices(author, building, palette):
    if not building.get('publicNotice'):
        return
    board = building['publicNotice']
    panels = []
    author.box(panels, board['bounds'], palette['wood'])
    x0, y, z0, x1, _, z1 = board['artBounds']
    author.panel(panels, [(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)], board['texture'],
                 [(0,0),(1,0),(1,1),(0,1)])
    author.model(building['id'] + '_public_notice', panels, building)
