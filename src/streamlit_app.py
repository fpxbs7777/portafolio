import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy import stats

def calculate_portfolio_metrics(weights, returns, cov_matrix):
    """
    Calculate key portfolio metrics given weights and return/covariance data
    """
    portfolio_return = np.sum(returns.mean() * weights) * 252  # Annualized
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
    sharpe_ratio = portfolio_return / portfolio_std if portfolio_std > 0 else 0
    
    return {
        'return': portfolio_return,
        'risk': portfolio_std,
        'sharpe': sharpe_ratio
    }

def optimize_portfolio(returns, asset_types, target_return=None, risk_free_rate=0.02):
    """
    Optimize portfolio weights using Modern Portfolio Theory with asset type constraints
    """
    n_assets = returns.shape[1]
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    # Initial guess: equal weights
    initial_weights = np.array([1/n_assets] * n_assets)
    
    # Asset type constraints
    asset_type_bounds = {
        'ACCIONES': (0, 1),
        'BONOS': (0, 0.6),  # Máximo 60% en bonos
        'FCI': (0, 0.4),    # Máximo 40% en FCIs
        'OPCIONES': (0, 0.1) # Máximo 10% en opciones
    }
    
    # Create bounds based on asset types
    bounds = []
    for asset_type in asset_types:
        bound = asset_type_bounds.get(asset_type, (0, 1))
        bounds.append(bound)
    
    bounds = tuple(bounds)
    
    # Basic constraints
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
    ]
    
    # Add asset type constraints
    for asset_type in set(asset_types):
        indices = [i for i, t in enumerate(asset_types) if t == asset_type]
        max_weight = asset_type_bounds.get(asset_type, (0, 1))[1]
        if indices:
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, idx=indices, max_w=max_weight: max_w - np.sum(x[idx])
            })
    
    if target_return is not None:
        constraints.append({
            'type': 'eq',
            'fun': lambda x: np.sum(mean_returns * x) - target_return/252
        })
    
    # Modified objective function
    def objective(weights):
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        if target_return is None:
            portfolio_ret = np.sum(mean_returns * weights)
            sharpe = (portfolio_ret - risk_free_rate/252) / portfolio_std
            return -sharpe
        return portfolio_std
    
    try:
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return result.x if result.success else initial_weights
    except Exception:
        return initial_weights

def calculate_asset_specific_metrics(returns, asset_type):
    """
    Calculate metrics specific to each asset type
    """
    metrics = {
        'mean': returns.mean(),
        'std': returns.std(),
        'skew': stats.skew(returns),
        'kurtosis': stats.kurtosis(returns),
    }
    
    if asset_type == 'BONOS':
        # Métricas específicas para bonos
        metrics.update({
            'duration': calculate_duration(returns),
            'yield': calculate_yield(returns)
        })
    elif asset_type == 'OPCIONES':
        # Métricas específicas para opciones
        metrics.update({
            'implied_vol': calculate_implied_vol(returns),
            'theta': calculate_theta(returns)
        })
    elif asset_type == 'FCI':
        # Métricas específicas para FCIs
        metrics.update({
            'tracking_error': calculate_tracking_error(returns),
            'information_ratio': calculate_information_ratio(returns)
        })
    
    return metrics

# Funciones auxiliares para métricas específicas
def calculate_duration(returns):
    return np.mean(returns) * 252

def calculate_yield(returns):
    return np.sum(returns)

def calculate_implied_vol(returns):
    return np.std(returns) * np.sqrt(252)

def calculate_theta(returns):
    return -np.mean(returns) * 252

def calculate_tracking_error(returns):
    return np.std(returns) * np.sqrt(252)

def calculate_information_ratio(returns):
    return np.mean(returns) / (np.std(returns) + 1e-6)
