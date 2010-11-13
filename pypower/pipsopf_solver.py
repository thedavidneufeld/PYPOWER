# Copyright (C) 2000-2010 Power System Engineering Research Center (PSERC)
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

from numpy import array, ones, zeros, nonzero, Inf, pi, exp, conj, r_

from idx_bus import BUS_TYPE, REF, VM, VA, MU_VMAX, MU_VMIN, LAM_P, LAM_Q
from idx_brch import F_BUS, T_BUS, RATE_A, PF, QF, PT, QT, MU_SF, MU_ST
from idx_gen import GEN_BUS, PG, QG, VG, MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN
from idx_cost import MODEL, PW_LINEAR, NCOST

from makeYbus import makeYbus
from opf_costfcn import opf_costfcn
from opf_consfcn import opf_consfcn
from opf_hessfcn import opf_hessfcn
from pips import pips
from util import sub2ind

def pipsopf_solver(om, ppopt, out_opt=None):
    """Solves AC optimal power flow using PIPS.

    Inputs are an OPF model object, a MATPOWER options vector and
    a struct containing fields (can be empty) for each of the desired
    optional output fields.

    Outputs are a RESULTS struct, SUCCESS flag and RAW output struct.

    RESULTS is a MATPOWER case struct (ppc) with the usual baseMVA, bus
    branch, gen, gencost fields, along with the following additional
    fields:
        - C{order}      see 'help ext2int' for details of this field
        - C{x}          final value of optimization variables (internal order)
        - C{f}          final objective function value
        - C{mu}         shadow prices on ...
            - C{var}
                - C{l}  lower bounds on variables
                - C{u}  upper bounds on variables
            - C{nln}
                - C{l}  lower bounds on non-linear constraints
                - C{u}  upper bounds on non-linear constraints
            - C{lin}
                - C{l}  lower bounds on linear constraints
                - C{u}  upper bounds on linear constraints
        - C{g}          (optional) constraint values
        - C{dg}         (optional) constraint 1st derivatives
        - C{df}         (optional) obj fun 1st derivatives(not yet implemented)
        - C{d2f}        (optional) obj fun 2nd derivatives(not yet implemented)

    SUCCESS     1 if solver converged successfully, 0 otherwise

    RAW         raw output in form returned by MINOS
        .xr     final value of optimization variables
        .pimul  constraint multipliers
        ["iN"]fo   solver specific termination code
        .output solver specific output information

    @see: L{opf}, L{mips}
    """
    ##----- initialization -----
    ## optional output
    if out_opt is None:
        out_opt = {}

    ## options
    verbose = ppopt[31]    ## VERBOSE
    feastol = ppopt[81]    ## PDIPM_FEASTOL
    gradtol = ppopt[82]    ## PDIPM_GRADTOL
    comptol = ppopt[83]    ## PDIPM_COMPTOL
    costtol = ppopt[84]    ## PDIPM_COSTTOL
    max_it  = ppopt[85]    ## PDIPM_MAX_IT
    max_red = ppopt[86]    ## SCPDIPM_RED_IT
    step_control = (ppopt[11] == 565)  ## OPF_ALG == 565, PIPS-sc
    if feastol == 0:
        feastol = ppopt[16]    ## = OPF_VIOLATION by default
    opt = {  'feastol': feastol,
             'gradtol': gradtol,
             'comptol': comptol,
             'costtol': costtol,
             'max_it': max_it,
             'max_red': max_red,
             'step_control': step_control,
             'cost_mult': 1e-4,
             'verbose': verbose  }

    ## unpack data
    ppc = om.get_ppc()
    baseMVA, bus, gen, branch, gencost = \
        ppc["baseMVA"], ppc["bus"], ppc["gen"], ppc["branch"], ppc["gencost"]
    vv, ll, nn = om.get_idx()

    ## problem dimensions
    nb = bus.shape[0]          ## number of buses
    nl = branch.shape[0]       ## number of branches
    ny = om.getN('var', 'y')   ## number of piece-wise linear costs

    ## linear constraints
    A, l, u = om.linear_constraints()

    ## bounds on optimization vars
    x0, xmin, xmax = om.getv()

    ## build admittance matrices
    Ybus, Yf, Yt = makeYbus(baseMVA, bus, branch)

    ## try to select an interior initial point
    ll = xmin, uu = xmax
    ll[xmin == -Inf] = -1e10   ## replace Inf with numerical proxies
    uu[xmax ==  Inf] =  1e10
    x0 = (ll + uu) / 2
    Varefs = bus[bus[:, BUS_TYPE] == REF, VA] * (pi / 180)
    ## angles set to first reference angle
    x0[vv["i1"]["Va"]:vv["iN"]["Va"]] = Varefs[0]
    if ny > 0:
        ipwl = nonzero(gencost[:, MODEL] == PW_LINEAR)
#         PQ = r_[gen[:, PMAX], gen[:, QMAX]]
#         c = totcost(gencost[ipwl, :], PQ[ipwl])
        c = gencost(sub2ind(gencost.shape, ipwl, NCOST+2*gencost[ipwl, NCOST]))    ## largest y-value in CCV data
        x0[vv["i1"]["y"]:vv["iN"]["y"]] = max(c) + 0.1 * abs(max(c))
