import os
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import gym
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
import torch.nn as nn
import torch.optim as optim
from gym import spaces
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback, CallbackList
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='gym')
warnings.filterwarnings('ignore', category=UserWarning, module='stable_baselines3')

class PortfolioEnv(gym.Env):
    """Custom Environment for portfolio optimization using reinforcement learning"""
    metadata = {'render.modes': ['human']}
    
    def __init__(self, df: pd.DataFrame, initial_balance: float = 100000, 
                 window_size: int = 30, commission: float = 0.001):
        """
        Initialize the environment with historical data
        
        Args:
            df: DataFrame with historical price data (columns: assets, index: dates)
            initial_balance: Initial portfolio balance in ARS
            window_size: Number of days to look back for state representation
            commission: Trading commission as a fraction of trade value
        """
        super(PortfolioEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.window_size = window_size
        self.commission = commission
        self.n_assets = len(df.columns)
        
        # Define action and observation space
        # Action space: portfolio weights (sum to 1)
        self.action_space = spaces.Box(
            low=0, high=1, 
            shape=(self.n_assets + 1,),  # +1 for cash position
            dtype=np.float32
        )
        
        # Observation space: prices, returns, portfolio weights, etc.
        # Shape: (window_size * n_assets) + n_assets + 1
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=((window_size * self.n_assets) + self.n_assets + 1,),
            dtype=np.float32
        )
        
        # Initialize state
        self.reset()
    
    def reset(self) -> np.ndarray:
        """Reset the environment to initial state"""
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.portfolio = np.zeros(self.n_assets)  # Number of shares for each asset
        self.done = False
        self.profits = []
        
        # Calculate initial portfolio value
        prices = self.df.iloc[self.current_step].values
        self.portfolio_value = self.balance + np.sum(self.portfolio * prices)
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """Get the current state observation"""
        # Get price data for the window
        window_data = self.df.iloc[self.current_step - self.window_size:self.current_step]
        
        # Calculate returns and normalize
        returns = window_data.pct_change().dropna()
        if not returns.empty:
            returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # Get current prices
        current_prices = self.df.iloc[self.current_step].values
        
        # Calculate portfolio weights
        portfolio_value = self.balance + np.sum(self.portfolio * current_prices)
        if portfolio_value > 0:
            weights = np.concatenate([
                [self.balance / portfolio_value],
                (self.portfolio * current_prices) / (portfolio_value + 1e-8)
            ])
        else:
            weights = np.zeros(self.n_assets + 1)
        
        # Combine all features
        obs = np.concatenate([
            returns.values.flatten(),  # Historical returns
            current_prices / current_prices.mean(),  # Normalized current prices
            weights  # Current portfolio weights
        ]).astype(np.float32)
        
        return obs
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Take a step in the environment
        
        Args:
            action: Array of weights for each asset + cash (sum to 1)
            
        Returns:
            tuple: (observation, reward, done, info)
        """
        if self.done:
            return self._get_observation(), 0, True, {}
        
        # Normalize action to sum to 1
        action = np.clip(action, 0, 1)
        action = action / (np.sum(action) + 1e-8)
        
        # Get current and next prices
        current_prices = self.df.iloc[self.current_step].values
        next_prices = self.df.iloc[self.current_step + 1].values
        
        # Calculate current portfolio value
        portfolio_value = self.balance + np.sum(self.portfolio * current_prices)
        
        # Calculate target portfolio values
        target_values = action * portfolio_value
        
        # Calculate new portfolio (number of shares)
        new_portfolio = target_values[1:] / (current_prices + 1e-8)
        
        # Calculate transaction costs
        trade_values = np.abs(new_portfolio - self.portfolio) * current_prices
        transaction_cost = np.sum(trade_values) * self.commission
        
        # Update portfolio and balance
        self.portfolio = new_portfolio
        self.balance = target_values[0] - transaction_cost
        
        # Calculate new portfolio value
        new_portfolio_value = self.balance + np.sum(self.portfolio * next_prices)
        
        # Calculate reward (log return)
        reward = np.log(new_portfolio_value) - np.log(portfolio_value)
        
        # Update step
        self.current_step += 1
        self.portfolio_value = new_portfolio_value
        self.profits.append(new_portfolio_value - self.initial_balance)
        
        # Check if episode is done
        self.done = (self.current_step >= len(self.df) - 2) or (new_portfolio_value <= 0)
        
        # Additional info
        info = {
            'portfolio_value': new_portfolio_value,
            'return': (new_portfolio_value / self.initial_balance) - 1,
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'volatility': self._calculate_volatility(),
            'transaction_cost': transaction_cost
        }
        
        return self._get_observation(), reward, self.done, info
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0, window: int = 30) -> float:
        """Calculate Sharpe ratio for the latest window of returns"""
        if len(self.profits) < 2:
            return 0.0
            
        returns = np.diff(self.profits[-window:]) / (np.array(self.profits[:-1]) + 1e-8)
        
        if len(returns) < 2:
            return 0.0
            
        excess_returns = returns - (risk_free_rate / 252)  # Annual to daily
        return np.sqrt(252) * (excess_returns.mean() / (returns.std() + 1e-8))
    
    def _calculate_volatility(self, window: int = 30) -> float:
        """Calculate annualized volatility for the latest window"""
        if len(self.profits) < 2:
            return 0.0
            
        returns = np.diff(self.profits[-window:]) / (np.array(self.profits[:-1]) + 1e-8)
        
        if len(returns) < 2:
            return 0.0
            
        return returns.std() * np.sqrt(252)  # Annualized
    
    def render(self, mode: str = 'human') -> None:
        """Render the environment"""
        if mode == 'human':
            print(f'Step: {self.current_step}, Value: {self.portfolio_value:.2f}')
    
    def close(self) -> None:
        """Close the environment"""
        pass


class TensorboardCallback(BaseCallback):
    """
    Custom callback for logging additional values to TensorBoard
    """
    def __init__(self, verbose=0):
        super(TensorboardCallback, self).__init__(verbose)
        self.episode_returns = []
        self.episode_values = []
        
    def _on_step(self) -> bool:
        # Log scalar values (here a random variable)
        if 'episode' in self.locals:
            self.episode_returns.append(self.locals['rewards'][0])
            self.episode_values.append(self.locals['values'][0])
            
            if len(self.episode_returns) > 0:
                self.logger.record('train/episode_return', np.mean(self.episode_returns))
                self.logger.record('train/episode_value', np.mean(self.episode_values))
                self.episode_returns = []
                self.episode_values = []
                
        return True


def train_rl_agent(data: pd.DataFrame, total_timesteps: int = 10000) -> PPO:
    """
    Train a PPO agent on the given data
    
    Args:
        data: DataFrame with historical price data (columns: assets, index: dates)
        total_timesteps: Total number of timesteps to train for
        
    Returns:
        PPO: Trained agent
    """
    # Create environment
    env = DummyVecEnv([lambda: Monitor(PortfolioEnv(data))])
    
    # Initialize PPO agent
    model = PPO(
        'MlpPolicy', 
        env, 
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        clip_range_vf=None,
        ent_coef=0.0,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=dict(
            net_arch=dict(pi=[64, 64], vf=[64, 64]),
            activation_fn=torch.nn.ReLU,
            ortho_init=True
        )
    )
    
    # Train the agent
    callback = TensorboardCallback()
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback,
        progress_bar=True
    )
    
    return model


def evaluate_agent(model: PPO, env: gym.Env, n_episodes: int = 10) -> Dict[str, Any]:
    """
    Evaluate the trained agent
    
    Args:
        model: Trained PPO model
        env: Environment to evaluate on
        n_episodes: Number of episodes to evaluate for
        
    Returns:
        Dict with evaluation metrics
    """
    episode_returns = []
    episode_values = []
    portfolio_values = []
    
    for _ in range(n_episodes):
        obs = env.reset()
        done = False
        episode_return = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_return += reward
            
            if done:
                episode_returns.append(episode_return)
                portfolio_values.append(info[0].get('portfolio_value', 0))
                break
    
    # Calculate metrics
    metrics = {
        'mean_return': float(np.mean(episode_returns)),
        'std_return': float(np.std(episode_returns)),
        'mean_portfolio_value': float(np.mean(portfolio_values)),
        'sharpe_ratio': float(np.mean(episode_returns) / (np.std(episode_returns) + 1e-8) * np.sqrt(252)),
        'win_rate': float(np.mean(np.array(episode_returns) > 0))
    }
    
    return metrics


def run_rl_analysis(token_portador: str, activos: List[Dict], fecha_desde: str, fecha_hasta: str):
    """
    Run RL-based portfolio optimization
    
    Args:
        token_portador: Authentication token for API
        activos: List of assets with their details
        fecha_desde: Start date (YYYY-MM-DD)
        fecha_hasta: End date (YYYY-MM-DD)
    """
    import streamlit as st
    
    st.title("Análisis de Portafolio con Aprendizaje por Refuerzo")
    st.warning("⚠️ Esta es una característica experimental. Los resultados pueden variar y no deben considerarse como asesoramiento financiero.")
    
    # Add a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Load historical data
    with st.spinner('Cargando datos históricos...'):
        try:
            # Use existing function to get historical data
            from app import get_historical_data_for_optimization
            historical_data = get_historical_data_for_optimization(token_portador, activos, fecha_desde, fecha_hasta)
            
            if not historical_data:
                st.error("No se pudieron cargar los datos históricos. Verifica la conexión y los parámetros.")
                return None
            
            # Combine data into a single DataFrame
            prices = pd.concat([df['precio'].rename(asset['simbolo']) 
                              for asset, df in zip(activos, historical_data.values())], 
                             axis=1)
            
            # Drop any rows with missing values
            prices = prices.dropna()
            
            if len(prices) < 30:  # Minimum data points required
                st.error("No hay suficientes datos históricos para el análisis.")
                return None
                
            progress_bar.progress(20)
            status_text.text("Datos históricos cargados correctamente")
            
        except Exception as e:
            st.error(f"Error al cargar los datos históricos: {str(e)}")
            return None
    
    # Train RL agent
    with st.spinner('Entrenando el agente de RL... Esto puede tomar unos minutos...'):
        try:
            model = train_rl_agent(prices, total_timesteps=10000)
            progress_bar.progress(70)
            status_text.text("Entrenamiento del agente completado")
            
        except Exception as e:
            st.error(f"Error durante el entrenamiento del agente: {str(e)}")
            return None
    
    # Evaluate the agent
    with st.spinner('Evaluando el agente...'):
        try:
            env = DummyVecEnv([lambda: Monitor(PortfolioEnv(prices))])
            metrics = evaluate_agent(model, env, n_episodes=5)
            progress_bar.progress(90)
            status_text.text("Evaluación completada")
            
        except Exception as e:
            st.error(f"Error durante la evaluación del agente: {str(e)}")
            return None
    
    # Display results
    st.success("¡Análisis completado exitosamente!")
    progress_bar.progress(100)
    
    # Show performance metrics
    st.subheader("Métricas de Desempeño")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Retorno Promedio", f"{metrics['mean_return']*100:.2f}%")
    with col2:
        st.metric("Volatilidad", f"{metrics['std_return']*100:.2f}%")
    with col3:
        st.metric("Valor del Portafolio", f"${metrics['mean_portfolio_value']:,.2f}")
    with col4:
        st.metric("Ratio de Sharpe", f"{metrics['sharpe_ratio']:.2f}")
    
    # Show portfolio allocation
    st.subheader("Asignación Óptima del Portafolio")
    
    # Get the final portfolio allocation from the trained model
    env = PortfolioEnv(prices)
    obs = env.reset()
    done = False
    portfolio_values = [env.portfolio_value]
    dates = [prices.index[0]]
    actions = []
    
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        actions.append(action)
        obs, reward, done, info = env.step(action)
        portfolio_values.append(env.portfolio_value)
        if env.current_step < len(prices) - 1:
            dates.append(prices.index[env.current_step])
    
    # Get the final action (portfolio weights)
    final_weights = actions[-1] if actions else np.zeros(len(activos) + 1)
    
    # Create a DataFrame with the allocation (excluding cash for now)
    allocation = pd.DataFrame({
        'Activo': ['Efectivo'] + [asset['simbolo'] for asset in activos],
        'Asignación (%)': (final_weights * 100).round(2)
    })
    
    # Display allocation as a pie chart (excluding cash if it's zero)
    if final_weights[0] > 0.01:  # Only show cash if it's > 1%
        fig = go.Figure(data=[go.Pie(
            labels=allocation['Activo'],
            values=allocation['Asignación (%)'],
            hole=0.3,
            textinfo='label+percent',
            textposition='inside'
        )])
    else:
        # Exclude cash from the pie chart
        fig = go.Figure(data=[go.Pie(
            labels=allocation['Activo'][1:],
            values=allocation['Asignación (%)'][1:],
            hole=0.3,
            textinfo='label+percent',
            textposition='inside'
        )])
    
    fig.update_layout(
        title='Distribución del Portafolio Óptimo',
        showlegend=True,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display allocation as a table
    st.dataframe(allocation, use_container_width=True)
    
    # Plot portfolio value over time
    st.subheader("Evolución del Valor del Portafolio")
    
    # Calculate benchmark (equal-weighted portfolio)
    benchmark_returns = prices.pct_change().mean(axis=1).dropna()
    benchmark_values = [100000]  # Starting with 100,000
    for r in benchmark_returns[1:]:
        benchmark_values.append(benchmark_values[-1] * (1 + r))
    
    # Create the performance chart
    fig = go.Figure()
    
    # Add portfolio value
    fig.add_trace(go.Scatter(
        x=dates[:len(portfolio_values)],
        y=portfolio_values,
        mode='lines',
        name='Portafolio RL',
        line=dict(color='#636EFA')
    ))
    
    # Add benchmark (equal-weighted)
    fig.add_trace(go.Scatter(
        x=prices.index[:len(benchmark_values)],
        y=benchmark_values[:len(prices)],
        mode='lines',
        name='Benchmark (Igual Ponderado)',
        line=dict(color='#FFA15A', dash='dash')
    ))
    
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Valor del Portafolio (ARS)',
        showlegend=True,
        template='plotly_dark',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add download button for the portfolio allocation
    csv = allocation.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Asignación del Portafolio",
        data=csv,
        file_name="asignacion_portafolio_optimo.csv",
        mime="text/csv",
        help="Descargar la asignación de activos óptima en formato CSV"
    )
    
    # Add some explanations
    with st.expander("📝 ¿Cómo interpretar estos resultados?"):
        st.markdown("""
        - **Portafolio RL**: Muestra el rendimiento de la estrategia de aprendizaje por refuerzo.
        - **Benchmark (Igual Ponderado)**: Muestra el rendimiento de una cartera con asignación igualitaria entre todos los activos.
        - **Ratio de Sharpe**: Mide el rendimiento ajustado al riesgo. Valores mayores a 1 son generalmente considerados buenos.
        - **Volatilidad**: Mide la variabilidad de los rendimientos. Una menor volatilidad generalmente indica menor riesgo.
        
        💡 Recuerda que los rendimientos pasados no son indicativos de resultados futuros.
        """)
    
    return model
