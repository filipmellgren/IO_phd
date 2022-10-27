import plotly.express as px
import numpy as np
import pandas as pd
import ipdb
from scipy import interpolate

# Plot reaction function

def rf_bertrand(alpha, beta, c, gamma, p1):
	p2 = (alpha/beta + c*(1+gamma/2) - 2 * p1*(1+gamma/2)) * (-2 / gamma)
	return(p2)

def demand(alpha, beta, c, gamma, p1, p2):
	q1 = 1/2 * (alpha - beta * (1+gamma/2) * p1 + p2 * beta * gamma / 2)
	return(q1)

def inv_demand(alpha, beta, c, gamma, q1, q2):
	p1 = alpha / beta - 1 / beta * (2+gamma) / (1+gamma) * (q1 + q2 * gamma / (2 + gamma) )
	return(p1)

def rf_cournot(alpha, beta, c, gamma, q1):
	q2 = alpha/2 * (1+gamma) / (2+gamma) - 1/2 * (gamma)/(2+gamma) * q1 - beta * c/2 *(1+gamma) / (2+gamma)
	return(q2)

gamma = 1

# Bertrand
def solve_bertrand(gamma, save_output):
	alpha = 0.25
	beta = 0.5
	c = 0.1

	p1 = np.linspace(
		start = 0, 
		stop = 1,
		num = 1000).T

	p2 = rf_bertrand(alpha, beta, c, gamma, p1)

	df = pd.DataFrame({'Firm 1 price':p1, 'Firm 2 price':p2})
	
	pstar_ix = np.argmin(np.abs(df["Firm 1 price"] - df["Firm 2 price"]))

	p_star = df["Firm 1 price"][pstar_ix]

	q_bertrand = demand(alpha, beta, c, gamma, p_star, p_star)

	profit_bertrand = (p_star-c) * q_bertrand

	bertrand = np.array((p_star, q_bertrand, profit_bertrand, c), dtype = [("p", "float64"), ("q", "float64"), ("profit", "float64"), ("cost", "float64")])

	bertrand = np.expand_dims(bertrand, axis = 0)
	if save_output:
		fig = px.line(df, x='Firm 1 price', y='Firm 2 price', title = f'Reaction function, gamma = {gamma}') 
		fig.add_scatter(x=df['Firm 2 price'], y=df['Firm 1 price'], name = 'Firm 2 price',mode='lines')
		fig.add_scatter(x=df['Firm 1 price'], y=df['Firm 2 price'], name = 'Firm 1 price',mode='lines')
		fig.write_image(f'figures/bertrand_gamma_{gamma}.png')
		np.savetxt(f'figures/bertrand_gamma_{gamma}.csv', bertrand, delimiter=',')

	return(gamma, bertrand)

def solve_cournot(gamma, save_output):
	# Cournot
	alpha = 0.25
	beta = 0.5
	c = 0.1
	q1 = np.linspace(
		start = 0, 
		stop = 1,
		num = 1000).T

	q2 = rf_cournot(alpha, beta, c, gamma, q1)

	df = pd.DataFrame({'Firm 1 quantity':q1, 'Firm 2 quantity':q2})


	qstar_ix = np.argmin(np.abs(df["Firm 1 quantity"] - df["Firm 2 quantity"]))
	q_star = df["Firm 1 quantity"][qstar_ix]

	p_cournot = inv_demand(alpha, beta, c, gamma, q_star, q_star)

	profit_cournot = (p_cournot - c) * q_star
	cournot = np.array((q_star, p_cournot, profit_cournot, c), dtype = [("p", "double"), ("q", "double"), ("profit", "double"), ("cost", "double")])
	cournot = np.expand_dims(cournot, axis = 0)
	
	if save_output:
		fig = px.line(df, x='Firm 1 quantity', y='Firm 2 quantity', title = f'Reaction function, gamma = {gamma}') 
		fig.add_scatter(x=df['Firm 2 quantity'], y=df['Firm 1 quantity'], name = 'Firm 2 quantity',mode='lines')
		fig.add_scatter(x=df['Firm 1 quantity'], y=df['Firm 2 quantity'], name = 'Firm 1 quantity',mode='lines')
		np.savetxt(f'figures/cournot_gamma_{gamma}.csv', cournot, delimiter=',')
		fig.write_image(f'figures/cournot_gamma_{gamma}.png')
	return(gamma, cournot)

solve_bertrand(gamma, True)
solve_cournot(gamma, True)

gamma = 1.5

solve_bertrand(gamma, True)
solve_cournot(gamma, True)

# Optional and extra
bertrand = np.empty((1000, 2), dtype = "float64")
for g in range(1000):
	gamma = (g+1)/1000
	gamma, bert_outcome = solve_bertrand(gamma, False)
	bertrand[g, 0] = gamma
	bertrand[g, 1] = bert_outcome["profit"]
df = pd.DataFrame(bertrand, columns = ["gamma", "profit"])
fig = px.line(df, x='gamma', y='profit', title = "Bertrand profit varies with gamma") 
fig.write_image(f'figures/bertrand_gamma_profits.png')

# Cournot
cournot = np.empty((1000, 2), dtype = "float64")
for g in range(1000):
	gamma = (g+1)/1000
	gamma, cort_outcome = solve_cournot(gamma, False)
	cournot[g, 0] = gamma
	cournot[g, 1] = cort_outcome["profit"]
df = pd.DataFrame(cournot, columns = ["gamma", "profit"])
fig = px.line(df, x='gamma', y='profit', title = "Cournot profit varies with gamma") 
fig.write_image(f'figures/cournot_gamma_profits.png')



