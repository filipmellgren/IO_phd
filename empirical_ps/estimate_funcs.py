import pandas as pd
import numpy as np
import pyblp
import plotly.express as px
from sklearn.linear_model import LinearRegression
import ipdb


def est_demand_ols(df):
	# Based on plots, do some data filtration
	
	top_N = 4
	top_wines = df.groupby(level = 0).sum()["numbot"].sort_values(ascending = False).reset_index()[:top_N].idcode
	df = df.reset_index()
	df = df.loc[pd.Series(df.idcode).isin(top_wines)]

	df_prices = df.pivot(index=["date", "storenum"], columns = "idcode", values='lnprice')

	df = df.set_index(["date", "storenum"])
	df = df.join(df_prices)
	df = df.dropna()
	df["lnq"] = np.log(df["numbot"])

	df["lnq"].describe()
	df["lnprice"].describe()

	df["Wine_id"] = df["idcode"].astype(str)
	fig = px.scatter(df, x = "lnq", y = "lnprice", color = "Wine_id", trendline = "ols")
	fig.show()
	fig.write_image("figures/price_quant.png")

	els = []
	for wine in top_wines:
		X = df.loc[df.idcode == wine, df.columns.isin(top_wines)]
		Y = df.loc[df.idcode == wine, "lnq"]
		reg = LinearRegression().fit(X, Y)
		els.append(reg.coef_)

	els = pd.DataFrame(els)
	els.index = top_wines
	els.index = els.index.map(str)
	els.columns = top_wines
	els.columns = els.columns.map(str)

	fig = px.imshow(els, title = "Elasticity estimates under OLS controlling for price") 
	fig.write_image("figures/elasticities_ols.png")
	return


# TODO: Do this before cutting away values
def calc_shares(df, k):
	'''
	k is the constant used to define the market size
	'''
	Msize = df["numbot"].groupby(level = [0,1]).sum().groupby(level = [1]).max() * k # Max bought over time, multiuplied by constant
	df = df.join(Msize, rsuffix = "_market")
	df["shares"] = df["numbot"] / df["numbot_market"]
	return(df)

def set_names(df):
	
	df["product_ids"] = df.index.get_level_values('idcode')
	df["prices"] = df["price"]
	df["market_ids"] = df.index.get_level_values('date').astype(str) +"_"+ df.index.get_level_values('storenum').astype(str)
	df["demand_instruments0"] = df["price"]
	return(df)

def est_prod_char(df):
	# Specification 3 & 4, product characteristics
	logit_formulation = pyblp.Formulation('prices + proof + variet')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_characteristics = problem.solve()
	return()

def est_fe(df):
	# Specification 5, fixed effects
	logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids)')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_fe = problem.solve()
	return

def est_blp_instrument():
	# Specification 6, BLP styled instruments
	df["demand_instruments0"] = df["proof"].groupby(level = [0,1]).sum() - df["proof"]
	df["demand_instruments1"] = df["merlot"].groupby(level = [0,1]).sum() - df["merlot"]
	logit_formulation = pyblp.Formulation('prices')
	problem = pyblp.Problem(logit_formulation, df)
	logit_results_blp = problem.solve()
	return

def est_nests(df):
	# Specification 7, countries as nests
	df["nesting_ids"] = df["national"]
	groups = df.groupby(["market_ids", "nesting_ids"])
	df["demand_instruments20"] = groups["shares"].transform(np.size)
	nl_formulation = pyblp.Formulation('0 + prices')
	problem = pyblp.Problem(nl_formulation, df)
	nl_results = problem.solve(rho = 0.7)
	return

def extract_estimation_results(results, path):
	''' Calculate elasticities, markups, marginal costs, and create plots
	results : a ProblemResults object from pyblp package
	'''
	elasticities = results.compute_elasticities()
	mean_elasticities = results.extract_diagonal_means(elasticities)
	aggregates = results.compute_aggregate_elasticities(factor=0.1)
	costs = results.compute_costs() # Note: Either firm IDs or an ownership matrix must have been specified.
	markups = results.compute_markups(costs=costs)
	return