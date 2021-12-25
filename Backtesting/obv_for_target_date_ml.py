#!/usr/bin/env python
# coding: utf-8

import yfinance as yf, pandas as pd, shutil, os, time, glob, smtplib, ssl
from datetime import datetime
from joblib import dump, load
from sklearn.ensemble import RandomForestClassifier
#from get_all_tickers import get_tickers as gt

STOCK_PATH = "/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/"
#target_date = "2020-12-21"
#num_days_analyze = 10
#num_days_since_begin_prev_week = 5


def get_stock_list_path(stocks, path_to_stock_history):
    list_files = []
    for stock in stocks:
        list_files.append(path_to_stock_history + stock + ".csv")
    return list_files

def get_obv(target_date, sell_date, list_files, num_days_analyze=5, num_days_since_begin_prev_week=5, history=20):

    # OBV Analysis, feel free to replace this section with your own analysis -------------------------------------------------------------------------
    new_data = [] #  This will be a 2D array to hold our stock name and OBV score
    interval = 0  # Used for iteration
    while interval < len(list_files):
        file = list_files[interval]

        #print(file)
        Data = pd.read_csv(file)
        if len(Data) < num_days_analyze:
            interval += 1
        else:
            if len(Data.loc[Data['Date']==target_date].index) == 0:
                #print(Data.tail(1))
                interval +=1
            else:
                #print(Data.loc[Data['Date']==target_date].index)
                start_date_idx = (Data.loc[Data['Date']==target_date].index - num_days_analyze)[0]
                end_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
                Data = Data.iloc[start_date_idx:end_date_idx]
                
                #Debug
                #print(Data)
                
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
        
    return new_data



def pct_change_past_week(target_date, sell_date, num_days_analyze=5, num_days_since_begin_prev_week=5, num_stocks=10):
    list_files = (glob.glob("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/*.csv"))
    obv_data = get_obv(target_date, sell_date, list_files, 
                       num_days_analyze=num_days_analyze, 
                       num_days_since_begin_prev_week=num_days_since_begin_prev_week)
    
    obv_sorted = pd.DataFrame(obv_data, columns = ['Stock', 'OBV_Value'])  # Creates a new dataframe from the new_data list
    obv_sorted["Stocks_Ranked"] = obv_sorted["OBV_Value"].rank(ascending = False)  # Rank the stocks by their OBV_Values
    obv_sorted.sort_values("OBV_Value", inplace = True, ascending = False)  # Sort the ranked stocks


    potential_stocks = obv_sorted["Stock"].head(100).tolist()
    list_files = get_stock_list_path(potential_stocks, STOCK_PATH)

    i = 0
    temp_data = []
    while i < len(list_files):
        # Read in CSV files
        file = list_files[i]
        Data = pd.read_csv(file)
        
        start_date_idx = (Data.loc[Data['Date']==target_date].index - num_days_analyze)[0]
        end_date_idx = (Data.loc[Data['Date']==target_date].index)[0]
        stock_data = Data.iloc[start_date_idx:end_date_idx]
        
        
        last_entry = stock_data.iloc[-1]

        # Get stock symbol
        stock_name = ((os.path.basename(list_files[i])).split(".csv")[0])

        temp_data.append([stock_name, stock_data.iloc[-1,0], stock_data.iloc[-1,4], 
                        stock_data.iloc[-1,8], stock_data.iloc[-1,9],
                         stock_data.iloc[-1,10], stock_data.iloc[-1,11]])
        i += 1
    

    screened_stocks = pd.DataFrame(temp_data, columns=['stock','date', 'close', 'ewa_short', 'ewa_long', 'sma_short', 'sma_long'])
    screened_ewa = screened_stocks[screened_stocks['ewa_short'] > screened_stocks['ewa_long']]
    final_screened = screened_ewa[screened_ewa['sma_short'] > screened_ewa['sma_long']]
    final_screened['ewa_change'] = (final_screened['ewa_short'] - final_screened['ewa_long']) / final_screened['ewa_long'] * 100
    final_screened['sma_change'] = (final_screened['sma_short'] - final_screened['sma_long']) / final_screened['sma_long'] * 100
    final_screened.sort_values('sma_change', ascending = False, inplace=True)
    
    
    
    top_10 = final_screened["stock"].tolist()[0:5]
    list_files = []
    for stock in top_10:
        list_files.append("/home/alekzandr/Documents/robinhood/Daily_Stock_Report/Stocks/" + stock + ".csv")
    
    # Debug: Display Selected Stocks
    #print(top_10)

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
