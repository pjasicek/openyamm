"""Shared batch registration against native coverage landmarks, without per-pose fitting."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.optimize import minimize
from process import ROOT, queue, save, fix

def body(im):
    a = np.asarray(im.resize((128,128),Image.Resampling.BILINEAR)).astype(float)
    coverage = a[:,:,3]/255
    coverage *= np.clip(ndi.distance_transform_edt(a[:,:,3]>200)/2,0,1)
    return ndi.gaussian_filter(coverage,1)

def warp(a, values):
    scale, dx, dy = values
    offset = 64-(64+np.array([dy,dx]))/scale
    return ndi.affine_transform(a,np.eye(2)/scale,offset=offset,order=1,mode='constant')

