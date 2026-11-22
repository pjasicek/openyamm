#!/usr/bin/env python3
"""The engine's random yaw (degrees) for a decoration model at (x, y): game/maps/DecorationModelSet.cpp placementRandom."""
import sys
M=0xffffffff
def r(x,y,salt=2):
    h=((x*0x9e3779b1)&M) ^ ((y*0x85ebca77)&M) ^ ((salt*0xc2b2ae3d)&M)
    h^=h>>15; h=(h*0x2c1b3c6d)&M; h^=h>>12; h=(h*0x297a2d39)&M; h^=h>>15
    return (h&0xffffff)/0x1000000
def yaw(x,y): return r(x&M,y&M)*360
if __name__=='__main__':
    for a in sys.argv[1:]:
        x,y=map(int,a.split(',')); print(a, round(yaw(x,y),1))
