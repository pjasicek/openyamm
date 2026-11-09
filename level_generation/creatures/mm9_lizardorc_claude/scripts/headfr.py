"""Head frame: Meshy head (glTF coordinates) -> fit frame (MM9). Uniform-ish: x .65, y and z .68, nose 3 deg up, snout tip on MM9's."""
import numpy as np
A=np.radians(3.); S=np.array([.65,.68,.68]); T=np.array([0.,.69,.13]); c,s=np.cos(A),np.sin(A)
HINGE=np.array([0,.72,.19]); GAPE_CLOSE=8.; MID_SLOPE=np.radians(19.)
PLANE_P=np.array([0,.612,.10]); PLANE_N=np.array([0,.98,.196]); PLANE_N=PLANE_N/np.linalg.norm(PLANE_N)    # under the chin, under the hood
def F(p):
    q=p*S; return np.c_[q[:,0],q[:,1]*c+q[:,2]*s,-q[:,1]*s+q[:,2]*c]+T
def Fi(p):
    q=p-T; return np.c_[q[:,0],q[:,1]*c-q[:,2]*s,q[:,1]*s+q[:,2]*c]/S
