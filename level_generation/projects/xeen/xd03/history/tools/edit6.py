import re
def setconst(p, table):
    s=open(p).read()
    for name,val in table.items():
        pat=re.compile(r"^%s = S\(.*\)$" % re.escape(name), re.M)
        if pat.search(s): s=pat.sub(f"{name} = {val}", s)
        else: raise SystemExit('missing '+name+' in '+p)
    open(p,'w').write(s)
setconst('gen_rooms.py', {
 'DEEP1': "S('c2b', 256, 256)", 'BASALT': "S('vlcwl1lg', 256, 256)", 'BIGBLOCK': "S('vlcwl3a', 128, 256)",
 'RUNEFRIEZE': "S('vlctrm3', 128, 128)", 'RUNEGLOW': "S('7tfb1', 128, 128)", 'DARKFLAGS': "S('vlcflore', 128, 128)",
 'FLAGSTONE': "S('vlcflora', 128, 128)", 'CRYSTALFLOOR': "S('crdrf1', 128, 128)", 'CRYSTAL': "S('crstont', 256, 256)",
 'GOLDROCK': "S('c1gold', 256, 256)", 'GOLDDEEP': "S('c2b', 256, 256)", 'EARTHROCK': "S('c2b', 256, 256)",
 'DIRT': "S('cfb1', 128, 128)", 'POST': "S('bemv16a', 16, 256)", 'BEAM': "S('bemh16a', 256, 16)",
 'PLANKS': "S('bemvwal', 128, 256)", 'PLANKFLOOR': "S('7trimda', 256, 128)", 'IRON': "S('ch004i', 64, 64)",
 'LAVA': "S('orfyrlga', 256, 256)", 'COPPER': "S('ctflor5', 128, 128)", 'SKULL': "S('ctceil3', 128, 128, fit=True)",
 'GEODEWALL': "S('crstont', 256, 256)", 'CRACKED': "S('crstont', 256, 256)", 'DARKFLAGS2': "S('vlcflore', 128, 128)",
 'DARKIRON': "S('vlcgnrc3', 256, 256)", 'CAVESTONES': "S('cfb1', 128, 128)", 'WEB': "S('c2b', 256, 256)",
})
setconst('gen_objects.py', {
 'PLANKS': "S('7trimd', 128, 256)", 'IRON': "S('ch004i', 64, 64)", 'PLANKDOOR': "S('bemvwal', 128, 256, fit=True)",
 'CRYSTAL': "S('crflr3', 128, 128)", 'DARKIRON': "S('vlcgnrc3', 256, 256)",
})
s=open('gen_rooms.py').read()
s=s.replace("MINEPOST_PLACEHOLDER","")
if 'MINEPOST' not in s:
    s=s.replace("POST = S('bemv16a', 16, 256)", "POST = S('bemv16a', 16, 256)\nMINEPOST = S('trim11_32', 32, 64)\nMINEBEAM = S('trim9_32a', 64, 32)\nDRESSED2 = S('ctwl2', 256, 256)\nTFB2 = S('tfb2', 128, 128)")
