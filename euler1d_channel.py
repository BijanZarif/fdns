import matplotlib
matplotlib.interactive(True)

import time
from pylab import *
from numpy import *
from numpad import *

gamma, R = 1.4, 287.

def T_ratio(M2):
    return 1 + (gamma - 1) / 2 * M2

def p_ratio(M2):
    return T_ratio(M2)**(gamma / (gamma - 1))

def inlet_condition(pt, Tt, p_over_rhoc_minus_u):
    def inlet_resid(w):
        r, ru, p = w
        T = p / (r**2 * R)
        c2 = gamma * p / r**2
        M2 = (ru / r)**2 / c2
        p_diff = pt - p * p_ratio(M2)
        T_diff = Tt - T * T_ratio(M2)
        p_over_rhoc = p / (r**2 * sqrt(c2))
        u_diff = p_over_rhoc_minus_u - (p_over_rhoc - ru / r)
        return array([p_diff, T_diff, u_diff])
    r_guess = value(sqrt(pt / (R * Tt)))
    w_guess = np.array([r_guess, 0.0, value(pt)])
    return solve(inlet_resid, w_guess, verbose=False)

T0, p0, M0 = 300., 101325., 0.5

pt_in = p0 * p_ratio(M0**2)
Tt_in = T0 * T_ratio(M0**2)
p_out = p0

rho0 = p0 / (R * T0)
c0 = sqrt(gamma * p0 / rho0)
u0 = c0 * M0

L = 10.
dx = 0.02
dt = dx / u0
N = int(L / dx)
x = arange(N) * dx + 0.5 * dx

def diffx(w):
    return (w[2:] - w[:-2]) / (2 * dx)

def rhs(w):
    r, ru, p = w[:,0], w[:,1], w[:,2]
    u = ru / r
    rhs_w = zeros(w[1:-1].shape)
    rhs_w[:,0] = 0.5 * diffx(r * ru) / r[1:-1]
    rhs_w[:,1] = ((diffx(ru*ru) + (r*ru)[1:-1] * diffx(u)) / 2.0 \
                + diffx(p)) / r[1:-1]
    rhs_w[:,2] = gamma * diffx(p * u) - (gamma - 1) * u[1:-1] * diffx(p)
    return rhs_w

def apply_bc(w):
    w_ext = zeros([w.shape[0] + 2, w.shape[1]])
    w_ext[1:-1] = w

    # inlet
    r, ru, p = w[0,:]
    c2 = gamma * p / r**2
    rhoc = sqrt(gamma) * sqrt(p) * r
    w_ext[0,:] = inlet_condition(pt_in, Tt_in, p / rhoc - ru / r)
    # w_ext[0,:] = [rho0, w[0,1], pt_in - 0.5 * w[0,1]**2]

    # outlet
    r, ru, p = w[-1,:]
    c2 = gamma * p / r**2
    rhoc = sqrt(gamma) * sqrt(p) * r

    dp = p_out - p
    dr = dp / (2 * r * c2)
    du = -dp / rhoc
    dru = r * du + (ru / r) * dr
    w_ext[-1,:] = [w[-1,0] + dr, w[-1,1] + dru, w[-1,2] + dp]
    return w_ext

def midpoint_res(w1, w0):
    w_ext = apply_bc(0.5 * (w0 + w1))
    return (w1 - w0) / dt + rhs(w_ext)

def conserved(w):
    r, ru, p = w[:,0], w[:,1], w[:,2]
    rho, u = r * r, ru / r
    mass = rho.sum()
    momentum = (rho * u).sum()
    energy = (p / (gamma - 1) + 0.5 * ru * ru).sum()
    return mass, momentum, energy

def ddt_conserved(w, rhs_w):
    r, ru, p = w[:,0], w[:,1], w[:,2]
    rho, u = r * r, ru / r
    ddt_rho = -rhs_w[:,0] * 2 * r
    ddt_rhou = -rhs_w[:,1] * r + 0.5 * u * ddt_rho
    ddt_p = -rhs_w[:,2]
    ddt_rhou2 = 2 * u * ddt_rhou - u**2 * ddt_rho

    ddt_mass = ddt_rho.sum()
    ddt_momentum = ddt_rhou.sum()
    ddt_energy = ddt_p.sum() / (gamma - 1) + 0.5 * ddt_rhou2.sum()
    return ddt_mass, ddt_momentum, ddt_energy

wave = 1 + 0.1 * sin(x / L * pi)**32
rho = rho0 * wave
p = p0 * wave**gamma
u = u0 * ones(wave.shape)

w = zeros([N, 3])
w[:,0] = sqrt(rho)
w[:,1] = sqrt(rho) * u
w[:,2] = p

# w *= 0.9 + 0.2 * random.random(w.shape)

print(ddt_conserved(w, rhs(apply_bc(w))))

print(conserved(w))

for iplot in range(50):
    for istep in range(10):
        # w = solve(midpoint_res, w, (w,))
        w = solve(midpoint_res, w, (w,), verbose=False)
        w.obliviate()
    r, ru, p = w[:,0], w[:,1], w[:,2]
    rho, u = r * r, ru / r
    cla()
    plot(rho / rho0)
    plot(u / u0)
    plot(p / p0)
    draw()
    time.sleep(0.5)
    print(conserved(w))

