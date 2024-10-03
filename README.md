# bitunix_bars

Dev Log 1
Learned that I need to expand scope immediately. Starting with Folder 1 - API_Clients, will be all the objects that can fetch data from APIs. Will use this same folder to later get API calls on DXY, Interest Rates, and other Financial Indicators.
Next Steps:
Data Processing 1, be able to look into the storage folder, find right csv, and do some basic data pulling/analysis. 

Dev Log 2
Data Processing -> Indicators.py created
This will be the object that is sent a dataframe (df = pd.read_csv("API QUERY I JUST DID"), data = Indicator(df), data.ema(5), to call the Ema on that data, verbage could be better but this will be baseline way that code interacts) then you could set each to be graphed/plotted by matplot lib or directly, save these pngs. 

Dev Log 3
main.py -> First data processor to call the objects we've created and run data analysis (adding indicator columns to the dataframe we imported with the Client object (BitUnixAPI)). Eventually, change main.py to be part of the data_processing folder.

Working Todo List
 1. Saving CSVs Smarter - should include DateTime to them?, isnt the datetime of the candles more relevant? for bitunix it is same though.. should be okay for now
 2. Move the main.py workflow into the data_processing folder, remove old bitunix_public.py file. 
