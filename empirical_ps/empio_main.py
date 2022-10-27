# Empirical problem set Industrial Organizatino 2022. Filip Mellgren
# filip.mellgren@su.se


# TODO: read: https://pyblp.readthedocs.io/en/stable/
# See my old Berry 1994 estimation: https://github.com/filipmellgren/IO/blob/master/Workshop_3/Workshop_3.Rmd

import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.io as pio
import pyblp
pio.templates.default = "plotly_white"

# Store x time is a 'market'
# What about outside option here?

# 0. Load data

df = pd.read_excel("data/wine_ps2.xls")
df = df.dropna()

# 1. Descriptive statistics

df.describe()

dagg = df.groupby(["date", "storenum"]).sum().reset_index()
fig = px.line(dagg, x='date', y="numbot", color = "storenum")
fig.show()



# 2. Estimate demand for wine
# Problem with this specification: prices are endogenous
# Additional issue: how seaprated are the markets? Some SUTVA might be violated
top_N = 5
top_wines = df.groupby("winespec").sum()["numbot"].sort_values(ascending = False).reset_index()[:top_N].winespec
df = df.loc[pd.Series(df.winespec).isin(top_wines)]


X = df[["p", "pinot"]] # TODO: add price of competing products (price other wines same store same week?)
Y = df["numbot"]
reg = LinearRegression().fit(X, Y)

# 3. Berry 1994, Estimation. Estimate demand using discrtete choice a la Berry (1994) using observable product characteristics

# 4. Berry 1994, Markups. Implied markups assuming MC are constant.
# https://pyblp.readthedocs.io/en/stable/_notebooks/tutorial/post_estimation.html

# 5. Estimate demand again, with product fixed effects instead of observables

# 6. BLP: Sam but with BLP-instruments for price
# Note: key differences relativey to Beryy 1994 is "Random coefficients model" of consumer utility?


# 7. Same but with nested logit specificataion
