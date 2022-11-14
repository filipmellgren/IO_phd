import pandas as pd
import numpy as np
import pyblp
import plotly.express as px
from sklearn.linear_model import LinearRegression
import ipdb
import plotly.graph_objects as go



def est_demand_ols(df, top_N):
	''' Estimate elasticities using linear regression.

	'''	
	
	top_wines = df.groupby(level = 2).sum()["numbot"].sort_values(ascending = False).reset_index()[:top_N].idcode
	df = df.reset_index()
	df = df.loc[pd.Series(df.idcode).isin(top_wines)]

	df_prices = df.pivot(index=["date", "storenum"], columns = "idcode", values='lnprice')

	df = df.set_index(["date", "storenum"])
	df = df.join(df_prices)
	df = df.dropna()
	df["lnq"] = np.log(df["numbot"])

	df["Wine_id"] = df["idcode"].astype(str)

	fig = px.scatter(df, x = "lnq", y = "lnprice", color = "Wine_id", trendline = "ols")
	
	fig.write_image("figures/price_quant.png")

	els = []
	top_wines = np.sort(top_wines)
	for wine in top_wines:
		X = df.loc[df.idcode == wine, df.columns.isin(top_wines) | df.columns.isin(["numbot_market", "doc", "proof"])] 
		Y = df.loc[df.idcode == wine, "lnq"]
		reg = LinearRegression().fit(X, Y)
		els.append(reg.coef_)


	els = pd.DataFrame(els)

	els = els.loc[:, X.columns.isin(top_wines)]
	els.index = top_wines
	els.index = els.index.map(str)
	els.columns = top_wines
	els.columns = els.columns.map(str)
	
	fig = px.imshow(els, title = "Elasticity estimates under OLS controlling for price") 
	fig.write_image("figures/elasticities_ols.png")
	return

def calc_shares(df, k):
	'''
	k is the constant used to define the market size
	'''

	Msize = df["numbot"].groupby(level = [0, 1]).sum().groupby(level = [1]).max() * k # Max bought over time, multiuplied by constant
	df = df.join(Msize, rsuffix = "_max_market")
	df["shares"] = df.numbot / df.numbot_max_market

	return(df)

def set_names(df):
	
	df["product_ids"] = df.index.get_level_values('idcode')
	df["prices"] = df["price"]
	df["market_ids"] = df.index.get_level_values('date').astype(str) +"_"+ df.index.get_level_values('storenum').astype(str)
	df["demand_instruments0"] = df["price"]
	df['firm_ids'] = df['product_ids'] # Each product is associated with 1 prodct
	return(df)

def est_prod_char(df):
	# Specification 3 & 4, product characteristics
	#pd.get_dummies(df["sub_class"]).columns
	logit_formulation = pyblp.Formulation('prices + proof + variet + doc')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_characteristics = problem.solve()
	return(logit_results_characteristics)

def est_fe(df):
	# Specification 5, fixed effects
	logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids)')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_fe = problem.solve()
	return(logit_results_fe)

def est_blp_instrument(df):
	# Specification 6, BLP styled instruments
	
	df["demand_instruments0"] = df["fx"] # Cost shifter
	df["demand_instruments1"] = df["doc"].groupby(level = [0,1]).sum() - df["doc"] # BLP instrument
	df["demand_instruments2"] = df.groupby(level = [0,1]).size() # BLP instrument, number of other products in store
	logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids)')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_blp = problem.solve()
	return(logit_results_blp)

def est_nests(df):
	# Specification 7, countries as nests
	df["nesting_ids"] = df["national"]
	groups = df.groupby(["market_ids", "nesting_ids"])
	df["demand_instruments20"] = groups["shares"].transform(np.size)
	nl_formulation = pyblp.Formulation('0 + prices')
	problem = pyblp.Problem(nl_formulation, df)
	nl_results = problem.solve(rho = 0.7)
	return(nl_results)

def extract_estimation_results(df, results):
	''' Calculate elasticities, markups, marginal costs, and create plots
	results : a ProblemResults object from pyblp package
	# TODO: extract coefficients for each run
	# TODO: WANT TO HAVE all outcome in a single plot. Would be neat
	# Histogram with markups for each specification. 
	# TODO: he asks specifically for quantiles: What is the implied markup - at the 5th percentile, 25th, median, 75th and 95th?
	'''
	elasticities = results.compute_elasticities()
	# Information about own elasticities of demand from elasticity matrices:
	mean_elasticities = results.extract_diagonal_means(elasticities)
	# Aggregate elasticities of demand, E, in each market, which reflect the change in total sales under a proportional sales tax of some factor
	aggregates = results.compute_aggregate_elasticities(factor=0.1)
	costs = results.compute_costs() 
	markups = results.compute_markups(costs=costs)
	return(mean_elasticities, aggregates, costs, markups)

def plot_aggs_means(aggs, means):
	fig = go.Figure()
	fig.add_trace(go.Histogram(x=np.squeeze(means, axis = 1)))
	fig.add_trace(go.Histogram(x=np.squeeze(aggregates, axis = 1)))
	# Overlay both histograms
	fig.update_layout(barmode='overlay')
	# Reduce opacity to see both histograms
	fig.update_traces(opacity=0.75)
	fig.write_image("figures/mean_agg_elasticities.png")
	return

def histogram(df, variable, path):
	fig = go.Figure()
	fig.add_trace(go.Histogram(x=np.squeeze(variable, axis = 1)))
	fig.write_image(path)
	return






