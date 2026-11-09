"""Compose native-shaped grey fringe art and quilt shared finished edge strips."""
import json
import cv2
from PIL import ImageDraw
from scipy.ndimage import gaussian_filter, binary_opening, binary_closing, binary_dilation
from common import *

F = P / 'transitions/grey_family_v1'
AI = P / 'transitions/grey_fringe_ai'


def local_art(name, background, foreground, new_bg, new_fg):
    native = read(P / 'references' / (name + '.png'), 512)
    generated = read(AI / 'raw' / (name + '.png'), 512)
    grey = lambda a: seams.byte(gaussian_filter(a.mean(2), 4))
    flow = cv2.calcOpticalFlowFarneback(grey(native), grey(generated), None, .5, 4, 45, 5, 7, 1.5, 0)
    flow = gaussian_filter(flow, (5, 5, 0))
    yy, xx = np.mgrid[:512, :512]
    aligned = cv2.remap(generated.astype('float32'), (xx + flow[:, :, 0]).astype('float32'),
                       (yy + flow[:, :, 1]).astype('float32'), cv2.INTER_CUBIC,
                       borderMode=cv2.BORDER_REPLICATE)
    restored = aligned + gaussian_filter(native - aligned, (12, 12, 0))
    fields = np.load(P / 'transitions/fields' / (name + '.npz'))
    alpha, shade = fields['coverage'], fields['shade']
    mix = seams.srgb(seams.linear(new_bg)*(1-alpha[:, :, None]) +
                     seams.linear(new_fg)*alpha[:, :, None])*shade[:, :, None]
    stone = gaussian_filter((background-native).mean(2), 3) > 7
    stone = binary_closing(binary_opening(stone, iterations=2), iterations=3)
    weight = gaussian_filter(binary_dilation(stone, iterations=8).astype(float), 3)
    exact = (np.max(abs(native-foreground),2)<4) | (np.max(abs(native-background),2)<4)
    local = gaussian_filter(binary_dilation(~exact, iterations=8).astype(float), 4)
    weight *= local
    return mix*(1-weight[:, :, None]) + restored*weight[:, :, None]


def minimum_cut(current, target):
    length = len(current)
    minimum = 24
    cost = np.mean((current-target)**2, axis=2)[minimum:length-4].T
    distance, back = cost.copy(), np.zeros(cost.shape, dtype='int16')
    for cross in range(1,512):
        previous = np.pad(distance[cross-1], (2,2), constant_values=np.inf)
        choices = np.stack([previous[i:i+cost.shape[1]] for i in range(5)])
        best = np.argmin(choices,axis=0)
        distance[cross] += np.min(choices,axis=0)
        back[cross] = np.arange(cost.shape[1])+best-2
    cut = np.empty(512,int); cut[-1] = np.argmin(distance[-1])
    for cross in range(510,-1,-1):
        cut[cross] = back[cross+1,cut[cross+1]]
    cut += minimum
    weight = np.clip((cut[None,:]-np.arange(length)[:,None]+2)/4,0,1)
    return weight*weight*(3-2*weight)


def graft(pixels, topology, donors, masters):
    result = pixels.copy()
    length = 128
    cross = np.arange(512)
    ends = np.minimum(cross,511-cross)
    keep_art = np.clip((ends-64)/48,0,1)[None,:,None]
    for side, contract in topology.items():
        indices = np.arange(length) if side in 'NW' else 511-np.arange(length)
        strip = lambda a: a[indices].copy() if side in 'NS' else a[:,indices].swapaxes(0,1).copy()
        current = strip(result)
        if contract in ('00','11'):
            target = strip(masters[int(contract[0])])
        else:
            axis = 'h' if side in 'NS' else 'v'
            donor = donors[(axis,contract)]
            samples = 256+np.arange(length) if side in 'NW' else 255-np.arange(length)
            target = donor[samples].copy() if side in 'NS' else donor[:,samples].swapaxes(0,1).copy()
            # Shared corners continue the authoritative periodic master in its
            # destination phase. Only the mixed centre carries donor edge artwork.
            pure = np.where((cross<256)[None,:,None],
                            strip(masters[int(contract[0])]),strip(masters[int(contract[1])]))
            target = target*keep_art + pure*(1-keep_art)
        weight = minimum_cut(current,target)[:, :, None]
        values = current*(1-weight)+target*weight
        if side in 'NS': result[indices] = values
        else: result[:,indices] = values.swapaxes(0,1)
    return result


def main():
    F.mkdir(parents=True,exist_ok=True)
    build = json.loads((P/'transitions/build.json').read_text())
    records = [r for r in build['tiles'] if r['family']=='grey_stone']
    background,foreground = [read(P/'references'/(n+'.png'),512) for n in ('gdtyl','gstyl')]
    masters = [read(M/'materials'/(n+'.png')) for n in ('grey_dirt','grey_stone')]
    art = {r['name']:local_art(r['name'],background,foreground,*masters) for r in records}
    donors = {('h','10'):art['gse'],('h','01'):art['gsw'],
              ('v','01'):art['gsn'],('v','10'):art['gss']}
    output = []
    for r in records:
        name=r['name']
        pixels = graft(art[name],r['topology'],donors,masters)
        save(F/'local_art'/(name+'.png'),art[name])
        save(F/'authoring'/(name+'.png'),pixels)
        save(F/'runtime'/(name+'.png'),seams.reduce(seams.pad(pixels,'edge')))
        output.append(dict(name=name,topology=r['topology'],runtime_sha256=sha(F/'runtime'/(name+'.png')),
                           authoring_sha256=sha(F/'authoring'/(name+'.png')),
                           raw_sha256=sha(AI/'raw'/(name+'.png'))))
    for start in range(0,len(output),4):
        rows=output[start:start+4]
        sheet=Image.new('RGB',(768,280*len(rows)),'#202933');draw=ImageDraw.Draw(sheet)
        for row,r in enumerate(rows):
            name=r['name']
            for col,path in enumerate((P/'references'/(name+'.png'),OUT/(name+'.png'),F/'runtime'/(name+'.png'))):
                sheet.paste(Image.open(path).convert('RGB').resize((256,256)),(col*256,row*280+24))
                draw.text((col*256+4,row*280+5),name+' '+['native','previous','shared art'][col],fill='white')
        sheet.save(F/('comparison_%d.png'%start))
    report=dict(status='candidate_shared_art_requires_join_and_visual_review',tiles=output,
                donor_sources={':'.join(k):n for k,n in [(('h','10'),'gse'),(('h','01'),'gsw'),
                                                        (('v','01'),'gsn'),(('v','10'),'gss')]},
                source_build_sha256=sha(P/'transitions/build.json'),script_sha256=sha(Path(__file__)))
    (F/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built',len(output),'grey-stone family candidates outside runtime union')


if __name__=='__main__': main()
