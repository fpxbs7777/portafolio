import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras.optimizers import Adam
from collections import deque
import random
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

class PortfolioEnvironment:
    """Environment for portfolio optimization using reinforcement learning"""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = 100000, window_size: int = 30):
        """
        Initialize the environment with historical data
        
        Args:
            data: DataFrame with historical price data (columns: assets, index: dates)
            initial_balance: Initial portfolio balance in ARS
            window_size: Number of days to look back for state representation
        """
        self.data = data
        self.initial_balance = initial_balance
        self.window_size = window_size
        self.n_assets = len(data.columns)
        
        # Initialize state
        self.reset()
    
    def reset(self) -> np.ndarray:
        """Reset the environment to initial state"""
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.portfolio = np.zeros(self.n_assets)  # Number of shares for each asset
        self.done = False
        
        # Calculate initial portfolio value
        prices = self.data.iloc[self.current_step].values
        self.portfolio_value = self.balance + np.sum(self.portfolio * prices)
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Get the current state representation"""
        # Get price data for the window
        window_data = self.data.iloc[self.current_step - self.window_size:self.current_step]
        
        # Calculate returns
        returns = window_data.pct_change().dropna()
        
        # Normalize the data
        normalized_data = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # Flatten the window data into a 1D array
        state = normalized_data.values.flatten()
        
        # Add portfolio allocation and balance info
        portfolio_info = np.concatenate([
            [self.balance / self.initial_balance],
            self.portfolio / (np.sum(self.portfolio) + 1e-8)  # Normalized portfolio weights
        ])
        
        return np.concatenate([state, portfolio_info])
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Take a step in the environment
        
        Args:
            action: Array of weights for each asset (sum to 1)
            
        Returns:
            tuple: (next_state, reward, done, info)
        """
        # Get current and next prices
        current_prices = self.data.iloc[self.current_step].values
        next_prices = self.data.iloc[self.current_step + 1].values
        
        # Calculate portfolio value before rebalancing
        old_portfolio_value = self.balance + np.sum(self.portfolio * current_prices)
        
        # Rebalance portfolio according to action
        total_value = old_portfolio_value
        new_weights = action / (np.sum(np.abs(action)) + 1e-8)  # Normalize weights
        
        # Calculate target values for each asset
        target_values = new_weights * total_value
        
        # Calculate new portfolio (number of shares)
        new_portfolio = target_values / current_prices
        
        # Update portfolio and balance (assuming no transaction costs for now)
        self.portfolio = new_portfolio
        self.balance = total_value - np.sum(self.portfolio * current_prices)
        
        # Calculate new portfolio value
        new_portfolio_value = self.balance + np.sum(self.portfolio * next_prices)
        
        # Calculate reward (log return)
        reward = np.log(new_portfolio_value) - np.log(old_portfolio_value)
        
        # Update step
        self.current_step += 1
        self.portfolio_value = new_portfolio_value
        
        # Check if episode is done
        self.done = (self.current_step >= len(self.data) - 2) or (new_portfolio_value <= 0)
        
        # Get next state
        next_state = self._get_state()
        
        # Additional info
        info = {
            'portfolio_value': new_portfolio_value,
            'return': (new_portfolio_value / self.initial_balance) - 1,
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'volatility': self._calculate_volatility()
        }
        
        return next_state, reward, self.done, info
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0, window: int = 30) -> float:
        """Calculate Sharpe ratio for the latest window of returns"""
        if self.current_step <= self.window_size + 1:
            return 0.0
            
        start_idx = max(0, self.current_step - window)
        returns = self.data.iloc[start_idx:self.current_step].pct_change().dropna()
        
        if len(returns) < 2:
            return 0.0
            
        excess_returns = returns - (risk_free_rate / 252)  # Annual to daily
        return np.sqrt(252) * (excess_returns.mean() / (returns.std() + 1e-8)).mean()
    
    def _calculate_volatility(self, window: int = 30) -> float:
        """Calculate annualized volatility for the latest window"""
        if self.current_step <= 1:
            return 0.0
            
        start_idx = max(0, self.current_step - window)
        returns = self.data.iloc[start_idx:self.current_step].pct_change().dropna()
        
        if len(returns) < 2:
            return 0.0
            
        return returns.std() * np.sqrt(252)  # Annualized


