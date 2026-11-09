"""Round water contours without collapsing thin rivers; original, directed marching-squares implementation."""
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter1d


def rounded_water(mask, sigma, maximum_shift):
    padded = np.pad(mask.astype(np.uint8),1)
    cases = padded[:-1,:-1]+2*padded[:-1,1:]+4*padded[1:,1:]+8*padded[1:,:-1]
    # Edge order: top, right, bottom, left. Directed segments keep water on their right.
    segments = {1:[(0,3)],2:[(1,0)],3:[(1,3)],4:[(2,1)],5:[(0,3),(2,1)],6:[(2,0)],
                7:[(2,3)],8:[(3,2)],9:[(0,2)],10:[(1,0),(3,2)],11:[(1,2)],12:[(3,1)],
                13:[(0,1)],14:[(3,0)]}
    edges = {}
    for y,x in zip(*np.nonzero((cases>0)&(cases<15))):
        points = [(2*x+1,2*y),(2*x+2,2*y+1),(2*x+1,2*y+2),(2*x,2*y+1)]
        for a,b in segments[int(cases[y,x])]:
            assert points[a] not in edges
            edges[points[a]] = points[b]
    contours = []
    while edges:
        start = next(iter(edges))
        point = start
        path = []
        while True:
            path.append(point)
            point = edges.pop(point)
            if point==start:
                break
        points = np.array(path,dtype=float)/2-.5
        signed_area = .5*np.sum(points[:,0]*np.roll(points[:,1],-1)-np.roll(points[:,0],-1)*points[:,1])
        lengths = np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1)
        distances = np.r_[0,np.cumsum(lengths)]
        samples = np.arange(0,distances[-1],1.)
        points = np.vstack((points,points[0]))
        uniform = np.stack([np.interp(samples,distances,points[:,axis]) for axis in [0,1]],axis=1)
        local_sigma = min(sigma,max(0.5,len(uniform)/16))
        smooth = gaussian_filter1d(uniform,local_sigma,axis=0,mode='wrap')
        delta = smooth-uniform
        delta *= np.minimum(1,maximum_shift/np.maximum(np.linalg.norm(delta,axis=1),1e-6))[:,None]
        smooth = uniform+delta
        for axis,extent in [(0,mask.shape[1]),(1,mask.shape[0])]:
            boundary = (uniform[:,axis]<=.5)|(uniform[:,axis]>=extent-.5)
            smooth[boundary,axis] = uniform[boundary,axis]
        contours.append((abs(signed_area),signed_area>0,smooth))
    canvas = Image.new('L',(mask.shape[1],mask.shape[0]))
    draw = ImageDraw.Draw(canvas)
    for area,water,points in sorted(contours,key=lambda r:-r[0]):
        if len(points)>=3:
            draw.polygon([tuple(p) for p in points],fill=255 if water else 0)
    return np.array(canvas)>127
