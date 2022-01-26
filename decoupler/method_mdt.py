"""
Method MDT.
Code to run the Multivariate Decision Tree (MDT) method. 
"""

import numpy as np
import pandas as pd

from .pre import extract, match, rename_net, get_net_mat, filt_min_n

from anndata import AnnData
from skranger.ensemble import RangerForestRegressor
from tqdm import tqdm


def fit_rf(net, sample, trees=100, min_leaf=5, n_jobs=4, seed=42):
    regr = RangerForestRegressor(n_estimators=trees, min_node_size=min_leaf, 
                                 n_jobs=n_jobs, seed=seed, importance='impurity')
    regr.fit(net, sample)
    return regr.feature_importances_
        

def mdt(mat, net, trees=10, min_leaf=5, n_jobs=4, seed=42, verbose=False):
    """
    Multivariate Decision Tree (MDT).
    
    Computes MDT to infer regulator activities.
    
    Parameters
    ----------
    mat : np.array
        Input matrix with molecular readouts.
    net : np.array
        Regulatory adjacency matrix.
    trees : int
        Number of trees in the forest.
    min_leaf : int
        The minimum number of samples required to be at a leaf node.
    n_jobs : int
        Number of jobs to run in parallel
    seed : int
        Random seed to use.
    verbose : bool
        Whether to show progress.
    
    Returns
    -------
    acts : Array of activities.
    """
    
    acts = np.zeros((mat.shape[0], net.shape[1]))
    for i in tqdm(range(mat.shape[0]), disable=not verbose):
        acts[i] = fit_rf(net, mat[i], trees=trees, min_leaf=min_leaf, n_jobs=n_jobs, seed=seed)
    
    return acts


def run_mdt(mat, net, source='source', target='target', weight='weight', trees=100, 
            min_leaf=5, n_jobs=4, min_n=5, seed=42, verbose=False, use_raw=True):
    """
    Multivariate Decision Tree (MDT).
    
    Wrapper to run MDT.
    
    Parameters
    ----------
    mat : list, pd.DataFrame or AnnData
        List of [features, matrix], dataframe (samples x features) or an AnnData
        instance.
    net : pd.DataFrame
        Network in long format.
    source : str
        Column name in net with source nodes.
    target : str
        Column name in net with target nodes.
    weight : str
        Column name in net with weights.
    trees : int
        Number of trees in the forest.
    min_leaf : int
        The minimum number of samples required to be at a leaf node.
    n_jobs : int
        Number of jobs to run in parallel
    min_n : int
        Minimum of targets per source. If less, sources are removed.
    seed : int
        Random seed to use.
    verbose : bool
        Whether to show progress.
    use_raw : bool
        Use raw attribute of mat if present.
    
    Returns
    -------
    Returns mdt activity estimates or stores them in 
    `mat.obsm['mdt_estimate']`.
    """
    
    # Extract sparse matrix and array of genes
    m, r, c = extract(mat, use_raw=use_raw)
    
    # Transform net
    net = rename_net(net, source=source, target=target, weight=weight)
    net = filt_min_n(c, net, min_n=min_n)
    sources, targets, net = get_net_mat(net)
    
    # Match arrays
    net = match(c, targets, net)
    
    if verbose:
        print('Running mdt on {0} samples and {1} sources.'.format(m.shape[0], net.shape[1]))
    
    # Run MDT
    estimate = mdt(m.A, net, trees=trees, min_leaf=min_leaf, 
                   n_jobs=n_jobs, seed=seed, verbose=verbose)
    
    # Transform to df
    estimate = pd.DataFrame(estimate, index=r, columns=sources)
    estimate.name = 'mdt_estimate'
    
    # AnnData support
    if isinstance(mat, AnnData):
        # Update obsm AnnData object
        mat.obsm[estimate.name] = estimate
    else:
        return estimate