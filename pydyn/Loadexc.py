# Copyright (C) 2009 Stijn Cole <stijn.cole@esat.kuleuven.be>
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

from numpy import copy

def Loadexc(casefile_dyn):
    """ Loads exciter data.

    @param casefile_dyn: m-file or struct with dynamic data
    @return: exciter parameter matrix

    @see: U{http://www.esat.kuleuven.be/electa/teaching/matdyn/}
    """
    # Load data
    if isinstance(casefile_dyn, dict):
        exc = casefile_dyn["exc"]
    else:
        dyn = __import__(casefile_dyn)
        _, exc, _, _, _, _ = eval("dyn.%s" % casefile_dyn)

    ## Consecutive numbering or rows
    Pexc = copy(exc)

    for i in range(len(exc[0, :])):
        Pexc[exc[:, 0], i] = exc[:, i]

    return Pexc
