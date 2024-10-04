import unittest, os, sys
    #unittest is Pythons built-in testing framework. OS and SYS are used to manipulate the Python runtime eenvironment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    #this line is what allows us to grab StorageManager from a sister folder utils, without needing to be where main.py is in file structure
from pathlib import Path
import shutil #Used for high-level file operations. Deleting Directories
import pandas as pd
from datetime import datetime
from utils.storage_manager import StorageManager


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        #Set up a temp directory for testing:
        self.test_base_path = 'test_storage'
        self.storage_manager = StorageManager(base_path=self.test_base_path)

        # Sample data for tests
        self.sample_df = pd.DataFrame({
            'col1':[1,2,3],
            'col2':['a','b','c']
        })
        self.sample_fig = None #replace with a Matplotlib figure if needed


    def tearDown(self):
        #Remove the temp directory after tests
        shutil.rmtree(self.test_base_path)
    
    def test_get_kline_path_date(self):
        date_type = 'Date'
       
        symbol = 'BTCUSDT'
        timeframe = '1m'

        path = self.storage_manager.get_kline_path(date_type=date_type, symbol=symbol, timeframe=timeframe)
        today_date = datetime.now().strftime('%m-%d-%Y')

        expected_path = Path(self.test_base_path) /'Kline'/ 'Date' / today_date / symbol / timeframe
        self.assertEqual(path, expected_path)
        self.assertTrue(path.exists())
        print(f"Test_Get_Kline_Path. Path created: {path}")
        #Test_Get_Kline_Path. Path created: test_storage\Kline\Date\10-03-2024\BTCUSDT\1m

    def test_get_kline_path_historical(self):
        date_type = 'Historical'
        symbol = 'BTCUSDT'
        timeframe ='1m'

        path = self.storage_manager.get_kline_path(date_type=date_type, symbol=symbol, timeframe=timeframe)

        expected_path = Path(self.test_base_path) /'Kline'/'Historical'/symbol/timeframe
        self.assertEqual(path, expected_path)
        self.assertTrue(path.exists())
        print(f"Test_Get_Kline_Path_HISTORICAL: Path created {path}")
        #Test_Get_Kline_Path_HISTORICAL: Path created test_storage\Kline\Historical\BTCUSDT\1m

    
    def test_save_and_load_dataframe(self):
        date_type = 'Date'
        date = '03-10-2024'
        symbol = 'BTCUSDT'
        timeframe = '1m'
        filename = 'test_dataframe.csv'

        path = self.storage_manager.get_kline_path(date_type=date_type, date=date, symbol=symbol, timeframe=timeframe)
        self.storage_manager.save_dataframe(self.sample_df, filename, path)

        #Verify file exists
        file_path = path / filename
        self.assertTrue(file_path.exists())

        #Load the DataFrame
        loaded_df = self.storage_manager.load_dataframe(filename,path)
        pd.testing.assert_frame_equal(self.sample_df, loaded_df)

    def test_save_and_load_dataframe_historical(self):
        date_type = 'Historical'
        symbol = 'BTCUSDT'
        timeframe = '1m'
        filename = 'test_dataframe.csv'

        path = self.storage_manager.get_kline_path(date_type=date_type, symbol=symbol, timeframe=timeframe)
        self.storage_manager.save_dataframe(self.sample_df, filename, path)

        #Verify file exists
        file_path = path / filename
        self.assertTrue(file_path.exists())

        #Load the DF
        loaded_df = self.storage_manager.load_dataframe(filename, path)
        pd.testing.assert_frame_equal(self.sample_df, loaded_df)

    def test_invalid_date_type(self):
        with self.assertRaises(ValueError):
            self.storage_manager.get_kline_path(date_type='InvalidType')

    def test_get_indicator_path(self):
        date = '10-03-2024'
        symbol = 'BTCUSDT'
        timeframe = '1m'

        path = self.storage_manager.get_indicator_path(date=date, symbol=symbol, timeframe=timeframe)

        expected_path = Path(self.test_base_path) / 'Indicator' / date / symbol / timeframe
        self.assertEqual(path, expected_path)
        self.assertTrue(path.exists())

if __name__ == '__main__':
    unittest.main()