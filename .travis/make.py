# Import Dependencies
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time, os.path, datetime
import os
from flask import Flask, render_template
from alpha_vantage.timeseries import TimeSeries
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
ALPHA_KEY = server.connect(os.environ['MONGO_URL'])
ts = TimeSeries(key=ALPHA_KEY,output_format='pandas')

skipTrain = True
pullCount = 0
now = datetime.datetime.now()
todayEight = now.replace(hour=8, minute=0, second=0, microsecond=0)

def getData(abbr):
    name = str('csvs/' + abbr + '_data.csv')
    lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    
    if (lastUpdate > todayEight) == True:
        data = pd.read_csv(name)
        data = data.iloc[::-1]
    else:
        data, metadata=ts.get_daily(abbr,outputsize='full')
        global pullCount
        pullCount += 1
        if pullCount == 5:
            time.sleep(55)
            pullCount = 0
        data = data.iloc[::-1]
        data.to_csv(name)
        
    data['date'] = data.index
    return data, name, abbr

def loadScale(name):
    training_complete = pd.read_csv(name)
    training_processed = training_complete.iloc[:, 1:2].values
    scaler = MinMaxScaler(feature_range = (0, 1))
    training_scaled = scaler.fit_transform(training_processed)
    return training_complete, training_processed, scaler, training_scaled

def loadModel(training_scaled, abbr):
    model = load_model(modelName)
    name = str('csvs/' + abbr + '_data_2.csv')
    lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    
    if (lastUpdate > todayEight) == True:
        data = pd.read_csv(name)
    else:
        data2, metadata=ts.get_daily(abbr,outputsize='compact')
        global pullCount
        pullCount += 1
        if pullCount == 5:
            time.sleep(55)
            pullCount = 0
        data2 = data2.iloc[::-1]
        data2.to_csv(name)

    return model, name

def predict(name, scaler, abbr, model, training_complete):
    testing_complete = pd.read_csv(name)
    name = str('static/assets/img/' + abbr + '_predictions.png')
    testing_processed = testing_complete.iloc[:, 1:2].values
    total = pd.concat((training_complete['1. open'], testing_complete['1. open']), axis=0)
    test_inputs = total[len(total) - len(testing_complete) - 60:].values
    test_inputs = test_inputs.reshape(-1,1)
    testii = test_inputs
    test_inputs = scaler.transform(test_inputs)
    testy = scaler.inverse_transform(test_inputs)
    test_features = []
    
    for i in range(60, 161):
        test_features.append(test_inputs[i-60:i, 0])
    test_features = np.array(test_features)
    test_features = np.reshape(test_features, (test_features.shape[0], test_features.shape[1], 1))
    predictions = model.predict(test_features)

    for i in range(0,10):
        new_pred = [predictions[-1]]
        test_inputs = np.append(test_inputs,new_pred)
        test_features = []
        for j in range(60, 161+i):
            test_features.append(test_inputs[j-60:j])
        test_features = np.array(test_features)
        test_features = np.reshape(test_features, (test_features.shape[0], test_features.shape[1], 1))
        predictions = model.predict(test_features)

    predictions = scaler.inverse_transform(predictions)
    
    predname = str("csvs/" + abbr + "_prediction.csv")
    np.savetxt(predname, predictions, delimiter=",")
    print(predictions.shape)
    print(test_inputs.shape)
    print(predictions[-10::])
    
    # Plot the results -model trained with 100 epochs 
    plt.figure(figsize=(10,6))
    plt.plot(testing_processed, color='blue', label='Actual Stock Price')
    plt.plot(predictions , color='red', label='Predicted Stock Price')
    plt.title(abbr + ' Stock Price Prediction')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.savefig(name)
    # plt.show()

def runModel(abbr):
    data, name, abbr = getData(abbr)
    training_complete, training_processed, scaler, training_scaled = loadScale(name)
    model, name = loadModel(training_scaled, abbr)
    predict(name, scaler, abbr, model, training_complete)

comps = ["MSFT","AAPL","AMZN","FB","BRK-B","GOOGL","JNJ","JPM","V","PG","MA","INTC","UNH","BAC","T"]

for entry in comps:
    low = entry.lower()
    modelName = str('models/' + low + 'Model.h5')
    runModel(entry)