"""Insert the AI ridge repair with periodic Poisson constraints; no copied border strips."""
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import splu


def repair(original, painted, width=80):
    size=original.shape[0]
    yy,xx=np.mgrid[:size,:size]
    mask=(abs(xx-(size-1)/2)<width)|(abs(yy-(size-1)/2)<width)
    indices=np.full((size,size),-1,dtype=int)
    indices[mask]=np.arange(mask.sum())
    rows,columns=np.where(mask)
    matrix=lil_matrix((mask.sum(),mask.sum()));matrix.setdiag(4)
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        other=indices[(rows+dy)%size,(columns+dx)%size]
        valid=other>=0
        matrix[np.arange(len(rows))[valid],other[valid]]=-1
    solve=splu(matrix.tocsc())
    shifted=np.roll(original,(size//2,size//2),(0,1))
    rhs=np.zeros_like(painted[mask])
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        sy,sx=(rows+dy)%size,(columns+dx)%size
        gradient=painted[mask]-painted[sy,sx]
        wraps=(rows+dy<0)|(rows+dy>=size)|(columns+dx<0)|(columns+dx>=size)
        continuation=.5*(painted[(rows-dy)%size,(columns-dx)%size]-painted[mask]
                         +painted[sy,sx]-painted[(sy+dy)%size,(sx+dx)%size])
        gradient[wraps]=continuation[wraps]
        rhs+=gradient
        outside=~mask[sy,sx]
        rhs[outside]+=shifted[sy[outside],sx[outside]]
    result=shifted.copy();result[mask]=solve.solve(rhs)
    result=np.roll(result,(-size//2,-size//2),(0,1))
    assert np.array_equal(result[width:-width,width:-width],original[width:-width,width:-width])
    return result
