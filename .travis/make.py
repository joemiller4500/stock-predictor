# Import Dependencies
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time, os.path, datetime
from flask import Flask, render_template
from alpha_vantage.timeseries import TimeSeries
ALPHA_KEY = os.environ['ALPHA_KEY']
ts = TimeSeries(key=ALPHA_KEY,output_format='pandas')
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from pandas.plotting import table 


skipTrain = True
pullCount = 0
now = datetime.datetime.now()
todayEight = now.replace(hour=8, minute=0, second=0, microsecond=0)

def getData(abbr):
    name = str('comps/' + abbr + '/data.csv')
    # lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    data, metadata=ts.get_daily(abbr,outputsize='full')
    global pullCount
    pullCount += 1
    if pullCount == 5:
        time.sleep(55)
        pullCount = 0
    data = data.iloc[::-1]
    data.to_csv(name)

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
        
    data['date'] = data.index
    return data, name, abbr

def loadScale(name):
    training_complete = pd.read_csv(name)
    training_processed = training_complete.iloc[:, 1:2].values
    scaler = MinMaxScaler(feature_range = (0, 1))
    training_scaled = scaler.fit_transform(training_processed)
    return training_complete, training_processed, scaler, training_scaled

def loadModel(training_scaled, abbr):
    uppr = abbr.upper()
    modelName = str('models/' + uppr + "Model.h5")
    model = load_model(modelName)
    name = str('comps/' + abbr + '/data_2.csv')
    # lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(os.path.getmtime(name))))
    
    data2, metadata=ts.get_daily(abbr,outputsize='compact')
    global pullCount
    pullCount += 1
    if pullCount == 5:
        time.sleep(55)
        pullCount = 0
    data2 = data2.iloc[::-1]
    data2.to_csv(name)

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

def predict(name, scaler, abbr, model, training_complete, data2):
    testing_complete = pd.read_csv(name)
    # name = str('static/assets/img/' + abbr + '_predictions.png')
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
    pred_past = predictions[0:100]
    fut_pred = predictions[-10:]
    # print(fut_pred)

    data2['Predictions'] = pred_past
    del data2['2. high'], data2['3. low'], data2['4. close'], data2['5. volume']
    data2.rename(columns={"1. open": "Open"}, inplace=True)
    # print(data2)
    # print(data2.index)
    # dates = data2.index
    # print(dates)

    # pred_past['date'] = dates
    
    past_predname = str('comps/' + abbr + '/prediction1.csv')
    data2.to_csv(past_predname)
    last_open = data2['Open'][-1]
    fut_dates = []
    fut_preds = []
    last_date = data2.index[-1]
    # print(last_date)
    for pred in fut_pred:
        next_date = last_date + datetime.timedelta(days=1)
        if (next_date.weekday() == 5):
            next_date = next_date + datetime.timedelta(days=2)
        fut_dates.append(next_date.strftime("%Y-%m-%d"))
        last_date = next_date
        fut_preds.append(pred[0])
    # print(last_date.weekday())
    # print(fut_dates)
    # print(fut_pred)
    # print(fut_preds)
    # fut_preds = list(fut_pred)
    # print(fut_preds)

    future_preds = {'date':fut_dates, 'prediction':fut_preds}

    future_preds = pd.DataFrame(future_preds, columns=['date','Prediction'])
    future_preds.set_index('date',inplace=True)
    print(future_preds)

    fut_predname = str('comps/' + abbr + '/prediction2.csv')
    future_preds.to_csv(fut_predname)

    table_name = str('comps/' + abbr + '/table.png')

    future_preds['margin'] = (future_preds['prediction'] -  last_open); 
    future_preds = future_preds.values
    columns = ('Open','Margin')
    rows = ['%d day(s)' % x for x in range(1,11)]
    cell_text = []
    for row in future_preds:
        cell_text.append([f'{x:1.4f}' for x in row])

    the_table = plt.table(cellText=cell_text,
                            rowLabels=rows,
                            colLabels=columns,
                            loc='center')
    ax = plt.gca()
    plt.box(on=None)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    # for 
    # print(predictions.shape)
    # print(test_inputs.shape)
    # print(predictions[-10::])
    # fig = plt.gcf()
    plt.savefig(table_name,
            bbox_inches='tight',
            dpi=150,
            pad_inches=0.1
            )
    
    plt.box(on=None)
    
    # Plot the results -model trained with 100 epochs 
    # plt.figure(figsize=(10,6))
    # plt.plot(testing_processed, color='blue', label='Actual Stock Price')
    # plt.plot(predictions , color='red', label='Predicted Stock Price')
    # plt.title(abbr + ' Stock Price Prediction')
    # plt.xlabel('Date')
    # plt.ylabel('Stock Price')
    # plt.legend()
    # plt.savefig(name)
    # plt.show()

def runModel(abbr):
    data, name, abbr = getData(abbr)
    training_complete, training_processed, scaler, training_scaled = loadScale(name)
    model, name, data2 = loadModel(training_scaled, abbr)
    predict(name, scaler, abbr, model, training_complete, data2)

comps = ["MSFT","AAPL","AMZN","FB","BRK-B","GOOGL","JNJ","JPM","V","PG","MA","INTC","UNH","BAC","T"]

for entry in comps:
    low = entry.lower()
    modelName = str('models/' + low + 'Model.h5')
    runModel(entry)
    
# Create instance of Flask app
app = Flask(__name__)

# # DATABASE_URL will contain the database connection string:
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '')
# # Connects to the database using the app config
# db = SQLAlchemy(app)
# @app.route("/")
# create route that renders index.html template
# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route("/graph")
# def graph():
#     return render_template("index4.html")

# if __name__ == "__main__":
    # app.run(debug=True)