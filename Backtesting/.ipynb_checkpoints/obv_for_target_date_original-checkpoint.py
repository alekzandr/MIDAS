#!/usr/bin/env python
# coding: utf-8

import yfinance as yf, pandas as pd, shutil, os, time, glob, smtplib, ssl
from datetime import datetime
#from get_all_tickers import get_tickers as gt


#target_date = "2020-12-21"
#num_days_analyze = 10
#num_days_since_begin_prev_week = 5


def pct_change_past_week(target_date, sell_date, num_days_analyze=5, num_days_since_begin_prev_week=5, num_stocks=10):
    # Adjust num_days_analyze so that it contains the right amount of indicies
    #num_days_analyze = num_days_analyze - 1 
    
    list_files = (glob.glob("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/*.csv")) # Creates a list of all csv filenames in the stocks folder
    new_data = [] #  This will be a 2D array to hold our stock name and OBV score
    interval = 0  # Used for iteration
    while interval < len(list_files):
        file = list_files[interval]

        # Debug : List all files
        #print(file)
        Data = pd.read_csv(file)# Gets the last 10 days of trading for the current stock in iteration
        if len(Data) < num_days_analyze:
            interval += 1
        else:
            if len(Data.loc[Data['Date']==target_date].index) == 0:
                #print(Data.tail(1))
                interval +=1
            else:
                #print(Data.loc[Data['Date']==target_date].index)
                start_date_idx = (Data.loc[Data['Date']==target_date].index - (num_days_analyze))[0]
                end_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
                
                # Debug
                #print(end_date_idx-start_date_idx)
                #print(Data.iloc[start_date_idx])
                #print(Data.iloc[end_date_idx])
                
                
                
                Data = Data.iloc[start_date_idx:end_date_idx]
                # Debug : Get Shape of Data
                #print(Data.shape)
                #print(Data.iloc[0,0])
                #print(Data.iloc[-1,0])

                if len(Data) < num_days_analyze:
                    interval +=1
                else:
                    pos_move = []  # List of days that the stock price increased
                    neg_move = []  # List of days that the stock price increased
                    OBV_Value = 0  # Sets the initial OBV_Value to zero
                    count = 0
                    while (count < num_days_analyze):  # 10 because we are looking at the last 10 trading days
                        if Data.iloc[count,1] < Data.iloc[count,4]:  # True if the stock increased in price
                            pos_move.append(count)  # Add the day to the pos_move list
                        elif Data.iloc[count,1] > Data.iloc[count,4]:  # True if the stock decreased in price
                            neg_move.append(count)  # Add the day to the neg_move list
                        count += 1
                    count2 = 0
                    for i in pos_move:  # Adds the volumes of positive days to OBV_Value, divide by opening price to normalize across all stocks
                        OBV_Value = round(OBV_Value + (Data.iloc[i,5]/Data.iloc[i,1]))
                    for i in neg_move:  # Subtracts the volumes of negative days from OBV_Value, divide by opening price to normalize across all stocks
                        OBV_Value = round(OBV_Value - (Data.iloc[i,5]/Data.iloc[i,1]))
                    Stock_Name = ((os.path.basename(list_files[interval])).split(".csv")[0])  # Get the name of the current stock we are analyzing
                    new_data.append([Stock_Name, OBV_Value])  # Add the stock name and OBV value to the new_data list
                    #print(new_data[-1])
                    interval += 1

    df = pd.DataFrame(new_data, columns = ['Stock', 'OBV_Value'])  # Creates a new dataframe from the new_data list
    df["Stocks_Ranked"] = df["OBV_Value"].rank(ascending = False)  # Rank the stocks by their OBV_Values
    df.sort_values("OBV_Value", inplace = True, ascending = False)  # Sort the ranked stocks
    df.to_csv("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Targeted_OBV_Ranked.csv", index = False)  # Save the dataframe to a csv without the index column
    # OBV_Ranked.csv now contains the ranked stocks that we want recalculate daily and receive in a digestable format.

    Analysis = pd.read_csv("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Targeted_OBV_Ranked.csv")  # Read in the ranked stocks

    # Commented out Percent Change Code
    '''
    # Get Top 100 Stocks and find the ones with the 
    # highest percent change
    ranked_stock_changes = []
    top_100 = Analysis['Stock'].head(100)
    
    # Build a list of all the stock files
    list_files = []
    for stock in top_100:
        list_files.append("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/" + stock + ".csv")
    
    # Loop through and get the percent change for each.
    interval = 0  # Used for iteration
    
    while interval < len(list_files):
        file = list_files[interval]
        Data = pd.read_csv(file)
        
        # Using the same start and end dates as the OBV Analysis
        start_date_idx = (Data.loc[Data['Date']==target_date].index - num_days_analyze)[0]
        end_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
        
        # Grab only needed data based on dates
        Data = Data.iloc[start_date_idx:end_date_idx+1]

        # Calculate Percent Change
        open_price = Data.iloc[0,1]
        close_price = Data.iloc[-1,1]
        percent_change = ((close_price - open_price) / open_price) * 100
        
        # Get Stock Name
        stock_name = ((os.path.basename(list_files[interval])).split(".csv")[0])
        
    
        # Add to list
        ranked_stock_changes.append([stock_name, percent_change])
        
        # Tick up Counter
        interval += 1
        
    # Sort dataframe and save to a file
    df = pd.DataFrame(ranked_stock_changes, columns = ['Stock', 'Change'])  # Creates a new dataframe from the new_data list
    df["Stocks_Ranked"] = df["Change"].rank(ascending = False)  # Rank the stocks by their OBV_Values
    df.sort_values("Stocks_Ranked", inplace = True, ascending = False)
    df.to_csv("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Percent_Changed_Ranked.csv", index = False)
    
    
    
    
    
    Analysis = pd.read_csv("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Percent_Changed_Ranked.csv")
    '''
    
    top_10 = Analysis['Stock'].head(num_stocks)
    list_files = []
    for stock in top_10:
        list_files.append("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/" + stock + ".csv")
    
    # Debug : View Selected Stocks
    print(top_10)

    interval = 0  # Used for iteration
    composite_fund = []
    while interval < len(list_files):
        file = list_files[interval]
        Data = pd.read_csv(file)
        
        #start_date_idx = (Data.loc[Data['Date']==target_date].index - num_days_since_begin_prev_week)[0]
        #end_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
        
        #print(file)
        start_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
        end_date_idx = (Data.loc[Data['Date']==sell_date].index)[0]
        
        
        Data = Data.iloc[start_date_idx:end_date_idx+1]

        
        open_price = Data.iloc[0,1]
        close_price = Data.iloc[-1,1]
        #print(Data)
        stock_name = ((os.path.basename(list_files[interval])).split(".csv")[0])
        percent_change = ((close_price - open_price) / open_price) * 100
        composite_fund.append([stock_name, percent_change])
        interval +=1

    composite_fund=pd.DataFrame(composite_fund, columns = ['Stock', 'Pct_Change'])
    return composite_fund, composite_fund['Pct_Change'].mean()