#        x0[vv["i1"]["y"]:vv["iN"]["y"]] = c + 0.1 * abs(c)

    ## find branches with flow limits
    il = nonzero(branch[:, RATE_A] != 0 & branch[:, RATE_A] < 1e10)
    nl2 = len(il)           ## number of constrained lines

    ##-----  run opf  -----
    f_fcn = opf_costfcn#(x, om)
    gh_fcn = opf_consfcn#(x, om, Ybus, Yf(il,:), Yt(il,:), ppopt, il)
    hess_fcn = opf_hessfcn#(x, Lmbda, om, Ybus, Yf(il,:), Yt(il,:), ppopt, il, opt.cost_mult)
    x, f, info, Output, Lmbda = \
      pips(f_fcn, x0, A, l, u, xmin, xmax, gh_fcn, hess_fcn, opt)
    success = (info > 0)

    ## update solution data
    Va = x[vv["i1"]["Va"]:vv["iN"]["Va"]]
    Vm = x[vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    Pg = x[vv["i1"]["Pg"]:vv["iN"]["Pg"]]
    Qg = x[vv["i1"]["Qg"]:vv["iN"]["Qg"]]
    V = Vm * exp(1j*Va)

    ##-----  calculate return values  -----
    ## update voltages & generator outputs
    bus[:, VA] = Va * 180 / pi
    bus[:, VM] = Vm
    gen[:, PG] = Pg * baseMVA
    gen[:, QG] = Qg * baseMVA
    gen[:, VG] = Vm[gen[:, GEN_BUS]]

    ## compute branch flows
    Sf = V[branch[:, F_BUS]] * conj(Yf * V)  ## cplx pwr at "from" bus, p["u"].
    St = V[branch[:, T_BUS]] * conj(Yt * V)  ## cplx pwr at "to" bus, p["u"].
    branch[:, PF] = Sf.real * baseMVA
    branch[:, QF] = Sf.imag * baseMVA
    branch[:, PT] = St.real * baseMVA
    branch[:, QT] = St.imag * baseMVA

    ## line constraint is actually on square of limit
    ## so we must fix multipliers
    muSf = zeros(nl)
    muSt = zeros(nl)
    if il.any():
        muSf[il] = \
            2 * Lmbda["ineqnonlin"][:nl2] * branch[il, RATE_A] / baseMVA
        muSt[il] = \
            2 * Lmbda["ineqnonlin"][nl2:nl2+nl2] * branch[il, RATE_A] / baseMVA

    ## update Lagrange multipliers
    bus[:, MU_VMAX]  = Lmbda["upper"][vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    bus[:, MU_VMIN]  = Lmbda["lower"][vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    gen[:, MU_PMAX]  = Lmbda["upper"][vv["i1"]["Pg"]:vv["iN"]["Pg"]] / baseMVA
    gen[:, MU_PMIN]  = Lmbda["lower"][vv["i1"]["Pg"]:vv["iN"]["Pg"]] / baseMVA
    gen[:, MU_QMAX]  = Lmbda["upper"][vv["i1"]["Qg"]:vv["iN"]["Qg"]] / baseMVA
    gen[:, MU_QMIN]  = Lmbda["lower"][vv["i1"]["Qg"]:vv["iN"]["Qg"]] / baseMVA
    bus[:, LAM_P] = \
        Lmbda["eqnonlin"][nn["i1"]["Pmis"]:nn["iN"]["Pmis"]] / baseMVA
    bus[:, LAM_Q] = \
        Lmbda["eqnonlin"][nn["i1"]["Qmis"]:nn["iN"]["Qmis"]] / baseMVA
    branch[:, MU_SF] = muSf / baseMVA
    branch[:, MU_ST] = muSt / baseMVA

    ## package up results
    nlnN = om.getN('nln')

    ## extract multipliers for non-linear constraints
    kl = nonzero(Lmbda["eqnonlin"] < 0)
    ku = nonzero(Lmbda["eqnonlin"] > 0)
    nl_mu_l = zeros(nlnN)
    nl_mu_u = r_[zeros(2*nb), muSf, muSt]
    nl_mu_l[kl] = -Lmbda["eqnonlin"][kl]
    nl_mu_u[ku] =  Lmbda["eqnonlin"][ku]

    mu = {
      'var': {'l': Lmbda["lower"], 'u': Lmbda["upper"]},
      'nln': {'l': nl_mu_l, 'u': nl_mu_u},
      'lin': {'l': Lmbda["mu_l"], 'u': Lmbda["mu_u"]} }

    results = ppc
    results["bus"], results["branch"], results["gen"], \
        results["om"], results["x"], results["mu"], results["f"] = \
            bus, branch, gen, om, x, mu, f

    ## optional fields
    if out_opt.has_key('dg'):
        g, geq, dg, dgeq = opf_consfcn(x, om, Ybus, Yf, Yt, ppopt)
        results["g"]  = r_[ geq, g] ## include this since we computed it anyway
        results["dg"] = r_[ dgeq.T, dg.T] ## true Jacobian organization
    if out_opt.has_key('g') and not g.any():
        g, geq = opf_consfcn(x, om, Ybus, Yf, Yt, ppopt)
        results["g"] = r_[ geq, g]
    if out_opt.has_key('df'):
        results.df = array([])
    if out_opt.has_key('d2f'):
        results.d2f = array([])
    pimul = r_[
        results["mu"]["nln"]["l"] - results["mu"]["nln"]["u"],
        results["mu"]["lin"]["l"] - results["mu"]["lin"]["u"],
        -ones(ny > 0),
        results["mu"]["var"]["l"] - results["mu"]["var"]["u"],
    ]
    raw = {'xr': x, 'pimul': pimul, 'info': info, 'output': Output}

    return results, success, raw
