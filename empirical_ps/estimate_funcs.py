# TODO: how to add market size or outside good?


df["product_ids"] = df["idcode"]
df["prices"] = df["price"]
df["shares"] = df["mshare"]
df["market_ids"] = df.index.get_level_values('date').astype(str) +"_"+ df.index.get_level_values('storenum').astype(str)
df["demand_instruments0"] = df["price"]

# Specification 3 & 4, product characteristics
logit_formulation = pyblp.Formulation('prices + proof + variet')
problem = pyblp.Problem(logit_formulation, df)
logit_results_characteristics = problem.solve()


# Specification 5, fixed effects
logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids)')
problem = pyblp.Problem(logit_formulation, df)
logit_results_fe = problem.solve()

# Specification 6, BLP styled instruments
df["demand_instruments0"] = df["proof"].groupby(level = [0,1]).sum() - df["proof"]
df["demand_instruments1"] = df["merlot"].groupby(level = [0,1]).sum() - df["merlot"]
logit_formulation = pyblp.Formulation('prices')
problem = pyblp.Problem(logit_formulation, df)
logit_results_blp = problem.solve()

# Specification 7, countries as nests

df["nesting_ids"] = df["national"]
groups = df.groupby(["market_ids", "nesting_ids"])
df["demand_instruments20"] = groups["shares"].transform(np.size)
nl_formulation = pyblp.Formulation('0 + prices')
problem = pyblp.Problem(nl_formulation, df)
nl_results = problem.solve(rho = 0.7)

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