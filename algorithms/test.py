import pandas
import numpy as np
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.models import load_model
from tensorflow.python.keras.layers import LSTM, Dense, Activation
from tensorflow.python.keras.layers import Dense
from tensorflow.python.keras.layers import RepeatVector
from tensorflow.python.keras.layers import TimeDistributed
from tensorflow.python.keras.callbacks import Callback
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler

df = pandas.read_csv("../algorithms/dataset_test.csv", sep=";", header=0)
print(df.keys())

df = df.drop(labels=0, axis=0)
print(df.keys())
cpu0 = df['cpu0'].values

cpu0 = cpu0.reshape((len(cpu0), 1))

scaler1 = MinMaxScaler(feature_range=(0, 1))
scaler1.fit(cpu0)