class DQNAgent:
    """Deep Q-Network agent for portfolio optimization"""
    
    def __init__(self, state_size: int, action_size: int):
        """
        Initialize the DQN agent
        
        Args:
            state_size: Size of the state space
            action_size: Number of assets in the portfolio
        """
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95  # discount factor
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
    
    def _build_model(self) -> tf.keras.Model:
        """Build the neural network model"""
        model = Sequential([
            Dense(64, input_dim=self.state_size, activation='relu'),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(self.action_size, activation='softmax')  # Output portfolio weights
        ])
        
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def update_target_model(self):
        """Update the target model with weights from the online model"""
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state: np.ndarray) -> np.ndarray:
        """Select action using epsilon-greedy policy"""
        if np.random.rand() <= self.epsilon:
            # Random action (exploration)
            action = np.random.rand(self.action_size)
            return action / np.sum(action)  # Normalize to sum to 1
            
        # Exploitation: use the model to predict the best action
        act_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return act_values[0]  # Return the action with highest Q-value
    
    def replay(self, batch_size: int):
        """Train the model on a batch of experiences"""
        if len(self.memory) < batch_size:
            return
            
        minibatch = random.sample(self.memory, batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                # Use target model for stability
                target = reward + self.gamma * np.amax(self.target_model.predict(next_state.reshape(1, -1), verbose=0)[0])
                
            # Get current Q-values from the model
            target_f = self.model.predict(state.reshape(1, -1), verbose=0)
            
            # Update the target for the taken action
            target_f[0] = action * target + (1 - action) * target_f[0]
            
            # Train the model
            self.model.fit(state.reshape(1, -1), target_f, epochs=1, verbose=0)
            
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


def train_rl_agent(data: pd.DataFrame, episodes: int = 100, batch_size: int = 32) -> DQNAgent:
    """
    Train a DQN agent on the given data
    
    Args:
        data: DataFrame with historical price data (columns: assets, index: dates)
        episodes: Number of episodes to train for
        batch_size: Size of batches for training
        
    Returns:
        DQNAgent: Trained agent
    """
    # Initialize environment and agent
    env = PortfolioEnvironment(data)
    state_size = env._get_state().shape[0]
    action_size = env.n_assets
    agent = DQNAgent(state_size, action_size)
    
    # Lists to store metrics
    portfolio_values = []
    returns = []
    
    # Training loop
    for e in range(episodes):
        state = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            # Get action from agent
            action = agent.act(state)
            
            # Take action in environment
            next_state, reward, done, info = env.step(action)
            
            # Store experience
            agent.remember(state, action, reward, next_state, done)
            
            # Train on batch of experiences
            agent.replay(batch_size)
            
            # Update state and metrics
            state = next_state
            episode_reward += reward
            
            if done:
                portfolio_values.append(info['portfolio_value'])
                returns.append(info['return'])
                
                if (e + 1) % 10 == 0:
                    print(f"Episode: {e+1}/{episodes}, "
                          f"Portfolio Value: {info['portfolio_value']:.2f}, "
                          f"Return: {info['return']*100:.2f}%, "
                          f"Sharpe: {info['sharpe_ratio']:.2f}, "
                          f"Volatility: {info['volatility']*100:.2f}%")
                break
    
    # Update target model after training
    agent.update_target_model()
    
    # Plot training results
    plot_training_results(portfolio_values, returns, data.columns)
    
    return agent


def plot_training_results(portfolio_values: List[float], returns: List[float], asset_names: List[str]):
    """Plot training results"""
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add portfolio value trace
    fig.add_trace(go.Scatter(
        y=portfolio_values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='royalblue')
    ))
    
    # Add returns trace (secondary y-axis)
    fig.add_trace(go.Scatter(
        y=returns,
        mode='lines',
        name='Cumulative Return',
        yaxis='y2',
        line=dict(color='firebrick')
    ))
    
    # Update layout
    fig.update_layout(
        title='Training Results',
        xaxis_title='Episode',
        yaxis_title='Portfolio Value (ARS)',
        yaxis2=dict(
            title='Cumulative Return',
            titlefont=dict(color='firebrick'),
            tickfont=dict(color='firebrick'),
            anchor='x',
            overlaying='y',
            side='right',
            tickformat=".1%"
        ),
        showlegend=True,
        template='plotly_dark'
    )
    
    # Save the plot
    os.makedirs('plots', exist_ok=True)
    fig.write_html('plots/training_results.html')
    
    # Show the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def run_rl_analysis(token_portador: str, activos: List[Dict], fecha_desde: str, fecha_hasta: str):
    """
    Run RL-based portfolio optimization
    
    Args:
        token_portador: Authentication token for API
        activos: List of assets with their details
        fecha_desde: Start date (YYYY-MM-DD)
        fecha_hasta: End date (YYYY-MM-DD)
    """
    st.title("Análisis de Portafolio con Aprendizaje por Refuerzo")
    
    # Load historical data
    with st.spinner('Cargando datos históricos...'):
        # Use existing function to get historical data
        from app import get_historical_data_for_optimization
        historical_data = get_historical_data_for_optimization(token_portador, activos, fecha_desde, fecha_hasta)
        
        if not historical_data:
            st.error("No se pudieron cargar los datos históricos. Verifica la conexión y los parámetros.")
            return
        
        # Combine data into a single DataFrame
        prices = pd.concat([df['precio'].rename(asset['simbolo']) 
                           for asset, df in zip(activos, historical_data.values())], 
                          axis=1)
    
    # Train RL agent
    with st.spinner('Entrenando el agente de RL...'):
        agent = train_rl_agent(prices)
    
    # Show final portfolio allocation
    st.subheader("Asignación Óptima del Portafolio")
    
    # Get final state and predict action
    env = PortfolioEnvironment(prices)
    state = env.reset()
    action = agent.act(state)
    
    # Create a DataFrame with the allocation
    allocation = pd.DataFrame({
        'Activo': [asset['simbolo'] for asset in activos],
        'Asignación (%)': (action * 100).round(2)
    })
    
    # Display allocation as a pie chart
    fig = go.Figure(data=[go.Pie(
        labels=allocation['Activo'],
        values=allocation['Asignación (%)'],
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
    
    # Show performance metrics
    st.subheader("Métricas de Desempeño")
    
    # Simulate the strategy on test data
    test_env = PortfolioEnvironment(prices)
    state = test_env.reset()
    done = False
    portfolio_values = [test_env.portfolio_value]
    
    while not done:
        action = agent.act(state)
        state, _, done, _ = test_env.step(action)
        portfolio_values.append(test_env.portfolio_value)
    
    # Calculate metrics
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
    annualized_return = (1 + total_return/100) ** (252/len(portfolio_values)) - 1
    volatility = np.std(returns) * np.sqrt(252) * 100
    sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Retorno Total", f"{total_return:.2f}%")
    with col2:
        st.metric("Retorno Anualizado", f"{annualized_return*100:.2f}%")
    with col3:
        st.metric("Volatilidad Anualizada", f"{volatility:.2f}%")
    with col4:
        st.metric("Ratio de Sharpe", f"{sharpe_ratio:.2f}")
    
    # Plot portfolio value over time
    st.subheader("Evolución del Valor del Portafolio")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prices.index,
        y=portfolio_values,
        mode='lines',
        name='Valor del Portafolio',
        line=dict(color='royalblue')
    ))
    
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Valor del Portafolio (ARS)',
        showlegend=True,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add download button for the portfolio allocation
    csv = allocation.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Asignación del Portafolio",
        data=csv,
        file_name="asignacion_portafolio_optimo.csv",
        mime="text/csv"
    )
