import numpy as np

def variance_ratio(returns : np.ndarray, q: int) -> tuple[float,float]:
    clean_returns = returns[~np.isnan(returns)]

    mean_returns = np.mean(clean_returns)
    var_1 = np.var(clean_returns)

    var_q = 0
    for k in (q,len(returns)):
        var_q += (np.sum(clean_returns[k-q:k]) - q*mean_returns)**2

    VR = var_q/var_1
    return VR,0

