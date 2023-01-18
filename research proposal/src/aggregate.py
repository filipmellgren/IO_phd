# Functions related to aggregation
import numpy as np
from scipy import optimize
from industry import industry_equilibrium

def agg_variables(ratio, P, P_tildej, Z_js, markups, marginal_entrants, theta, c_shifter, c_curvature):
	''' Gives aggregated variables from industry variables
	Note, we use means to aggregate as there are infinitely tiny industries (integral 0 to 1)
	ratio is the W**(-theta) * Y guess
	'''
	W = find_wage(P_tildej, theta)
	Y = W**theta * ratio
	#Y = W**theta # TODO: slide 43, from labor demand of each firm? Maybe not in dynamic case. 
	Pj =  P_tildej * W 
	Yj = (Pj/P)**(-theta) * Y # Slide 19, L1
	costj = Yj / np.array(Z_js)
	# Slide 46, L1 + using relationship of industry markup to find expression for aggregate markup.
	Markup = ((P/W)**(1 - theta)) / np.mean(markups ** (-theta) * Z_js**(theta - 1))
	Z = (np.mean((markups/Markup)**(-theta) * Z_js**(theta-1)))**(1/(theta - 1))
	Lprod = Y/Z
	#L = Y / (Markup * W) # Slide 51 L1 Same as above for P = 1

	entry_labor = 0
	for jj in range(Z_js.size):
		entrant_vec = np.arange(marginal_entrants[jj] - 1) # Function takes incumbent as argument
		entry_labor += np.sum(get_entry_costs(W, c_shifter, entrant_vec, c_curvature))/W
	
	L_total = Lprod + entry_labor / Z_js.size
	avg_firms = np.mean(marginal_entrants)
	return(Lprod, L_total, W, Y, Z, Markup, costj, avg_firms)

def agg_eq_ka(k, firms_no_ka, profit_no_ka, gamma, theta, c_shifter, c_curvature):
	''' Computes aggregate equilibrium difference in profits when the initial firm acquires all firms following the kth entrant.

	Acquiring the kth entrant and everyoen afterwards (due to increasing costs to enter and same effect on profit_large as kth entrant) can be both profitable and not profitable.

	This function tells whether it is profitable to acquire everyuione following the kth entrant. 

	A key assumption is that the profit of the future entrants remains at the same constant value. Otherwise, an effect of acquiring a firm is that the future profits of potential entrants increases, and therefore the price for the incumbent. 
	TODO: should I change Pj to 1? 
	'''
	print(k)
	# Effect on profit_large comes from limiting number of entrants to k.
	# Everyone after k is acquired as cost of acquiring additional firms decrease while effect on profits is constant. 
	z_draws_limited = z_draws[:, 0:k]

	profit_large, share_large, avg_firms, hh_welfare, W, Y, Pj = agg_equilibrium(L_supply, c_curvature, c_shifter, z_draws_limited, prod_grid, probs, gamma, theta, "Bertrand", learning_rate, "figures/scrap")

	markup_s = gamma / (gamma - 1)
	Pj = 1 # TODO: think this normalization should be made as we know P = 1,
	# And there is only one industry (for problem set), so Pj = 1. 
	
	entry_profits = (1 - 1 / markup_s) * (markup_s * W / z_draws[:, k:firms_no_ka])**(1 - gamma) * Pj**(gamma - theta) * Y
	
	entry_costs = get_entry_costs(W, c_shifter, np.arange(k+1, firms_no_ka+1), c_curvature)

	acq_price = np.sum(entry_profits - entry_costs)

	net_profit_large = profit_large - acq_price
	
	return(profit_no_ka - net_profit_large)

def check_mc(ratio, L_supply, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate, path):
	''' Checks aggregate market clearing. 
	Use only after solving for an initial equilibrium, as it depends on L_supply which is only known after it has been solved for in equilibrium once. 
	ratio: is the W**(-theta) Y value using which firms decide whether to enter or not. It reduces the state space.

	For ratio = 1 = W = Y, L becomes the same as in Exc1 part b
	
	'''
	# Industry variables, arrays with one value per industry
	markups, prices_j, Z_js, marginal_entrants = [], [], [], []
	profits_large, shares_large = [], []

	for industry in range(z_draws.shape[0]):	
		z_draw = z_draws[industry, :]
		markupj, P_tildej, Zj, marginal_entrant, profit_large, share_large = industry_equilibrium(ratio, c_curvature, c_shifter, z_draw, prod_grid, probs, gamma, theta, competition, learning_rate) 

		markups.append(markupj)
		prices_j.append(P_tildej)
		Z_js.append(Zj)
		marginal_entrants.append(marginal_entrant)
		profits_large.append(profit_large)
		shares_large.append(share_large)
	
	P = 1 # Given by problem set

	Lprod, L, W_implied, Y_tilde, Z, Markup, costj, avg_firms = agg_variables(ratio, P, np.array(P_tildej), np.array(Z_js), np.array(markups), marginal_entrants, theta, c_shifter, c_curvature)
		
	share_large_avg = np.mean(np.array(shares_large))
	profit_large_avg = np.mean(np.array(profits_large) * Y_tilde)
	loss = L - L_supply
	markups = np.array(markups)
	
	return(loss, markups, np.array(prices_j), np.array(Z_js), Y_tilde, W_implied, avg_firms, profit_large_avg, share_large_avg, P)

def agg_equilibrium(L_supply, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate, path):
	''' Computes an aggregate equilibrium for the entry game economy. Returns cost weighted variables by each percentile

	# TODO: add case where W=Y = 1
	'''
	# Find market clearing value of X := W**(-theta)*Y
	X = optimize.bisect(lambda x: check_mc(x, L_supply, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate, path)[0], 1e-1, 1e+1, xtol = 1e-5)
	
	_, markups, prices_j, Z_js, Y, W, avg_firms, profit_large, share_large, P = check_mc(X, L_supply, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate, path)

	hh_welfare = get_hh_welfare(W, L_supply, P)
	# TODO: calculate overall firm profits so I can measure total welfare. 

	return(profit_large, share_large, avg_firms, hh_welfare, W, Y, prices_j)


def find_wage(Ptildej, theta):
	''' Find economy wage
	Slide 42, lecture 1
	Assumes aggregate good has a normalized price, P = 1
	'''
	
	W_inv = (np.mean(Ptildej**(1-theta)))**(1/(1-theta))
	
	W = W_inv**(-1)
	return(W)

def aggregate_Z(Zj, markupj, markup, theta):
	''' Slide 46, lecture 1
	Pj, Zj : arrays of values for all industries, each j in J.
	'''
	#Z = (np.mean(Zj * Pj**(gamma - theta)))**(-1)
	markup = Y / (W * L) # TODO What is this?
	Z = (np.mean((markupj/markup)**(-theta) * Zj**(theta-1)))**(1/(theta - 1))
	return(Z)

def get_hh_welfare(W, L_supply, P):
	''' Returns HH welfare
	Use BC and FOC on slide 40 to back out parameter psi, assuming rho = 2
	'''
	hh_c = W * L_supply / P # From BC
	rho = 2 # Assumption. TODO: make consistent with curvatures and shift?
	psi = -1/rho * np.log(hh_c * W / P) / np.log(L_supply) # Rewrite FOC
	hh_welfare = (hh_c**(1-rho)-1)/(1-rho) - 1/(psi + 1) * L_supply**(psi + 1)
	return(hh_welfare)


def get_entry_costs(W, c_shifter, n, c_curvature):
	''' n is the number of incumbents, so entry cost for marginal entrant uses n+1
	'''
	return(W * c_shifter * ((n+1) ** c_curvature))