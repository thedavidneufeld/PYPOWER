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

from numpy import array, zeros, nonzero, linalg, Inf, r_
from scipy.sparse import csr_matrix

from idx_gen import PC1, PC2, QC1MIN, QC1MAX, QC2MIN, QC2MAX

from hasPQcap import hasPQcap

def makeApq(baseMVA, gen):
    """Construct linear constraints for generator capability curves.

    Constructs the parameters for the following linear constraints
    implementing trapezoidal generator capability curves, where
    Pg and Qg are the real and reactive generator injections.

    APQH * [Pg Qg] <= UBPQH
    APQL * [Pg Qg] <= UBPQL

    DATA constains additional information as shown below.

    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    data = {}
    ## data dimensions
    ng = gen.shape[0]      ## number of dispatchable injections

    ## which generators require additional linear constraints
    ## (in addition to simple box constraints) on (Pg,Qg) to correctly
    ## model their PQ capability curves
    ipqh = nonzero( hasPQcap(gen, 'U') )
    ipql = nonzero( hasPQcap(gen, 'L') )
    npqh = ipqh.shape[0]   ## number of general PQ capability curves (upper)
    npql = ipql.shape[0]   ## number of general PQ capability curves (lower)

    ## make Apqh if there is a need to add general PQ capability curves
    ## use normalized coefficient rows so multipliers have right scaling
    ## in $$/pu
    if npqh > 0:
        data["h"] = r_[gen[ipqh, QC1MAX] - gen[ipqh, QC2MAX],
                       gen[ipqh, PC2] - gen[ipqh, PC1]]
        ubpqh = data["h"][:, 1] * gen[ipqh, PC1] + \
                data["h"][:, 2] * gen[ipqh, QC1MAX]
        for i in range(npqh):
            tmp = linalg.norm(data["h"][i, :], Inf)
            data["h"][i, :] = data["h"][i, :] / tmp
            ubpqh[i] = ubpqh[i] / tmp
        Apqh = csr_matrix((data["h"][:],
                           (r_[range(npqh), range(npqh)], r_[ipqh, ipqh+ng])),
                           (npqh, 2*ng))
        ubpqh = ubpqh / baseMVA
    else:
        data["h"] = array([])
        Apqh  = zeros((0, 2*ng))
        ubpqh = array([])

    ## similarly Apql
    if npql > 0:
        data["l"] = r_[gen[ipql, QC2MIN] - gen[ipql, QC1MIN],
                       gen[ipql, PC1] - gen[ipql, PC2]]
        ubpql = data["l"][:, 1] * gen[ipql, PC1] + \
                data["l"][:, 2] * gen[ipql, QC1MIN]
        for i in range(npql):
            tmp = linalg.norm(data["l"][i, :], Inf)
            data["l"][i, :] = data["l"][i, :] / tmp
            ubpql[i] = ubpql[i] / tmp
        Apql = csr_matrix((data["l"][:],
                           (r_[range(npql), range(npql)], r_[ipql, ipql+ng])),
                           (npql, 2*ng))
        ubpql = ubpql / baseMVA
    else:
        data["l"] = array([])
        Apql  = zeros((0, 2 * ng))
        ubpql = array([])

    data["ipql"] = ipql
    data["ipqh"] = ipqh

    return Apqh, ubpqh, Apql, ubpql, data
