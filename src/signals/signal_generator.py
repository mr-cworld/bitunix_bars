import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

class SignalGenerator:
    """
    Generates trading signals based on technical indicators.
    Works in conjunction with the Indicator class.
    """

    def __init__(self, indicator_df: pd.DataFrame):
        """
        Initialize SignalGenerator with indicator DataFrame.

        Args:
            indicator_df (pd.DataFrame): DataFrame containing calculated indicators
        """
        self.df = indicator_df.copy()
        self.logger = logging.getLogger(__name__)
        self.signals = pd.DataFrame(index=self.df.index)
        self.signals['combined_signal'] = 0  # -1 for sell, 0 for neutral, 1 for buy

    def generate_rsi_signals(self, period: int = 14, 
                           oversold: int = 30, 
                           overbought: int = 70) -> pd.Series:
        """
        Generate signals based on RSI.
        Buy when oversold, sell when overbought.
        """
        try:
            col_name = f'rsi_{period}'
            if col_name not in self.df.columns:
                self.logger.error(f"{col_name} not found in DataFrame")
                return pd.Series(0, index=self.df.index)

            signals = pd.Series(0, index=self.df.index)
            signals[self.df[col_name] < oversold] = 1  # Buy signal
            signals[self.df[col_name] > overbought] = -1  # Sell signal
            
            self.signals['rsi_signal'] = signals
            return signals
        except Exception as e:
            self.logger.error(f"Error generating RSI signals: {e}")
            return pd.Series(0, index=self.df.index)

    def generate_macd_signals(self) -> pd.Series:
        """
        Generate signals based on MACD.
        Buy when MACD crosses above signal line, sell when crosses below.
        """
        try:
            if 'macd_line' not in self.df.columns or 'macd_signal' not in self.df.columns:
                self.logger.error("MACD columns not found in DataFrame")
                return pd.Series(0, index=self.df.index)

            signals = pd.Series(0, index=self.df.index)
            
            # Generate crossover signals
            signals[(self.df['macd_line'] > self.df['macd_signal']) & 
                   (self.df['macd_line'].shift(1) <= self.df['macd_signal'].shift(1))] = 1  # Buy signal
            
            signals[(self.df['macd_line'] < self.df['macd_signal']) & 
                   (self.df['macd_line'].shift(1) >= self.df['macd_signal'].shift(1))] = -1  # Sell signal
            
            self.signals['macd_signal'] = signals
            return signals
        except Exception as e:
            self.logger.error(f"Error generating MACD signals: {e}")
            return pd.Series(0, index=self.df.index)

    def generate_bollinger_signals(self, std_dev: float = 2.0) -> pd.Series:
        """
        Generate signals based on Bollinger Bands.
        Buy when price crosses below lower band, sell when crosses above upper band.
        """
        try:
            if 'bb_upper' not in self.df.columns or 'bb_lower' not in self.df.columns:
                self.logger.error("Bollinger Bands columns not found in DataFrame")
                return pd.Series(0, index=self.df.index)

            signals = pd.Series(0, index=self.df.index)
            
            # Generate band crossing signals
            signals[self.df['close'] < self.df['bb_lower']] = 1  # Buy signal
            signals[self.df['close'] > self.df['bb_upper']] = -1  # Sell signal
            
            self.signals['bollinger_signal'] = signals
            return signals
        except Exception as e:
            self.logger.error(f"Error generating Bollinger Bands signals: {e}")
            return pd.Series(0, index=self.df.index)

    def generate_stoch_rsi_signals(self, 
                                 oversold: float = 20, 
                                 overbought: float = 80) -> pd.Series:
        """
        Generate signals based on Stochastic RSI.
        Buy when K crosses above D in oversold region, sell when K crosses below D in overbought region.
        """
        try:
            if 'stoch_rsi_14_k' not in self.df.columns or 'stoch_rsi_14_d' not in self.df.columns:
                self.logger.error("Stochastic RSI columns not found in DataFrame")
                return pd.Series(0, index=self.df.index)

            signals = pd.Series(0, index=self.df.index)
            
            # Generate crossover signals in oversold/overbought regions
            k_line = self.df['stoch_rsi_14_k']
            d_line = self.df['stoch_rsi_14_d']
            
            # Buy signals: K crosses above D in oversold region
            signals[(k_line > d_line) & 
                   (k_line.shift(1) <= d_line.shift(1)) & 
                   (k_line < oversold)] = 1
            
            # Sell signals: K crosses below D in overbought region
            signals[(k_line < d_line) & 
                   (k_line.shift(1) >= d_line.shift(1)) & 
                   (k_line > overbought)] = -1
            
            self.signals['stoch_rsi_signal'] = signals
            return signals
        except Exception as e:
            self.logger.error(f"Error generating Stochastic RSI signals: {e}")
            return pd.Series(0, index=self.df.index)

    def generate_combined_signal(self, weights: Dict[str, float] = None) -> pd.Series:
        """
        Generate combined signal using weighted average of all signals.
        
        Args:
            weights (Dict[str, float]): Dictionary of signal weights. 
                                      If None, equal weights are used.
        """
        try:
            # Default weights if none provided
            if weights is None:
                weights = {
                    'rsi_signal': 1.0,
                    'macd_signal': 1.0,
                    'bollinger_signal': 1.0,
                    'stoch_rsi_signal': 1.0
                }

            # Calculate weighted sum
            weighted_signals = pd.Series(0, index=self.df.index)
            total_weight = 0

            for signal_name, weight in weights.items():
                if signal_name in self.signals.columns:
                    weighted_signals += self.signals[signal_name] * weight
                    total_weight += weight

            if total_weight > 0:
                combined = weighted_signals / total_weight
            else:
                combined = pd.Series(0, index=self.df.index)

            # Convert to discrete signals (-1, 0, 1)
            self.signals['combined_signal'] = np.sign(combined)
            return self.signals['combined_signal']
        except Exception as e:
            self.logger.error(f"Error generating combined signal: {e}")
            return pd.Series(0, index=self.df.index)

    def get_latest_signals(self) -> Dict[str, int]:
        """Return the most recent signals for all indicators."""
        return self.signals.iloc[-1].to_dict()

    def get_signal_summary(self) -> pd.DataFrame:
        """Return a summary of all signals with their timestamps."""
        return self.signals[self.signals != 0].dropna(how='all') 