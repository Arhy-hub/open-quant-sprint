import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#from src.contrib.arhaan import variance_ratio

def variance_ratio(returns: np.ndarray, q: int) -> tuple[float, float]:
    """Lo-MacKinlay (1988) variance ratio with bias-corrected estimators and
    the heteroskedasticity-robust z* statistic.

    returns: 1-period log returns. q: aggregation horizon (q >= 2).
    Returns (VR(q), z*(q)).
    """
    r = returns[~np.isnan(returns)]

    if q < 2:
        raise ValueError("q must be >= 2")

  
    nq = len(r)
    if nq <= q:
        raise ValueError("need more than q returns")

    mu = r.mean()

    # 1-period variance, unbiased: divide by nq - 1
    var_1 = np.sum((r - mu) ** 2) / (nq - 1)

    # overlapping q-period sums X_k - X_{k-q}, for every window (nq - q + 1 of them)
    csum = np.concatenate(([0.0], np.cumsum(r)))
    q_sums = csum[q:] - csum[:-q]

    # q-period variance (per period), bias-corrected: divide by m
    m = q * (nq - q + 1) * (1 - q / nq)
    var_q = np.sum((q_sums - q * mu) ** 2) / m

    VR = var_q / var_1

    # heteroskedasticity-robust asymptotic variance theta(q)
    dev2 = (r - mu) ** 2
    denom = np.sum(dev2) ** 2
    theta = 0.0
    for j in range(1, q):  # j = 1 .. q-1
        delta_j = nq * np.sum(dev2[j:] * dev2[:-j]) / denom
        theta += (2 * (q - j) / q) ** 2 * delta_j

    z_star = np.sqrt(nq) * (VR - 1) / np.sqrt(theta)
    return float(VR), float(z_star)



data = pd.read_parquet("data/train_1h.parquet")

q_timeframes = [2,4,8,24,72,168] # computing over 2hr,4hr,...,1day,...,1week timeframe on 1hr data
symbol_data = {}
symbols = data["symbol"].unique()
index_prices = 0

for symbol in symbols:
    prices = np.array(data[data["symbol"] == symbol]["close"])
    log_prices = np.log(prices)
    returns = log_prices[1:] - log_prices[:-1]

    index_prices += 1/len(symbols) * prices

    symbol_data[symbol] = {}
    symbol_data[symbol]["prices"] = prices
    symbol_data[symbol]["returns"] = returns
    symbol_data[symbol]["VR"] = []
    symbol_data[symbol]["z*"] = []


symbol_data["index"] = {}
symbol_data["index"]["prices"] = index_prices
symbol_data["index"]["returns"] = np.log(index_prices[1:])-np.log(index_prices[:-1]) 
symbol_data["index"]["VR"] = []
symbol_data["index"]["z*"] = []

for q in q_timeframes:
    for symbol in symbol_data.keys():
        returns = symbol_data[symbol]["returns"]
        VR,z_star= variance_ratio(returns,q)
        symbol_data[symbol]["VR"].append(VR)
        symbol_data[symbol]["z*"].append(z_star)
        




for symbol in symbol_data.keys():
    plt.plot(q_timeframes,symbol_data[symbol]["VR"],label=symbol)


plt.legend() 
plt.show()