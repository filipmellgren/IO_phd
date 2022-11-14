# Empirical problem set Industrial Organizatino 2022. Filip Mellgren
# filip.mellgren@su.se
# TODO: read: https://pyblp.readthedocs.io/en/stable/
# See my old Berry 1994 estimation: https://github.com/filipmellgren/IO/blob/master/Workshop_3/Workshop_3.Rmd

import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import numpy as np
from plotting import plot_all
import ipdb
import plotly.express as px
from sklearn import datasets, linear_model
import pyblp
from estimate_funcs import est_demand_ols, calc_shares, set_names, est_prod_char, est_fe, est_blp_instrument, est_nests, extract_estimation_results
import plotly.graph_objects as go

# Store x time is a 'market'
# What about outside option here?
### TMP ############################################
#df.loc[df.idcode == 35413, df.columns.isin(top_wines)]

#TMP end ############################################
# 0. Load data

df = pd.read_excel("data/wine_ps2.xls")
df = df.dropna()
df = df.set_index(["idcode", "storenum", "date"])
MSIZE_k = 2
df["price"] = df["p"]
df["lnprice"] = np.log(df["price"])

total_sales = df.groupby(level = [1, 2]).sum()["numbot"]
df = df.join(total_sales, rsuffix = "_market")


# 1. Descriptive statistics

# SHould I do the below?
# TODO: correlation matrix with price
# TODO: correlation matrix with quantity

plot_all(df)

# 2. Estimate demand for wine
# Problem with this specification: prices are endogenous
# Additional issue: how seaprated are the markets? Some SUTVA might be violated
# #df = df.join(pd.get_dummies(df.sub_class))
top_N = 4
est_demand_ols(df, top_N)

# BLP estimation
k = MSIZE_k
df = calc_shares(df, MSIZE_k)
df = set_names(df)
# Swithching to BLP package here. 
# 3 and 4
results = est_prod_char(df)
me, agg, mc, mu = extract_estimation_results(df, results)
# 5
results_fe = est_fe(df)
me_fe, agg_fe, mc_fe, mu_fe = extract_estimation_results(df, results_fe)
# 6
results_blp = est_blp_instrument(df)
mu_blp, agg_blp, mc_blp, mu_blp = extract_estimation_results(df, results_blp)
# 7
results_nl = est_nests(df)
mu_nl, agg_nl, mc_nl, mu_nl = extract_estimation_results(df, results_nl)

# TODO: interpret markup. Is it p - mc or (p-mc)/p?
fig = go.Figure()
#fig.add_trace(go.Histogram(x=np.squeeze(mu, axis = 1),  name='Characteristics')) # Exclude, negative costs
fig.add_trace(go.Histogram(x=np.squeeze(mu_fe, axis = 1),  name='Fixed Effects'))
fig.add_trace(go.Histogram(x=np.squeeze(mu_blp, axis = 1), name='BLP IV'))
fig.add_trace(go.Histogram(x=np.squeeze(mu_nl, axis = 1), name='Country nest'))
# Overlay both histograms
fig.update_layout( title="Markup by Estimation Procedure", xaxis_title="Markup", yaxis_title = "Product ID", barmode='overlay')
# Reduce opacity to see both histograms
fig.update_traces(opacity=0.75)
fig.write_image("figures/markups.png")


'''

# 3. Berry 1994, Estimation. Estimate demand using discrtete choice a la Berry (1994) using observable product characteristics
Msize = df["numbot"].groupby(level = [0,1]).sum().groupby(level = [1]).max()*3 # Max bought over time, multiuplied by constant
df = df.join(Msize, rsuffix = "_market")
df["mshare"] = df["numbot"] / df["numbot_market"]
df["mshare_oo"] = 1 - df.mshare.groupby(level = [0,1]).agg("sum")
df["delta_j"] = np.log(df["mshare"]) - np.log(df["mshare_oo"])

def berry94_est(X, Y):
	 Estimate alpha in Equation 14 in Berry 1994.
	Assumes there is a variable "lnprice" which is log(price).
	
	price_var_loc = np.where(X.columns == "lnprice")[0][0]
	reg = LinearRegression().fit(X, Y) # Estimate beta and alpha through eq. 14 Berry 1994

	alpha = reg.coef_[price_var_loc]
	return(alpha, reg.coef_)

X_vars = ["lnprice", "proof", "variet", "doc"]
X = df.loc[:, df.columns.isin(X_vars)] 
Y = df.loc[:, "delta_j"]

b94_est, coefs = berry94_est(X, Y)
np.savetxt("figures/b94_elas.csv", np.expand_dims(b94_est,0))

# 4. Berry 1994, eq 31 (slighly before I think) Implied markups assuming MC are constant.
# https://pyblp.readthedocs.io/en/stable/_notebooks/tutorial/post_estimation.html
def berry94_markups(price, mshare, alpha):
	 Back out marginal costs as in Eq 31 Berry 94
	
	mc = price - 1/(alpha * (1 - mshare))
	markup = (price - mc)/price
	markup_quantiles = markup.quantile([.05, 0.25, 0.5, 0.75, 0.95])
	return(markup_quantiles)

markup_quantiles = berry94_markups(df["price"] , df["mshare"], b94_est)
np.savetxt("figures/b94_markup_pct.csv", markup_quantiles)

# 5. Estimate demand again, with product fixed effects instead of observables
# https://pyhdfe.readthedocs.io/en/stable/_notebooks/sklearn.html
# https://pyblp.readthedocs.io/en/stable/_notebooks/tutorial/logit_nested.html#Theory-of-Plain-Logit
df["product_ids"] = df["idcode"]
df["prices"] = df["price"]
df["shares"] = df["mshare"]
df["market_ids"] = df.index.get_level_values('date').astype(str) +"_"+ df.index.get_level_values('storenum').astype(str)
df["demand_instruments0"] = df["price"] # TODO: this subs in for an actual instrument and is needed. Is this the right way to do it?
logit_formulation = pyblp.Formulation('prices', absorb='C(product_ids)')
problem = pyblp.Problem(logit_formulation, df)
# T is the number of markets
# N is the length of the data set
# K1 is the dimension of the linear demand parameters
# ED is the numbe rof fixed effects dimenions, 1 is for one dim fixed effects
logit_results = problem.solve()

# 6. BLP: Same but with BLP-instruments for price
#Create a BLP instrument, a function of characteristics of other products' features
df["demand_instruments0"] = df["proof"].groupby(level = [0,1]).sum() - df["proof"]
df["demand_instruments1"] = df["merlot"].groupby(level = [0,1]).sum() - df["merlot"]
#df["demand_instruments2"] = df["doc"].groupby(level = [0,1]).sum() - df["doc"] # Colinear with current setup, add more products or just different products.
logit_formulation = pyblp.Formulation('prices')
problem = pyblp.Problem(logit_formulation, df)
logit_results = problem.solve()

# 7. Same but with nested logit specificataion
# https://pyblp.readthedocs.io/en/stable/_notebooks/tutorial/logit_nested.html#Theory-of-Nested-Logit