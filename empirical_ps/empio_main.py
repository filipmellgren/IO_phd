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

# Store x time is a 'market'
# What about outside option here?
### TMP ############################################
df.loc[df.idcode == 35413, df.columns.isin(top_wines)]

#TMP end ############################################
# 0. Load data

df = pd.read_excel("data/wine_ps2.xls")
df = df.dropna()
df = df.set_index(["idcode", "storenum", "date"])


# 1. Descriptive statistics
# Number of products
plot_all(df)

# Based on plots, do some data filtration
df["price"] = df["p"] / df["fx"]
df["lnprice"] = np.log(df["price"])
df = df[df["lnprice"] < 6]

# 2. Estimate demand for wine
# Problem with this specification: prices are endogenous
# Additional issue: how seaprated are the markets? Some SUTVA might be violated
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



# TODO: maybe I should switch completely to the BLP package here. 

# 3. Berry 1994, Estimation. Estimate demand using discrtete choice a la Berry (1994) using observable product characteristics
Msize = df["numbot"].groupby(level = [0,1]).sum().groupby(level = [1]).max()*3 # Max bought over time, multiuplied by constant
df = df.join(Msize, rsuffix = "_market")
df["mshare"] = df["numbot"] / df["numbot_market"]
df["mshare_oo"] = 1 - df.mshare.groupby(level = [0,1]).agg("sum")
df["delta_j"] = np.log(df["mshare"]) - np.log(df["mshare_oo"])

def berry94_est(X, Y):
	''' Estimate alpha in Equation 14 in Berry 1994.
	Assumes there is a variable "lnprice" which is log(price).
	'''
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
	''' Back out marginal costs as in Eq 31 Berry 94
	'''
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