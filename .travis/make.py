# Import Dependencies
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time, os.path, datetime
from flask import Flask, render_template
from alpha_vantage.timeseries import TimeSeries
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from pandas.plotting import table 

# Load API key for AlphaVantage
ALPHA_KEY = os.environ['ALPHA_KEY']
ts = TimeSeries(key=ALPHA_KEY,output_format='pandas')

# DataFrame made to collect predictions from all companies to compare
comp_df = pd.DataFrame()

# pullCount will track how many API calls have been made to AlphaVantage
pullCount = 0

# # This code can be implimented optionally to check if the .csv files are 
# # up to date or if they should be updated
# now = datetime.datetime.now()
# todayEight = now.replace(hour=8, minute=0, second=0, microsecond=0)

# getData performs first of two API calls, outputs data to .csv,
def getData(abbr):
    name = str('comps/' + abbr + '/data.csv')
    
    # # Can be implemented to check if file is up to date or if API call 
    # # should be made to update data
    # lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    # if (lastUpdate > todayEight) == True:
    #     data = pd.read_csv(name)
    #     data = data.iloc[::-1]
    # else:
    #     data, metadata=ts.get_daily(abbr,outputsize='full')
    #     global pullCount
    #     pullCount += 1
    #     if pullCount == 5:
    #         time.sleep(55)
    #         pullCount = 0
    #     data = data.iloc[::-1]
    #     data.to_csv(name)
    
    # Make API call for individual company given by abbr. Save as .csv in 
    # comps folder for company. Using free version of AlphaVantage, so
    # pullCount is incremented on each call and checked. In order to not
    # exceed max limit of 5 calls per minute, time.sleep is implemented 
    # to wait before doing more calls.
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

# Create scale for model
def loadScale(name):
    training_complete = pd.read_csv(name)
    training_processed = training_complete.iloc[:, 1:2].values
    scaler = MinMaxScaler(feature_range = (0, 1))
    training_scaled = scaler.fit_transform(training_processed)
    return training_complete, training_processed, scaler, training_scaled

# Load model for individual company given by abbr, get compact version
# AlphaVantage daily return
def loadModel(training_scaled, abbr):
    uppr = abbr.upper()
    modelName = str('models/' + uppr + "Model.h5")
    model = load_model(modelName)
    name = str('comps/' + abbr + '/data_2.csv')
    
    data2, metadata=ts.get_daily(abbr,outputsize='compact')
    global pullCount
    pullCount += 1
    if pullCount == 5:
        time.sleep(55)
        pullCount = 0
    data2 = data2.iloc[::-1]
    data2.to_csv(name)

    # # Code also given earlier to check if data is up to date, not used in
    # # this implementation
    # lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    # if (lastUpdate > todayEight) == True:
    #     data = pd.read_csv(name)
    # else:
    #     data2, metadata=ts.get_daily(abbr,outputsize='compact')
    #     global pullCount
    #     pullCount += 1
    #     if pullCount == 5:
    #         time.sleep(55)
    #         pullCount = 0
    #     data2 = data2.iloc[::-1]
    #     data2.to_csv(name)

    return model, name, data2

# predict will actually make the predictions using the models and loaded data
def predict(name, scaler, abbr, model, training_complete, data2):
    testing_complete = pd.read_csv(name)
    testing_processed = testing_complete.iloc[:, 1:2].values
    total = pd.concat((training_complete['1. open'], testing_complete['1. open']), axis=0)
    test_inputs = total[len(total) - len(testing_complete) - 60:].values
    test_inputs = test_inputs.reshape(-1,1)
    test_inputs = scaler.transform(test_inputs)
    test_features = []
    
# Create 100 arrays of 60 data points to feed models
    for i in range(60, 161):
        test_features.append(test_inputs[i-60:i, 0])
    test_features = np.array(test_features)
    test_features = np.reshape(test_features, (test_features.shape[0], test_features.shape[1], 1))
    predictions = model.predict(test_features)

# Make a prediction for each day in the future one at a time and append to the 
# array of predictions to make the next day's prediction
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

# Construct dataframes to output to .csv files that will be used for visualizations 
# and tables
    pred_past = predictions[0:100]
    fut_pred = predictions[-10:]
    data2['Predictions'] = pred_past
    del data2['2. high'], data2['3. low'], data2['4. close'], data2['5. volume']
    data2.rename(columns={"1. open": "Open"}, inplace=True)
    past_predname = str('comps/' + abbr + '/prediction1.csv')
    data2.to_csv(past_predname)
    last_open = data2['Open'][-1]
    fut_dates = []
    fut_preds = []
    last_date = data2.index[-1]

# Append future dates, skipping weekends
    for pred in fut_pred:
        next_date = last_date + datetime.timedelta(days=1)
        if (next_date.weekday() == 5):
            next_date = next_date + datetime.timedelta(days=2)
        fut_dates.append(next_date.strftime("%Y-%m-%d"))
        last_date = next_date
        fut_preds.append(pred[0])
    future_preds = {'date':fut_dates, 'prediction':fut_preds}
    future_preds = pd.DataFrame(future_preds)
    future_preds.rename(columns={'date':'date','prediction':'Prediction'},inplace=True)
    future_preds.set_index('date',inplace=True)
    fut_predname = str('comps/' + abbr + '/prediction2.csv')
    future_preds.to_csv(fut_predname)

# Construct comparrison table, use margin between prediction for past/current day
# and each future day for comparison 
    table_name = str('comps/' + abbr + '/table.png')
    future_preds['margin'] = (future_preds['Prediction'] -  future_preds['Prediction'][0]); 
    comp_df[abbr] = future_preds['margin']
    future_preds_new = future_preds.values
    columns = ('Open','Margin')
    rows = ['%d day(s)' % x for x in range(1,11)]
    cell_text = []
    for row in future_preds_new:
        cell_text.append([f'{x:1.4f}' for x in row])

# Construct comparison table using matplotlib and save to .png
    the_table = plt.table(cellText=cell_text,
                            rowLabels=rows,
                            colLabels=columns,
                            loc='center')
    ax = plt.gca()
    plt.box(on=None)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.savefig(table_name,
            bbox_inches='tight',
            dpi=150,
            pad_inches=0.1
            )
    plt.box(on=None)
    
# runModel takes a company's stock market abbreviation and then calls all of the 
# functions defined above to produce new files representing both new real data and 
# new predictions
def runModel(abbr):
    data, name, abbr = getData(abbr)
    training_complete, training_processed, scaler, training_scaled = loadScale(name)
    model, name, data2 = loadModel(training_scaled, abbr)
    predict(name, scaler, abbr, model, training_complete, data2)

# Define companies and run each abbreviation through the code
comps = ["MSFT","AAPL","AMZN","FB","BRK-B","GOOGL","JNJ","JPM","V","PG","MA","INTC","UNH","BAC","T"]
for entry in comps:
    low = entry.lower()
    modelName = str('models/' + low + 'Model.h5')
    runModel(entry)

# Save .csv file containing the comparrison of all companies
comp_df.to_csv('compare/all_comps.csv')
table_name = str('compare/table.png')
comp_df_new = comp_df.values
rows = ['%d day(s)' % x for x in range(1,11)]
cell_text = []
for row in comp_df_new:
    cell_text.append([f'{x:1.3f}' for x in row])

the_table = plt.table(cellText=cell_text,
                        colLabels=comps,
                        loc='center')
the_table.auto_set_font_size(False)
the_table.set_fontsize(5.0)
ax = plt.gca()
plt.box(on=None)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
plt.savefig(table_name,
        dpi=300,
        pad_inches=0.1
        )

plt.box(on=None)