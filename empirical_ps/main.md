# Demand for Wine: Solutions to the Empirical Problem Set for Industrial Organization 2022
*Solutions by Filip Mellgren*, `filip.mellgren@su.se`

The problem set was solved using `python` and relies on the package `pyblp` by Christopher Conlon and Jeff Gortmaker.

## Descriptive Statistics

Since we want to estimate demand for wine, important variables in the dataset `wine_ps2.dta` include the price variabel `p`, which denotes the nominal price, and the quantity variable `numbot`. The unit of observation are `idcode`, which identifies a wine, `date`, which denotes a unit of time (presumably week), and `storenum`, which is a code identifying an individual store. `numbot` is consequenlty the number of bottles sold of a particular wine in a given store in a given point in time. In total, there are 31798 such observations, although I drop observations with NAs leaving me with 27189 observations. 

We begin by plotting the distribution of this price variable:

<img src="figures/price_hist.png" alt="price_dist" width="300"/>

Since we have data over time, we continue by looking at time trends for four, broad, price categories. Here, I define the categories by creating equally ranged bins. A wine connoisseur might disagree with the bins, but they work for our purpose nontheless:

<img src="figures/price_index.png" alt="price_trend" width="300"/>

We note that the price tends to be rather stable over the time horizon. However, it is interesting to note how *Value* wines increase in price while *Popular* drops towards the end of the sample frame. 

We proceed to look at the other key variable, `numbot`.

<img src="figures/bottles_by_prod.png" alt="numbot_distr" width="300"/>

This diagram shows us that wine sales follow something resembling a geometric distribution. That is, a few wines make up the bulk of sales and and most wines do not matter greatly for sales.

We also look at the distribution of sales over time. Here, we consider the distribution of total sales over `storenum`.
<img src="figures/bottles_time.png" alt="numbot_time" width="300"/>



Generate a variable `lnprice = log(p)`. 

## Demand estimation using naive regression



## Demand estimation using discrete choice 

There are several specifications for which we will repeat the exercise. 

TODO: nest based on red/white?





