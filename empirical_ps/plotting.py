# Plots for empirical problem set
import plotly.express as px
import plotly.io as pio
import pyblp
pio.templates.default = "plotly_white"
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def plot_all(df):
	# Price distribution
	df["price"] = df["p"]
	df["lnprice"] = df["p"]
	fig_lnp = px.histogram(df, x="lnprice").\
	update_layout(xaxis_title = "Log Price", yaxis_title = "Count")
	fig_p = px.histogram(df, x="price").\
	update_layout(xaxis_title = "Price", yaxis_title = "Count")
	fig_lnp.write_image("figures/log_price_hist.png")
	fig_p.write_image("figures/price_hist.png")

	# Price trend
	df["price_cat"] = pd.cut(df.price, bins = 4, labels = ["Value", "Popular", "Premium", "Super premium"])
	df["sales"] = df["price"] * df["numbot"]
	df_time_price = df.groupby(["date", "price_cat"]).sum()
	df_time_price["avg_price"] = df_time_price["sales"] / df_time_price["numbot"]

	first_date = np.min(df_time_price.reset_index()["date"])
	df_first_price = df_time_price[df_time_price.index.get_level_values(0) == first_date]["avg_price"].reset_index().set_index("price_cat")["avg_price"]
	df_time_price = df_time_price.join(df_first_price, rsuffix = "_first")
	df_time_price["avg_price_index"] = df_time_price["avg_price"]/df_time_price["avg_price_first"]
	df_time_price = df_time_price.reset_index()

	fig = px.line(df_time_price, x="date", y="avg_price_index", color='price_cat', markers = True).\
	update_layout(xaxis_title = "Date", yaxis_title = "Paasche price index", title = "Price evolution")
	fig.write_image("figures/price_index.png")

	# Quantities

	numbots_by_prod_tot = df[["prodname", "numbot"]].groupby(["prodname"]).sum().sort_values("numbot", ascending = False).reset_index()
	n_prods = numbots_by_prod_tot.shape[0]

	fig = px.bar(numbots_by_prod_tot, x = "prodname", y = "numbot", title = f"Long tail of wines with few sales, and a few super sellers <br><sup>Total number of products: {n_prods}</sup>").update_layout(xaxis_title = "Wine variety", yaxis_title = "Total number of bottles sold in data")
	fig.update_xaxes(visible=True, showticklabels=False)
	fig.write_image("figures/bottles_by_prod.png")

	# Volumes
	date_store = df.reset_index()[["numbot", "storenum", "date"]].\
	groupby(["date", "storenum"]).sum().reset_index()

	fig = px.box(date_store, x = "date", y = "numbot").\
	update_layout(xaxis_title = "Date", yaxis_title = "Bottles sold")
	
	fig.write_image("figures/bottles_time.png")
	
	return


	# TODO: look at red or white wines only