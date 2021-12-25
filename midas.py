from datetime import datetime
import shutil, os, time, glob, smtplib, ssl
import pandas as pd
import numpy as np
import yfinance as yf


class Midas:
    """
    This is the base class for a Project MIDAS object. It used for downloading, manipulating, and backtesting
    different swing trading strategies.
    
    :param stock_data_path: Path to the where you will save or access historical stock information.
    :type stock_data_path: str, optional
    
    :param stocks: A list of current stock symbols in string format held by Project MIDAS.
    :type stocks: list, optional
    
    :param selected_stocks: A list of stocks for which Project MIDAS will download financial information.
    :type selected_stocks: list, optional
    """
    
    
    def __init__(self, stock_data_path=None, selected_stocks=None):
        """
        Constructor method
        """
        self.stock_data_path = stock_data_path
        self.stocks = []
        self.selected_stocks=None
        
    def set_selected_stocks(self, list_of_stocks):
        """
        Set the stocks for which Project MIDAS will download financial information.
        :param list_of_stocks: A list of stock symbols.
        :type list_of_stocks: list
        """
        self.selected_stocks = list_of_stocks
        
    def get_selected_stocks(self):
        """
        Returns the stocks for which Project MIDAS will download financial information.
        :return: List of stock symbols
        :rtype: list
        """
        return self.selected_stocks
    
    def set_stocks(self, list_of_stocks):
        """
        Set the current stocks held by Project MIDAS
        :param list_of_stocks: A list of stock symbols.
        :type list_of_stocks: list
        """
        self.stocks = list_of_stocks
        
    def get_stocks(self):
        """
        Returns the current stock symbols held by Project MIDAS
        :return: List of stock symbols
        :rtype: list
        """
        return self.stocks
        
    def set_stock_data(self, stock_data_path):
        """
        Set the path for saving and accessing stock data.
        :param stock_data_path: Path to data
        :type stock_data_path: str
        """
        self.stock_data_path = stock_data_path
        
    def get_stock_data(self):
        """
        Returns the path to where stock data is stored
        :return: Path to where historical stock data is stored
        :rtype: str
        """
        return self.stock_data_path
    
    def download_stocks(self, path=None, api_call_limit=2000):
        """
        Creates the appropriate directory structures and downloads financial data from Yahoo finance. Will
        synchronize stocks on disk with MIDAS object. So if a stock's data cannot be downloaded, it will be
        removed from self.selected_stocks.
        :param path: Path to download stock data.
        :param api_call_limit: Max number of API calls to Yahoo finance. Terms of Services is 2000 per hour.
        """
        if path != None:
            self.set_stock_data(path)

        self.__make_stock_directory(self.get_stock_data())
        
        amount_of_api_calls = 0
        limit_of_api_calls = api_call_limit
        stock_failure = 0
        stocks_not_imported = 0
        tickers = self.get_selected_stocks()
        base_path = self.get_stock_data()
        stock_path = base_path + "/Stocks/"
        
        start_time = datetime.now()
        print("[-] Started at " + str(start_time))
        
        i=0
        while (i < len(tickers)) and (amount_of_api_calls < limit_of_api_calls):
            try:
                # Gets the current stock ticker
                stock = tickers[i]  
                temp = yf.Ticker(str(stock))
                hist_data = temp.history(period="max")  
                hist_data.to_csv(stock_path+stock+".csv")
                amount_of_api_calls += 1 
                stock_failure = 0
                i += 1
                
            except ValueError:
                # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
                print("Yahoo Finance Backend Error, Attempting to Fix")
                
                # Move on to the next ticker if the current ticker fails more than 5 times
                if stock_failure > 5:  
                    i+=1
                    stocks_not_imported += 1
                amount_of_api_calls += 1
                stock_failure += 1
                
        end_time = datetime.now()
        print("[+] Completed at " + str(end_time))
        print("[*] Total Time: " + str(end_time - start_time))
        self.__sync_selected_stocks()
        print("The amount of stocks we successfully imported: " + str(len(self.get_selected_stocks())))
        
    def __sync_selected_stocks(self):
        """
        Ensures that stock data present on disk is synchronized with MIDAS object.
        """
        base_path = self.get_stock_data()
        stock_path = base_path + "/Stocks/"
        temp_selected_stocks = self.get_selected_stocks()
        list_symbols = self.__get_symbols_present_on_disk()
        common_symbols = list(set(list_symbols).intersection(temp_selected_stocks))     
        self.set_selected_stocks(common_symbols)
    
    def __test_file_path(self, path):
        """
        Tests to see if a path to save files exists.
        :param path: The path to check if the directory exists.
        :return: True of False is path exists
        :rtype: bool
        """
        return os.path.exists(path)
    
    def __make_stock_directory(self, path):
        """
        Creates a directory structure for storying stock data.
        :param path: The path to create a directory in.
        """
        base_path = path
        stock_path = base_path + "/Stocks/"
        
        if os.path.exists(base_path):
            shutil.rmtree(base_path)
            os.makedirs(base_path)
            os.makedirs(stock_path)
        else:
            os.makedirs(base_path)
            os.makedirs(stock_path)
            
    def __get_symbols_present_on_disk(self):
        base_path = self.get_stock_data()
        stock_path = base_path + "/Stocks/"
        list_files = (glob.glob(stock_path+"*.csv"))
        list_symbols = [self.__get_stock_name_from_file(file) 
                        for file
                        in list_files
                        if self.__get_nrows_in_file(file) > 0]
        return list_symbols
        
    def __get_stock_name_from_file(self, file):
        """
        Returns the stock symbol from the filename.
        :param file: A file which assumes the filename is the stock symbol.
        :return: A stock symbol
        :rtype: str
        """
        symbol = ((os.path.basename(file)).split(".csv")[0])
        return symbol
    
    def __get_nrows_in_file(self, file):
        """
        Returns the number of rows in a file
        :param file: Path to a CSV file that was downloaded.
        :return: The number of rows in the file
        :rtype: int
        """
        data = pd.read_csv(file)
        return len(data.index)    
        
    def __update_selected_stocks(self, list_of_symbols):
        """
        Updates the MIDAS object's selected_stocks with list_of_symbols
        :param list_of_symbols: A list of stock symbols.
        """
        base_path = self.get_stock_data()
        stock_path = base_path + "/Stocks/"
        temp_selected_stocks = self.get_selected_stocks()
        list_symbols = list_of_symbols
        common_symbols = list(set(list_symbols).intersection(temp_selected_stocks))     
        self.set_selected_stocks(common_symbols)
        
    def __get_data_for_timeframe(self, file, start_date, end_date):
        """
        Returns a dataframe containing the financial data between the start and end dates inclusive.
        :param file: The a Yahoo Finance CSV file containing financial data.
        :param start_date: The start date to find.
        :param end_date: The end date to find.
        :return: A pandas dataframe.
        :rtype: pandas.dataframe
        """
        data = pd.read_csv(file)
        try:
            start_index = (data.loc[data['Date']==start_date].index)[0]
            end_index = (data.loc[data['Date']==end_date].index)[0]
            data = data.iloc[start_index:end_index+1]
        except:
            data = None
        
        return data
    
    def __get_price_from_df(self, df, df_index=-1, price_type="open"):
        """
        Returns either the Open or Close price from the last item in the dataframe.
        :param df: A dataframe returned from __get_data_for_timeframe.
        :param df_index: The index for which to return the price. 0 for the first day, -1 for the last.
        :param price_type: "Open" for the opening price. "Close" for the closing price.
        :return: Returns a price from the from the dataframe.
        :rtype: float
        """
        price_type = price_type.lower()

        if price_type == "close":
            column = 4
        else:
            column = 1
            
        return df.iloc[df_index,column]
    
    '''
    def filter_stocks(self, start_date=None, end_date=None, price_min=5, price_max=None):
        """
        Filter selected_stocks based on different paramters.
        :param start_date: Filter stocks that have data that begins on start_date. Requries end_date.
        :param end_data: Filter stocks that have data that ends on end_date. Requires start_date.
        :param price_min: Filter stocks based on a minimum price.
        :param price_max: Filter stocks based on a maximum price. Use
        """
        list_symbols = self.__get_symbols_present_on_disk()
        
        for symbol in list_sybols:
            __get_data_for_timeframe
        
        
        TODO ^ Finish filter stocks
            TODO Iterate through list of files
                TODO Check if start and end dates exist
                TODO Add symbol of keep list if it does
            TODO Update Selected stocks with keep list
        TODO Create helper functions return a list of CSV files on disk
    '''