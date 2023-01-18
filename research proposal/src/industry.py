# Industry equilibrium with killer acquisitions and not taking w**theta = Y = 1 as given
# This file assumes there exists an L_supply that can be obtained from np.loadtxt("total_labor.txt"). Running entrygame.py first creates that file. 

# TODO: This shouild be merged with industry_eq.py. Functions will need to be more general first. Currently incompatible as industry_eq.py is mostly based on taking W and Y as given whereas this file iterates over W**-theta * Y


import numpy as np
from scipy.stats import pareto
from scipy import optimize
import time
import scipy as sp
from prodgrid import gen_prod_grid
from numba import njit
import ipdb

def industry_equilibrium(ratio, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate):
	'''Simulate an industry, given prodcutivity draws.
	Three stage game based on Edmond, Midrigan, Xu (2022), with a killer acquisition phase added
		0th period: Incumbent decides whether to acquire potential entrant
		1st period: Entrants decide whether to enter. Incumbent decides whether to develop.
		2nd period: Static nested CES model
	
	INPUT :
	ratio : W**(-theta) * Y a guess of what this is. Want supply = demand so find this using bisection. Note, these are aggregates so find them in aggregate equilbirium.
	
	OUTPUT : 
	Variables summarising the industry state
	'''
 
	
	acquire_decision()
	
	# Extra entrants from knowing the dominant firm can acquire


	z_draws = z_draws[:int(marginal_firm)]

	markupj, Ptildej, Zj, profit_constant_large, share_large = static_competition(gamma, theta, z_draws, competition)

	return(markupj, Ptildej, Zj, int(marginal_entrant), profit_constant_large, share_large)

def static_competition(gamma, theta, z_draws, competition):
	''' Second stage: Static nested CES from lecture 1

	'''
	
	markups = get_markups(gamma, theta, z_draws, competition)
	
	Ptildej = price_aggregator(markups/z_draws, gamma) # Slide 42 L1

	markupj = (Ptildej**(1 - gamma)) / np.sum(markups ** (-gamma) * z_draws**(gamma - 1))
	
	# Slide 45 lecture 1
	Zj = (np.sum((markups/markupj)**(-gamma) * z_draws**(gamma - 1)))**(1/(gamma - 1))

	_, _, shares, _, _ = markup_diff(markups, z_draws, gamma, theta, competition)
	share_large = shares[0]
	profit_constant_large = (1-1/markups[0]) * share_large # Multiply by total output Y
	return(markupj, Ptildej, Zj, profit_constant_large, share_large)

def acquire_decision(n, ratio, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate):
	''' Calculate  entry owing from the dominant firm being able to acquire.
	
	Returns number of firms resulting from the decision to acquire.

	Key to this is to note that given the firm acquires, we compare values that do not depend on W and Y, these jsut scale both numerator and denominator equally.

	Whether to acquire depends on W

	* If acquire to kill: return n
	* If acquire to develop: return n+1
	* If not acquire: return n+1

	TODO return values for first firm within entry_decisions
	'''
	# prod_grid is the high and low value, probs are corresponding
	_, acq_price, V_no_acq = entry_decision(n, ratio, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate)
	
	probs_A = np.array([1 - rhoA, rhoA])
	_, V_dev1, V_dev2 = entry_decision(n, ratio, c_curvature, c_shifter, z_draws, prod_grid, probs_A, gamma, theta, competition, learning_rate) # Note: this is just the project in itself, does not yet take into account the lost profits from having an extra "competing" product
	V_dev = V_dev1 + V_dev2

	no_prod_grid = np.array([])
	no_probs = np.array([])
	_, V_dev1, V_kill = entry_decision(n, ratio, c_curvature, c_shifter, z_draws, no_prod_grid, no_probs, gamma, theta, competition, learning_rate)
	
	
	return(EV_acq)

def launch_decision():
	''' Entrepreneur decides whether to try out her idea.
	Will decide to develop if max(acquisition price, development value) > 0
	Start withou this possibility
	'''
	acquisition_price = 0

	dev_value = 0
	
	return(np.max(acquisition_price, dev_value) > 0)


