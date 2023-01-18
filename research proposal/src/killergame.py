# Let firms play the killer game!
import numpy as np
from scipy.stats import pareto
from scipy import optimize
#import scipy as sp
from prodgrid import gen_prod_grid
#import plotly.express as px
#import plotly.io as pio
#pio.templates.default = "plotly_white"
from aggregate import agg_equilibrium

#import pandas as pd

#import ipdb

alpha = 6
gamma = 10.5
theta = 1.24
n_incumb = 100
n_industries = 2
rhoE = 0.1

prod_grid, probs = np.array([1.135, 4.35]), np.array([1-rhoE, rhoE])
z_large = prod_grid[-1] # Industry dominant firm has the high productivity
z_fringe = np.repeat(prod_grid[0], n_incumb) # Fringe has the low productivity

z_entrants = np.random.choice(prod_grid, size = 1, p = probs)

z_draws = np.insert(z_fringe, 0, z_large)
z_draws = np.insert(z_draws, -1, z_entrants)

z_draws = np.expand_dims(z_draws, 0)
#prod_grid = np.expand_dims(prod_grid[0], axis = 0)
#probs = np.expand_dims(1, axis = 0)

# TODO maybe change approach to compute values assuming acquisition, then assuming no acquisition, and pick true value. 

c_curvature = 0
c_shifter = 2e-4
L_SUPPLY = 1

profit_large, share_large, avg_firms, hh_welfare, W, Y, prices_j = agg_equilibrium(L_SUPPLY, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, "Bertrand", 1, "figures/parta")



# Remember how I did it, incumbent maximises profits given potential outcomes. 
from scipy.optimize import minimize_scalar

sol = minimize_scalar(lambda x: agg_eq_ka(int(x), int(avg_firms), profit_large, gamma, theta, c_shifter, c_curvature), bounds = (2, avg_firms), method = "bounded", options = {"xatol" : 0.9})




f = open("agg_values_partb.txt", "w")
f.write("L_prod:" + str(Lprod) + "\n L_supply:" + str(L_supply) + "\n Z" + str(Z) + "\n Markup: " + str(Markup))
f.close()

f = open("total_labor.txt", "w")
f.write(str(L_supply))
f.close()




