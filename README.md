# bitunix_bars

Next Steps
1. main.py --> CSV_Data_Processor (rename and move into data_processing folder)
2. plotter.py -> new file in (data_processing) that will plot data and save pngs into a folder system in (storage)
3. api_chart appender -> Take new data and add to historical data frame for that symbol, will need same tech for indicators 
4. Day Collector (main run) -> Give it asset, get all data for all timeframes for that asset, run all indicators on that data -> on Daily-Cruncher now!


Dev Log 1
Learned that I need to expand scope immediately. Starting with Folder 1 - API_Clients, will be all the objects that can fetch data from APIs. Will use this same folder to later get API calls on DXY, Interest Rates, and other Financial Indicators.
Next Steps:
Data Processing 1, be able to look into the storage folder, find right csv, and do some basic data pulling/analysis. 

Dev Log 2
Data Processing -> Indicators.py created
This will be the object that is sent a dataframe (df = pd.read_csv("API QUERY I JUST DID"), data = Indicator(df), data.ema(5), to call the Ema on that data, verbage could be better but this will be baseline way that code interacts) then you could set each to be graphed/plotted by matplot lib or directly, save these pngs. 

Dev Log 3
main.py -> First data processor to call the objects we've created and run data analysis (adding indicator columns to the dataframe we imported with the Client object (BitUnixAPI)). Eventually, change main.py to be part of the data_processing folder called like Data_CSV_Processor or something lame, saves everything the dataframe does to a custom csv. Next File to create --> Indicator Plotter, takes the dataframe or csv and plots it, saves the png's, and we will use them for machine learning data/training data. Saving PNGs is where we make a smarter saving system to be used everywhere. 

Dev Log 4
Created the "Daily_Saver.py" in API_Clients and "Daily_Cruncher.py" in data_processing - these are the files that will take the objects I've created and then use them to gather data (right now, hardcoded lists of times and symbols), and then adds indicators to the data and saves that. Both of these need to be expanded to be better but the bones are there. Next item to build, the plotting and saving of the plots.


Working Todo List
 1. Saving CSVs Smarter - should include DateTime to them?, isnt the datetime of the candles more relevant? for bitunix it is same though.. should be okay for now
 2. Move the main.py workflow into the data_processing folder, remove old bitunix_public.py file. 

# What Every File is doing:
    A. api_clients folder:
        1. __init__py:
        2. api_client_bitunix - Handles API interactions with the BitUnix platform
        3. base_api_client - provides a base class with common funcationalities for all API clients
        4. Daily_Saver - saves daily fetche data from APIs to the storage system
    
    B. Data Processing
        1. __init__
        2. daily_cruncher - Aggregates and processes daily data for analysis
        3. indicators - calcualtes financial indicators EMA based on dataframes
        4. plotter - generates plots from processed data and saves them as a PNG file

    C. Storage 
        1. Kline Manages Kline (Bar Data) storage and retreival
        2. Where the files go

    D. Storage
        1. __init__.py - Initializes the Storage package
        2. Test_storage_manager - -contains tests for the storagne manager function
    
    C. Utils
        1. __init__
        2. constants - defines constant values used throughout the project
        3. storage_manager - handles storage operations such as reading and writing data