# mine timber in mine rooms
s=s.replace("'rise': top, 'surface': POST, 'top_surface': POST,","'rise': top, 'surface': MINEPOST, 'top_surface': MINEPOST,")
s=s.replace("'bottom_end': 16, 'surface': BEAM, 'notes': 'Stringer under the rail'","'bottom_end': 16, 'surface': MINEBEAM, 'notes': 'Stringer under the rail'")
s=s.replace("'bottom': int(surface_z(x)) - 64, 'surface': BEAM,","'bottom': int(surface_z(x)) - 64, 'surface': MINEBEAM,")
s=s.replace("'surface': BEAM, 'end_surface': POST,\n          'top_surface': BEAM, 'notes': 'The buffer stop","'surface': MINEBEAM, 'end_surface': MINEPOST,\n          'top_surface': MINEBEAM, 'notes': 'The buffer stop")
s=s.replace("{'path': [[7904, 960], [7904, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': BEAM}","{'path': [[7904, 960], [7904, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': MINEBEAM}")
s=s.replace("{'path': [[8160, 960], [8160, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': BEAM}","{'path': [[8160, 960], [8160, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': MINEBEAM}")
s=s.replace("'rise': 340, 'surface': POST, 'top_surface': POST, 'notes': 'Timber set post'","'rise': 340, 'surface': MINEPOST, 'top_surface': MINEPOST, 'notes': 'Timber set post'")
s=s.replace("'rise': 330, 'surface': POST, 'top_surface': POST, 'notes': 'Timber set post'","'rise': 330, 'surface': MINEPOST, 'top_surface': MINEPOST, 'notes': 'Timber set post'")
s=s.replace("'bottom': 340, 'surface': BEAM,\n             'notes': 'Cap of a timber set'","'bottom': 340, 'surface': MINEBEAM,\n             'notes': 'Cap of a timber set'")
s=s.replace("'bottom': 240, 'surface': BEAM,\n             'notes': 'Cap of a timber set'","'bottom': 240, 'surface': MINEBEAM,\n             'notes': 'Cap of a timber set'")
# king hall pillars and dais edge dressed
s=s.replace("pillars=[{'at': p, 'size': [224, 224], 'surface': BIGBLOCK}","pillars=[{'at': p, 'size': [224, 224], 'surface': DRESSED2}")
s=s.replace("'floor': -320, 'edge': BIGBLOCK,\n          'surface': INLAY,","'floor': -320, 'edge': DRESSED2,\n          'surface': INLAY,")
# hoard theme floor/reveal
s=s.replace("{'id': 'theme:hoard', 'wall': GOLDROCK, 'floor': INLAY, 'ceiling': GOLDDEEP, 'reveal': RUNES,","{'id': 'theme:hoard', 'wall': GOLDROCK, 'floor': TFB2, 'ceiling': GOLDDEEP, 'reveal': DEEP,")
# geode theme wall crystal-rock, vault family 7d24
s=s.replace("{'id': 'theme:geode', 'wall': EARTHROCK,","{'id': 'theme:geode', 'wall': CRYSTAL,")
s=s.replace("ceiling_surfaces=[{'steeper_than': 1.2, 'surface': EARTHROCK}],\n","")
s=s.replace("{'id': 'theme:dwarf_vault', 'wall': OLDBLOCK, 'floor': DARKFLAGS, 'ceiling': OLDBLOCK, 'reveal': RUNES,",
            "{'id': 'theme:dwarf_vault', 'wall': S('cwb', 128, 256), 'bands': [{'height': 96, 'surface': OLDBLOCK}], 'floor': S('7tfb1', 128, 128), 'ceiling': S('cwb', 128, 256), 'reveal': OLDBLOCK,")
# dome rings all geode rock, top ring the crystal cavity
for a,b in [("{'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': DEEP}","{'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': CRYSTAL}"),
            ("{'outline': r3, 'ceiling': 1088, 'top_outline': r4, 'edge': CRACKED}","{'outline': r3, 'ceiling': 1088, 'top_outline': r4, 'edge': CRYSTAL}"),
            ("{'outline': r4, 'ceiling': 1152, 'top_scale': 0, 'edge': CRACKED}","{'outline': r4, 'ceiling': 1152, 'top_scale': 0, 'edge': GEMWALL}")]:
    assert a in s, a; s=s.replace(a,b)
open('gen_rooms.py','w').write(s)
s=open('gen_objects.py').read()
s=s.replace("'surface': S('bmplnk', 256, 256), 'treasure_level': 2","'surface': S('7trimd', 128, 256), 'treasure_level': 2")
s=s.replace("'to': 'lavatyl'}","'to': 'orfyrlga'}")
open('gen_objects.py','w').write(s)
