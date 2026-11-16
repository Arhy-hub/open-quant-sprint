import numpy as np

def variance_ratio(returns : np.ndarray, q: int) -> tuple[float,float]:
    clean_returns = returns[~np.isnan(returns)]

    mu = np.mean(clean_returns)
    var_1 = np.var(clean_returns)

    var_q = 0
    for k in (q,len(clean_returns)):
        var_q += (np.sum(clean_returns[k-q:k]) - q*mu)**2

    var_q *= 1/(len(clean_returns) * q)
    VR = var_q/var_1

    theta=0

    for j in range(1,q-1):
        delta = 0

        for i in range(j+1,len(clean_returns)):
            delta += (clean_returns[i]-mu)**2 * (returns[i-j]-mu)**2

        delta = delta/var_1**2
        theta+= 2*(q-j)/q**2 * delta

    z_star = np.sqrt(len(clean_returns)) * (VR-1) / np.sqrt(theta)
    return VR,z_star

