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

from numpy import ones, zeros, copy

from idx_bus import BS
from idx_brch import BR_B, BR_R, TAP, SHIFT

from makeYbus import makeYbus

def makeB(baseMVA, bus, branch, alg):
    """Builds the FDPF matrices, B prime and B double prime.

    Returns the two matrices B prime and B double prime used in the fast
    decoupled power flow. Does appropriate conversions to p.u. ALG is the
    value of the PF_ALG option specifying the power flow algorithm.

    @see: L{fdpf}
    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    ## constants
    nb = bus.shape[0]          ## number of buses
    nl = branch.shape[0]       ## number of lines

    ##-----  form Bp (B prime)  -----
    temp_branch = copy(branch)                 ## modify a copy of branch
    temp_bus = copy(bus)                       ## modify a copy of bus
    temp_bus[:, BS] = zeros(nb)                ## zero out shunts at buses
    temp_branch[:, BR_B] = zeros(nl)           ## zero out line charging shunts
    temp_branch[:, TAP] = ones(nl)             ## cancel out taps
    if alg == 2:                               ## if XB method
        temp_branch[:, BR_R] = zeros(nl)       ## zero out line resistance
    Bp = -makeYbus(baseMVA, temp_bus, temp_branch).imag

    ##-----  form Bpp (B double prime)  -----
    temp_branch = copy(branch)                 ## modify a copy of branch
    temp_branch[:, SHIFT] = zeros(nl)          ## zero out phase shifters
    if alg == 3:                               ## if BX method
        temp_branch[:, BR_R] = zeros(nl)    ## zero out line resistance
    Bpp = -makeYbus(baseMVA, bus, temp_branch).imag

    return Bp, Bpp
