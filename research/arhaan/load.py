import numpy as np
import pandas as pd

INDEX_NAME = "EW_index"


def load_returns(path: str = "data/train_1h.parquet") -> pd.DataFrame:
    """Hourly close-to-close log returns, one column per symbol plus the
    equal-weighted index.

    Returns a DataFrame indexed by timestamp (hours), columns = the symbols
    followed by EW_index. The first hour is dropped (its return is NaN).
    Raises if the hourly grid has gaps, so nothing is filled silently.
    """
    data = pd.read_parquet(path, columns=["timestamp", "symbol", "close"])
    return returns_from_bars(data)


def returns_from_bars(data: pd.DataFrame) -> pd.DataFrame:
    # timestamp x symbol table of closes, rows in time order
    closes = data.pivot(index="timestamp", columns="symbol", values="close").sort_index()

    # the grid must be complete: every symbol has a bar every hour
    if closes.isna().any().any():
        missing = closes.isna().sum()
        raise ValueError(f"missing closes:\n{missing[missing > 0]}")
    
    steps = closes.index.to_series().diff().dropna()

    if not (steps == pd.Timedelta(hours=1)).all():
        raise ValueError("timestamps are not consecutive hours")

    # ln(close_t / close_{t-1}) per symbol; first row is NaN, drop it
    returns = np.log(closes).diff().iloc[1:]

    # equal-weighted index: mean of the symbols' hourly log returns (as in #17)
    returns[INDEX_NAME] = returns.mean(axis=1)
    return returns
