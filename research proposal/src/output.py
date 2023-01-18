
def plot_weighted_values(df, outcome_var, path):
	# TODO: color by max prodcutivty
	fig = px.scatter(x = df.index, y = df[outcome_var],
		labels=dict(x="Largest firm percentile", y = outcome_var), title = "Weights by industry cost")
	fig.write_image(path + "_" + outcome_var + ".png")
	return


def aggregate_output(shares, hhis, markups, prices_j, Z_js, path):
	df = pd.DataFrame(list(zip(shares, hhis, markups, prices_j, Z_js)), columns =['shares', 'hhis', 'markups', 'Ptildej', 'Zj'])
	df["cost"] = costj
	df["Pj"] = df["Ptildej"] * W # Slide 42, L1.
	df["pct"] = df.shares.rank(pct = True) * 100
	df["pct"] = df["pct"].apply(lambda x: int(x))
	df["j"] = df.index

	weights = df[["cost", "pct", "j"]].copy().set_index(["pct", "j"])
	group_weight = weights.groupby(level = 0).sum()
	weights = weights.join(group_weight, rsuffix = "_group")
	weights = weights.div(weights["cost_group"], axis = 0).drop(["cost_group"], axis = 1).rename(columns = {"cost" : "weight"})

	df = df.set_index(["pct", "j"])
	df = df.join(weights)
	# Multiply columns by cost variable used to weigh observations
	df = df.mul(df["weight"], axis=0)
	df = df.groupby(level = 0).sum()
	
	plot_weighted_values(df, "shares", path)
	plot_weighted_values(df, "hhis", path)
	plot_weighted_values(df, "markups", path)
	plot_weighted_values(df, "Pj", path)
	return