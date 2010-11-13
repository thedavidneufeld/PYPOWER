# Copyright (C) 1996-2010 Power System Engineering Research Center (PSERC)
# Copyright (C) 2010 Richard Lincoln <r.w.lincoln@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA, USA

from numpy import ones, zeros, r_

from idx_cost import MODEL, COST, NCOST, PW_LINEAR

from totcost import totcost

def poly2pwl(polycost, Pmin, Pmax, npts):
    """Converts polynomial cost variable to piecewise linear.
    PWLCOST = POLY2PWL(POLYCOST, PMIN, PMAX, NPTS) converts the polynomial
    cost variable POLYCOST into a piece-wise linear cost by evaluating at
    zero and then at NPTS evenly spaced points between PMIN and PMAX. If
    PMIN <= 0 (such as for reactive power, where P really means Q) it just
    uses NPTS evenly spaced points between PMIN and PMAX.

    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    pwlcost = polycost
    ## size of piece being changed
    m, n = polycost.shape
    ## change cost model
    pwlcost[:, MODEL]  = PW_LINEAR * ones(m)
    ## zero out old data
    pwlcost[:, COST:COST + n] = zeros(pwlcost[:, COST:COST + n].shape)
    ## change number of data points
    pwlcost[:, NCOST]  = npts * ones(m)

    for i in range(m):
        if Pmin[i] == 0:
            step = (Pmax[i] - Pmin[i]) / (npts - 1)
            xx = range(Pmin[i], step, Pmax[i])
        elif Pmin[i] > 0:
            step = (Pmax[i] - Pmin[i]) / (npts - 2)
            xx = r_[0, range(Pmin[i], step, Pmax[i])]
        elif Pmin[i] < 0 & Pmax[i] > 0:        ## for when P really means Q
            step = (Pmax[i] - Pmin[i]) / (npts - 1)
            xx = range(Pmin[i], step, Pmax[i])
        yy = totcost(polycost[i, :], xx)
        pwlcost[i,      COST:2:(COST + 2*(npts-1)    )] = xx
        pwlcost[i,  (COST+1):2:(COST + 2*(npts-1) + 1)] = yy

    return pwlcost
