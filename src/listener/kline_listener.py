import psycopg2
import psycopg2.extensions
import select
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import yaml
import pandas as pd
import time
import sys
import numpy as np

# Add the src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

# Now import the Indicator class
from indicator.indicator import Indicator

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'kline_listener.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KlineListener:
    def __init__(self, source_db_params: Dict[str, str], target_db_params: Dict[str, str],
                 source_table: str = None, target_table: str = None):
        """
        Initialize connections to both source and target databases.
        
        Args:
            source_db_params: Connection parameters for BitunixData database
            target_db_params: Connection parameters for Indicator database
            source_table: Name of the source table to listen to (e.g., 'btcusdt_1')
            target_table: Name of the target table for indicators (defaults to source_table_indicators)
        """
        self.source_db_params = source_db_params
        self.target_db_params = target_db_params
        self.source_conn = None
        self.target_conn = None
        
        # Store table information
        self.source_table = source_table
        self.target_table = target_table or (f"{source_table}_indicators" if source_table else None)
        
        # Parse metadata from table name
        self.symbol = None
        self.timeframe = None
        if source_table:
            self._parse_table_metadata(source_table)

    def _parse_table_metadata(self, table_name: str) -> None:
        """Parse symbol and timeframe from table name."""
        parts = table_name.split('_')
        if len(parts) >= 2:
            self.symbol = parts[0].replace('usdt', '')
            self.timeframe = parts[1]
            logger.info(f"Parsed metadata - Symbol: {self.symbol}, Timeframe: {self.timeframe}")

    def set_tables(self, source_table: str, target_table: str = None) -> None:
        """
        Set or update the source and target tables.
        
        Args:
            source_table: Name of source table
            target_table: Optional name of target table (will use source_table_indicators if not provided)
        """
        if not source_table:
            raise ValueError("Source table name cannot be empty")
        
        self.source_table = source_table
        self.target_table = target_table or f"{source_table}_indicators"
        self._parse_table_metadata(source_table)
        logger.info(f"Set tables - Source: {self.source_table}, Target: {self.target_table}")

    def get_historical_data(self, end_ts: datetime, min_periods: int = 50) -> pd.DataFrame:
        """
        Get historical data from source table, ensuring enough data for all indicators.
        
        Args:
            end_ts: End timestamp for the data
            min_periods: Minimum number of periods needed (default 50 for complex indicators)
        
        Returns:
            DataFrame with historical data
        """
        if not self.source_table:
            raise ValueError("Source table not set. Call set_tables() first.")
        
        # Calculate required periods based on indicators
        required_periods = max(
            50,  # Base minimum
            14 + 14 + 3,  # Stochastic RSI (RSI period + Stoch period + smoothing)
            26 + 9,  # MACD (slow period + signal)
            20,  # Bollinger Bands
            min_periods  # User specified minimum
        )
        
        logger.info(f"Fetching {required_periods} periods of historical data")
        
        with self.source_conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, ts, CAST(open AS FLOAT), CAST(high AS FLOAT), 
                       CAST(low AS FLOAT), CAST(close AS FLOAT)
                FROM {self.source_table}
                WHERE ts <= %s
                ORDER BY ts DESC
                LIMIT %s
            """, (end_ts, required_periods))
            
            data = cur.fetchall()
            if len(data) < required_periods:
                logger.warning(f"Only found {len(data)} periods of data, needed {required_periods}")
            
            # Important: Reverse the data to get chronological order
            df = pd.DataFrame(data[::-1], columns=['id', 'ts', 'open', 'high', 'low', 'close'])
            df['ts'] = pd.to_datetime(df['ts'])
            
            logger.info(f"Retrieved {len(df)} rows of historical data")
            return df

    def connect(self) -> None:
        """Establish database connections"""
        try:
            # Connect to source database (BitunixData)
            self.source_conn = psycopg2.connect(**self.source_db_params)
            self.source_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Connect to target database (Indicator)
            self.target_conn = psycopg2.connect(**self.target_db_params)
            self.target_conn.autocommit = True
            
            logger.info("Successfully connected to both databases")
        except Exception as e:
            logger.error(f"Error connecting to databases: {str(e)}")
            raise

    def create_indicator_table(self, table_name: str) -> None:
        """Create indicator table if it doesn't exist"""
        try:
            with self.target_conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        source_id INTEGER UNIQUE NOT NULL,
                        ts TIMESTAMP NOT NULL,
                        open NUMERIC(18,8),
                        high NUMERIC(18,8),
                        low NUMERIC(18,8),
                        close NUMERIC(18,8),
                        ema_14 NUMERIC(18,8),
                        rsi_14 NUMERIC(18,8),
                        bb_upper NUMERIC(18,8),
                        bb_middle NUMERIC(18,8),
                        bb_lower NUMERIC(18,8),
                        stoch_rsi NUMERIC(18,8),
                        stoch_k NUMERIC(18,8),
                        stoch_d NUMERIC(18,8),
                        atr NUMERIC(18,8),
                        cci NUMERIC(18,8),
                        roc_12 NUMERIC(18,8),
                        momentum_14 NUMERIC(18,8),
                        williams_r_14 NUMERIC(18,8),
                        macd_line NUMERIC(18,8),
                        macd_signal NUMERIC(18,8),
                        macd_histogram NUMERIC(18,8),
                        ichimoku_tenkan NUMERIC(18,8),
                        ichimoku_kijun NUMERIC(18,8),
                        ichimoku_senkou_a NUMERIC(18,8),
                        ichimoku_senkou_b NUMERIC(18,8),
                        ichimoku_chikou NUMERIC(18,8),
                        keltner_upper NUMERIC(18,8),
                        keltner_middle NUMERIC(18,8),
                        keltner_lower NUMERIC(18,8),
                        donchian_upper NUMERIC(18,8),
                        donchian_middle NUMERIC(18,8),
                        donchian_lower NUMERIC(18,8),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.target_conn.commit()
                logger.info(f"Created/verified indicator table: {table_name}")
                
        except Exception as e:
            self.target_conn.rollback()
            logger.error(f"Error creating indicator table {table_name}: {str(e)}")
            raise

    def _normalize_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to standard format"""
        # Map common variations to standard format
        timeframe_map = {
            '1': '1m',
            '3': '3m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '1h',
            '60m': '1h',
            '120': '2h',
            '240': '4h',
            '360': '6h',
            '720': '12h',
            '1440': '1d'
        }
        
        # If timeframe is already in correct format, return it
        if timeframe in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']:
            return timeframe
        
        # Try to get from map, otherwise append 'm'
        return timeframe_map.get(timeframe, f"{timeframe}m")

    def process_notification(self, payload: Dict[str, Any]) -> None:
        """Process notification and calculate indicators"""
        try:
            # Update tables based on payload
            source_table = payload['table']
            self.set_tables(source_table)
            
            timeframe = self._normalize_timeframe(payload['timeframe'])
            logger.info(f"Processing {self.symbol} {timeframe} data update")
            
            # Set the target table and ensure it exists
            self.target_table = f"{source_table}_indicators"
            self._ensure_indicator_table()
            
            # Get historical data with increased periods
            historical_df = self.get_historical_data(
                end_ts=payload['data']['ts'],
                min_periods=100  # Increased for better indicator calculation
            )
            
            # Debug logging
            logger.info(f"Retrieved {len(historical_df)} rows of historical data")
            logger.info(f"Data range: {historical_df['ts'].min()} to {historical_df['ts'].max()}")
            logger.info(f"Data length before calculations: {len(historical_df)}")
            
            # Ensure enough data for calculations
            if len(historical_df) < 50:
                logger.warning("Insufficient data for reliable calculations")
                return
            
            try:
                close = historical_df['close']
                high = historical_df['high']
                low = historical_df['low']
                
                # EMA (14 periods)
                ema = close.ewm(span=14, adjust=False).mean()
                
                # RSI (14 periods)
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                # Bollinger Bands (20 periods)
                bb_middle = close.rolling(window=20).mean()
                bb_std = close.rolling(window=20).std()
                bb_upper = bb_middle + (bb_std * 2)
                bb_lower = bb_middle - (bb_std * 2)
                
                # Stochastic RSI
                stoch_rsi = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min())
                stoch_k = stoch_rsi.rolling(3).mean()
                stoch_d = stoch_k.rolling(3).mean()
                
                # ATR (14 periods)
                tr1 = high - low
                tr2 = abs(high - close.shift())
                tr3 = abs(low - close.shift())
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(14).mean()
                
                # CCI (14 periods)
                typical_price = (high + low + close) / 3
                mean_dev = pd.Series(np.zeros_like(typical_price))
                for i in range(14, len(typical_price)):
                    mean_dev.iloc[i] = abs(typical_price.iloc[i-14:i] - typical_price.iloc[i-14:i].mean()).mean()
                cci = (typical_price - typical_price.rolling(14).mean()) / (0.015 * mean_dev)
                
                # ROC (12 periods)
                roc = ((close - close.shift(12)) / close.shift(12)) * 100
                
                # Momentum (14 periods)
                momentum = close - close.shift(14)
                
                # Williams %R (14 periods)
                highest_high = high.rolling(14).max()
                lowest_low = low.rolling(14).min()
                williams_r = ((highest_high - close) / (highest_high - lowest_low)) * -100
                
                # MACD (fixed calculation)
                exp12 = close.ewm(span=12, adjust=False).mean()
                exp26 = close.ewm(span=26, adjust=False).mean()
                macd_line = exp12 - exp26
                macd_signal = macd_line.ewm(span=9, adjust=False).mean()
                macd_hist = macd_line - macd_signal
                
                # Ichimoku Cloud (new)
                high_values = high.rolling(window=9).max()
                low_values = low.rolling(window=9).min()
                ichimoku_tenkan = (high_values + low_values) / 2  # Conversion Line (9)
                
                high_values26 = high.rolling(window=26).max()
                low_values26 = low.rolling(window=26).min()
                ichimoku_kijun = (high_values26 + low_values26) / 2  # Base Line (26)
                
                ichimoku_senkou_a = ((ichimoku_tenkan + ichimoku_kijun) / 2).shift(26)  # Leading Span A
                
                high_values52 = high.rolling(window=52).max()
                low_values52 = low.rolling(window=52).min()
                ichimoku_senkou_b = ((high_values52 + low_values52) / 2).shift(26)  # Leading Span B
                
                ichimoku_chikou = close.shift(-26)  # Lagging Span
                
                # Keltner Channels (fixed calculation)
                typical_price = (high + low + close) / 3
                keltner_middle = typical_price.ewm(span=20, adjust=False).mean()
                tr1 = high - low
                tr2 = abs(high - close.shift())
                tr3 = abs(low - close.shift())
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(14).mean()
                keltner_upper = keltner_middle + (2 * atr)
                keltner_lower = keltner_middle - (2 * atr)
                
                # Donchian Channels (fixed calculation)
                donchian_upper = high.rolling(window=20).max()
                donchian_lower = low.rolling(window=20).min()
                donchian_middle = (donchian_upper + donchian_lower) / 2

                # Update results dictionary with all indicators
                results = {
                    'ema_14': float(ema.iloc[-1]),
                    'rsi_14': float(rsi.iloc[-1]),
                    'bb_upper': float(bb_upper.iloc[-1]),
                    'bb_middle': float(bb_middle.iloc[-1]),
                    'bb_lower': float(bb_lower.iloc[-1]),
                    'stoch_rsi': float(stoch_rsi.iloc[-1]),
                    'stoch_k': float(stoch_k.iloc[-1]),
                    'stoch_d': float(stoch_d.iloc[-1]),
                    'atr': float(atr.iloc[-1]),
                    'cci': float(cci.iloc[-1]),
                    'roc_12': float(roc.iloc[-1]),
                    'momentum_14': float(momentum.iloc[-1]),
                    'williams_r_14': float(williams_r.iloc[-1]),
                    'macd_line': float(macd_line.iloc[-1]),
                    'macd_signal': float(macd_signal.iloc[-1]),
                    'macd_histogram': float(macd_hist.iloc[-1]),
                    'ichimoku_tenkan': float(ichimoku_tenkan.iloc[-1]),
                    'ichimoku_kijun': float(ichimoku_kijun.iloc[-1]),
                    'ichimoku_senkou_a': float(ichimoku_senkou_a.iloc[-1] if not pd.isna(ichimoku_senkou_a.iloc[-1]) else 0),
                    'ichimoku_senkou_b': float(ichimoku_senkou_b.iloc[-1] if not pd.isna(ichimoku_senkou_b.iloc[-1]) else 0),
                    'ichimoku_chikou': float(ichimoku_chikou.iloc[-1] if not pd.isna(ichimoku_chikou.iloc[-1]) else 0),
                    'keltner_upper': float(keltner_upper.iloc[-1]),
                    'keltner_middle': float(keltner_middle.iloc[-1]),
                    'keltner_lower': float(keltner_lower.iloc[-1]),
                    'donchian_upper': float(donchian_upper.iloc[-1]),
                    'donchian_middle': float(donchian_middle.iloc[-1]),
                    'donchian_lower': float(donchian_lower.iloc[-1])
                }

                # Handle any NaN values
                results = {k: 0 if pd.isna(v) else v for k, v in results.items()}

                # Debug logging
                logger.info("Final indicator values for insertion:")
                logger.info(f"EMA: {results['ema_14']:.4f}")
                logger.info(f"RSI: {results['rsi_14']:.4f}")
                logger.info(f"Stoch RSI: {results['stoch_rsi']:.4f}")
                logger.info(f"MACD Line: {results['macd_line']:.4f}")
                logger.info(f"Ichimoku Tenkan: {results['ichimoku_tenkan']:.4f}")
                logger.info(f"Keltner Upper: {results['keltner_upper']:.4f}")
                logger.info(f"Donchian Upper: {results['donchian_upper']:.4f}")

            except Exception as e:
                logger.error(f"Error in indicator calculations: {str(e)}")
                return

            # Add debug logging before INSERT
            logger.info("=== DEBUG: Values being inserted ===")
            logger.info(f"MACD values - Line: {results['macd_line']}, Signal: {results['macd_signal']}, Histogram: {results['macd_histogram']}")
            logger.info(f"Ichimoku values - Tenkan: {results['ichimoku_tenkan']}, Kijun: {results['ichimoku_kijun']}")
            logger.info(f"Keltner values - Upper: {results['keltner_upper']}, Middle: {results['keltner_middle']}, Lower: {results['keltner_lower']}")

            # Modified INSERT statement to include ALL indicators
            sql = f"""
                INSERT INTO {self.target_table} (
                    source_id, ts, open, high, low, close,
                    ema_14, rsi_14, bb_upper, bb_middle, bb_lower,
                    stoch_rsi, stoch_k, stoch_d, atr, cci,
                    roc_12, momentum_14, williams_r_14,
                    macd_line, macd_signal, macd_histogram,
                    ichimoku_tenkan, ichimoku_kijun, ichimoku_senkou_a, ichimoku_senkou_b, ichimoku_chikou,
                    keltner_upper, keltner_middle, keltner_lower,
                    donchian_upper, donchian_middle, donchian_lower
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (source_id) DO UPDATE SET
                    ema_14 = EXCLUDED.ema_14,
                    rsi_14 = EXCLUDED.rsi_14,
                    bb_upper = EXCLUDED.bb_upper,
                    bb_middle = EXCLUDED.bb_middle,
                    bb_lower = EXCLUDED.bb_lower,
                    stoch_rsi = EXCLUDED.stoch_rsi,
                    stoch_k = EXCLUDED.stoch_k,
                    stoch_d = EXCLUDED.stoch_d,
                    atr = EXCLUDED.atr,
                    cci = EXCLUDED.cci,
                    roc_12 = EXCLUDED.roc_12,
                    momentum_14 = EXCLUDED.momentum_14,
                    williams_r_14 = EXCLUDED.williams_r_14,
                    macd_line = EXCLUDED.macd_line,
                    macd_signal = EXCLUDED.macd_signal,
                    macd_histogram = EXCLUDED.macd_histogram,
                    ichimoku_tenkan = EXCLUDED.ichimoku_tenkan,
                    ichimoku_kijun = EXCLUDED.ichimoku_kijun,
                    ichimoku_senkou_a = EXCLUDED.ichimoku_senkou_a,
                    ichimoku_senkou_b = EXCLUDED.ichimoku_senkou_b,
                    ichimoku_chikou = EXCLUDED.ichimoku_chikou,
                    keltner_upper = EXCLUDED.keltner_upper,
                    keltner_middle = EXCLUDED.keltner_middle,
                    keltner_lower = EXCLUDED.keltner_lower,
                    donchian_upper = EXCLUDED.donchian_upper,
                    donchian_middle = EXCLUDED.donchian_middle,
                    donchian_lower = EXCLUDED.donchian_lower
            """

            values = (
                int(historical_df['id'].iloc[-1]), historical_df['ts'].iloc[-1], 
                float(historical_df['open'].iloc[-1]), float(historical_df['high'].iloc[-1]), 
                float(historical_df['low'].iloc[-1]), float(historical_df['close'].iloc[-1]),
                float(results['ema_14']), float(results['rsi_14']),
                float(results['bb_upper']), float(results['bb_middle']), float(results['bb_lower']),
                float(results['stoch_rsi']), float(results['stoch_k']), float(results['stoch_d']),
                float(results['atr']), float(results['cci']),
                float(results['roc_12']), float(results['momentum_14']), float(results['williams_r_14']),
                float(results['macd_line']), float(results['macd_signal']), float(results['macd_histogram']),
                float(results['ichimoku_tenkan']), float(results['ichimoku_kijun']), 
                float(results['ichimoku_senkou_a']), float(results['ichimoku_senkou_b']), 
                float(results['ichimoku_chikou']),
                float(results['keltner_upper']), float(results['keltner_middle']), float(results['keltner_lower']),
                float(results['donchian_upper']), float(results['donchian_middle']), float(results['donchian_lower'])
            )

            try:
                with self.target_conn.cursor() as target_cur:
                    target_cur.execute(sql, values)
                    # Verify the INSERT
                    target_cur.execute(f"SELECT macd_line, ichimoku_tenkan, keltner_upper FROM {self.target_table} WHERE source_id = %s", (int(historical_df['id'].iloc[-1]),))
                    result = target_cur.fetchone()
                    logger.info(f"=== DEBUG: Verification after INSERT ===")
                    logger.info(f"Retrieved values: MACD Line: {result[0]}, Ichimoku Tenkan: {result[1]}, Keltner Upper: {result[2]}")
                self.target_conn.commit()
                logger.info(f"Successfully processed new row for {self.symbol} {timeframe}")
            except Exception as e:
                self.target_conn.rollback()
                logger.error(f"=== DEBUG: SQL Error ===")
                logger.error(f"Error executing SQL: {str(e)}")
                logger.error(f"SQL: {sql}")
                logger.error(f"Values: {values}")
                raise

        except Exception as e:
            logger.error(f"Error processing notification: {str(e)}")
            logger.error(f"Payload: {payload}")
            self.target_conn.rollback()

    def _ensure_indicator_table(self):
        """Ensure the indicator table exists"""
        try:
            with self.target_conn.cursor() as cur:
                cur.execute(f"""
                    SELECT 1 FROM {self.target_table} LIMIT 1
                """)
                if not cur.fetchone():
                    raise ValueError(f"Indicator table {self.target_table} does not exist")
        except Exception as e:
            logger.error(f"Error checking indicator table: {str(e)}")
            raise

    def listen(self) -> None:
        """Start listening for notifications"""
        if not self.source_table:
            logger.warning("No source table set. Will use table from notifications.")
            
        try:
            with self.source_conn.cursor() as cur:
                cur.execute("LISTEN kline_updates;")
                logger.info("Started listening for kline updates...")
                
                while True:
                    if select.select([self.source_conn], [], [], 5) != ([], [], []):
                        self.source_conn.poll()
                        while self.source_conn.notifies:
                            notify = self.source_conn.notifies.pop(0)
                            payload = json.loads(notify.payload)
                            self.process_notification(payload)
                            
        except Exception as e:
            logger.error(f"Error in listener: {str(e)}")
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up database connections"""
        if self.source_conn:
            self.source_conn.close()
        if self.target_conn:
            self.target_conn.close()
        logger.info("Cleaned up database connections")

    def _check_connections(self) -> None:
        """Verify database connections are active"""
        if not self.source_conn or self.source_conn.closed:
            raise ConnectionError("Source database connection is not established")
        if not self.target_conn or self.target_conn.closed:
            raise ConnectionError("Target database connection is not established")

if __name__ == "__main__":
    # Load database configurations
    config_dir = Path(__file__).parent.parent / 'config'
    
    try:
        with open(config_dir / 'database_config.yaml', 'r') as f:
            source_params = yaml.safe_load(f)
            
        with open(config_dir / 'indicator_config.yaml', 'r') as f:
            target_params = yaml.safe_load(f)
            
        logger.info("Loaded database configurations successfully")
        
        listener = KlineListener(source_params, target_params)
        
        try:
            listener.connect()
            listener.listen()
        except KeyboardInterrupt:
            logger.info("Shutting down listener...")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            listener.cleanup()
            
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {str(e)}")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