def entry_decisions(n, ratio, c_curvature, c_shifter, z_draws, prod_grid, probs, gamma, theta, competition, learning_rate):
	''' Calculate net benefit to marginal entrant
	Find equilibrium. Probably unique ^_^.
	
	See slide 19 L2 on how the state is reduced

	TODO: aggregate small firms to one large firm Slide 15 L2 for a speed gain. 
	
	z_draws : is the incumbent productivity draws
	ratio : is W**(-theta) * Y which is what entry decisions ultimately depend on
	'''	
	# First value of enterring
	z_draws_incumbent = z_draws[:int(n)]
	
	enter_values_list = []
	value_incumbent_list = []

	for z_entrant in prod_grid:
		ipdb.set_trace()
		# Calc value proportional to profits
		z_draws_entrant = np.append(z_draws_incumbent, z_entrant)
		markups = get_markups(gamma, theta, z_draws_entrant, competition) # TODO: should I extract markups[0] and calculate value for incumbent here?
		Pj_divW = price_aggregator(markups / z_draws_entrant, gamma) # Should be multiplied by W
		enter_values = (1 - 1/markups) * (markups / z_draws_entrant)**(1-gamma) * Pj_divW**(gamma - theta) 
		enter_values_list.append(enter_values[-1])
		value_incumbent_list.append(enter_values[0])

	value_entering = np.array(enter_values_list) @ probs
	value_incumbent = np.array(value_incumbent_list) @ probs

	eps = c_shifter * (n+1) ** c_curvature
	decision = ratio * value_entering/eps -1 # We look for the root value and decision is enter if positive, otherwise not. 

	return(decision, value_entering, value_incumbent)

@njit
def get_markups(gamma, theta, z_draws, competition):
	''' Calculate markups given paramters, productivity, and type of compeition
	competition is either "Bertrand" or "Cournot".
	'''
	markup_guess = np.repeat(gamma / (gamma -1), repeats = np.size(z_draws))
	learning_rate = 0.5
	tol = 1e-7
	markups = markup_optim(markup_guess, learning_rate, z_draws, gamma, theta, competition, tol)
	return(markups)

@njit
def markup_optim(guess, learning_rate,  z_draws, gamma, theta, competition, tol):
	''' Find industry markups using Newton's method
	slide 27
	Markups here simply average cost
	NOTE: this seems to generate cycles depending on learning rate. For Cournot, Delta =1 might be too much.
	'''
	Delta = learning_rate
	error = tol + 10
	while error > tol: 
		error, markups, shares, elas, elas_grad = markup_diff(guess, z_draws, gamma, theta, competition)
		grad = 1 + ( 1/((elas-1)**2) ) * elas_grad * (1-gamma)*shares/guess
		guess = guess - Delta * error / grad
		error = np.sqrt(np.sum(error**2))
		
	return(guess)

@njit
def markup_diff(markup_guess, z_draws, gamma, theta, competition):
	''' Calculates difference betwee markup guess and implied markups
	
	Also returns markups, shares, and elasticities used along the way
	'''

	shares = ((markup_guess/z_draws)**(1-gamma))/(np.sum((markup_guess/z_draws)**(1-gamma)))
	
	if competition == "Bertrand":
		elas = (1 - shares)*gamma + shares * theta # Elasticity under Bertrand, slide 22, lecture 1
		elas_grad = -gamma + theta
	if competition == "Cournot":
		# Cournot seems less stable and leads to "overflow encountered in reduce"
		elas = ((1 - shares)*gamma**(-1) + shares*theta**(-1))**(-1)# Elasticity under cournot
		elas_grad = (1/theta - 1/gamma)/(( (1-shares) / gamma + shares / theta )**2)# For Cournot

	markups = elas/(elas - 1)

	loss = markup_guess - markups

	return(loss, markups, shares, elas, elas_grad)

@njit 
def cost_from_prices(Zj, Pj, P, W):
	''' Obtain firm marginal cost from productivity, prices, and wage
	First relationship – Slide: 19, L1
	Second relationship – Slide 46, L1 + using relationship of industry markup to find expression for aggregate markup.
	'''
	Yj = (Pj/P)**(-theta) * Y 
	costj = Yj / Zj
	return(costj)

@njit
def price_aggregator(p, elas):
	''' Price index calculation
	Slide 19 lecture 1 

	p : is a n input vector of lower level prices
	elas : is the within aggregation unit elasticity of substitution
	'''
	P = (np.sum(p**(1-elas)))**(1/(1-elas))
	#P = (np.mean(p**(1-elas)))**(1/(1-elas)) # TODO: which one?
	return(P)
