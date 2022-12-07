import plotly.express as px
import numpy as np
import pandas as pd
import ipdb
from scipy import interpolate
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_white"

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

def solve_bertrand(gamma):
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


	return(df, gamma, bertrand)

def solve_cournot(gamma):
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
	

	return(df, gamma, cournot)

# BERTRAND
df1, gamma1, b1 = solve_bertrand(gamma = 1)

df2, gamma2, b2 = solve_bertrand(gamma = 1.5)

def plot_rfs(df1, df2, firm1, firm2):
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=df1[firm1], y=df1[firm2],
		name='Firm 1, gamma = 1', line = dict(color='royalblue', width=2)))
	fig.add_trace(go.Scatter(x=df1[firm2], y=df1[firm1],
		name='Firm 2, gamma = 1', line = dict(color='firebrick', width=2)))

	fig.add_trace(go.Scatter(x=df2[firm1], y=df2[firm2], 
		name='Firm 1, gamma = 1.5', line = dict(color='royalblue', width=2, dash='dash')))
	fig.add_trace(go.Scatter(x=df2[firm2], y=df2[firm1], 
		name='Firm 2, gamma = 1.5', line = dict(color='firebrick', width=2, dash='dash')))
	fig.update_layout(xaxis_range=[0,0.6])
	fig.update_layout(yaxis_range=[0,0.6])
	fig.update_layout(xaxis_title=firm1, yaxis_title=firm2)
	
	return(fig)

fig = plot_rfs(df1, df2, 'Firm 1 price', 'Firm 2 price')
fig.update_layout(title='Bertrand reaction functions')
fig.write_image(f'figures/bertrand_gamma.png')

pd.DataFrame(b1).to_markdown()
pd.DataFrame(b2).to_markdown()

# COURNOT


dfc1, gamma1, c1 = solve_cournot(gamma = 1)
dfc2, gamma2, c2 = solve_cournot(gamma = 1.5)

fig = plot_rfs(dfc1, dfc2, 'Firm 1 quantity', 'Firm 2 quantity')
fig.update_layout(title='Cournot reaction functions')
fig.write_image(f'figures/cournot_gamma.png')

pd.DataFrame(c1).to_markdown()
pd.DataFrame(c2).to_markdown()




fig = px.line(df, x='Firm 1 quantity', y='Firm 2 quantity', title = f'Reaction function, gamma = {gamma}') 
fig.add_scatter(x=df['Firm 2 quantity'], y=df['Firm 1 quantity'], name = 'Firm 2 quantity',mode='lines')
fig.add_scatter(x=df['Firm 1 quantity'], y=df['Firm 2 quantity'], name = 'Firm 1 quantity',mode='lines')
np.savetxt(f'figures/cournot_gamma_{gamma}.csv', cournot, delimiter=',')
fig.write_image(f'figures/cournot_gamma_{gamma}.png')


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

# Part 2 #####################################
def indif_consumer(s1, s2, p1, p2, t, a, b):
	xstar = (s1-s2 - (p1 - p2))/(2 * t *(1-b-a)) + (1-b+a)/2
	return(xstar)

def find_prices(t, a, b, s1, s2):
	m = (1 - b + a)/2
	p2 = ((4 - 2 * m) * t * (1-b-a) - s1 + s2)/3
	p1 = 2 * t * (1-b - a) - p2
	return(p1, p2)

def find_quantities(s1, s2, p1, p2, t, a, b):
	q1 = indif_consumer(s1, s2, p1, p2, t, a, b)
	q2 = 1 - indif_consumer(s1, s2, p1, p2, t, a, b)
	return(q1, q2)

# b
t = 1
a = 0.2
b = 0.2
s1 = 0
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2
# c
t = 1
a = 0.4
b = 0.1
s1 = 0
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2

#c2
t = 1
a = 0
b = 0
s1 = 0
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2

#d
t = 1/2
a = 0.4
b = 0.1
s1 = 0
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2

# d2
t = 1/2
a = 0
b = 0
s1 = 0
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2

# e
t = 1
a = 0.4
b = 0.1
s1 = 1
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2

# e2
t = 1
a = 0
b = 0
s1 = 1
s2 = 0

p1, p2 = find_prices(t, a, b, s1, s2)
q1, q2 = find_quantities(s1, s2, p1, p2, t, a, b)
Profit1, Profit2 = p1*q1, p2*q2




