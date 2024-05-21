# Copyright (c) 1996-2015 PSERC. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Runs an optimal power flow.
"""

from sys import stdout, stderr

from os.path import dirname, join

from pypower.ppoption import ppoption
from pypower.opf import opf
from pypower.printpf import printpf
from pypower.savecase import savecase
from pypower.case9 import case9
from pypower.case4gs import case4gs
from pypower.case6ww import case6ww
from pypower.case14 import case14
from pypower.case24_ieee_rts import case24_ieee_rts
from pypower.case30 import case30
from pypower.case39 import case39
from pypower.case57 import case57
from pypower.case118 import case118
from pypower.case300 import case300

def runopf(casedata=None, ppopt=None, fname='', solvedcase=''):
    """Runs an optimal power flow.

    @see: L{rundcopf}, L{runuopf}

    @author: Ray Zimmerman (PSERC Cornell)
    """
    ## default arguments
    if casedata is None:
        casedata = join(dirname(__file__), 'case9')
    ppopt = ppoption(ppopt)

    ##-----  run the optimal power flow  -----
    r = opf(casedata, ppopt)

    ##-----  output results  -----
    if fname:
        fd = None
        try:
            fd = open(fname, "a")
        except IOError as detail:
            stderr.write("Error opening %s: %s.\n" % (fname, detail))
        finally:
            if fd is not None:
                printpf(r, fd, ppopt)
                fd.close()

    else:
        printpf(r, stdout, ppopt)

    ## save solved case
    if solvedcase:
        savecase(solvedcase, r)

    return r


if __name__ == '__main__':

    #print('Case 9...................')
    #ppc = case9()
    ppopt = ppoption(OPF_ALG=560, VERBOSE=2)
    #runopf(ppc, ppopt)

    #print('Case 4gs...................')
    #ppc = case4gs()
    #runopf(ppc, ppopt)

    print('Case 6ww...................')
    ppc = case6ww()
    runopf(ppc, ppopt)

    print('Case 14...................')
    ppc = case14()
    runopf(ppc, ppopt)

    print('Case 24 ieee rts...................')
    ppc = case24_ieee_rts()
    runopf(ppc, ppopt)

    print('Case 30...................')
    ppc = case30()
    runopf(ppc, ppopt)

    print('Case 39...................')
    ppc = case39()
    runopf(ppc, ppopt)

    print('Case 57...................')
    ppc = case57()
    runopf(ppc, ppopt)

    print('Case 118...................')
    ppc = case118()
    runopf(ppc, ppopt)

    print('Case 300...................')
    ppc = case300()
    runopf(ppc, ppopt)

