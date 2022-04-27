# Copyright 2021 Scuola Superiore Sant'Anna www.santannapisa.it
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# python and projects imports
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
from numpy import array , hstack
import joblib
from tensorflow.python.keras.callbacks import ModelCheckpoint
import os


import logging

log = logging.getLogger("Forecaster")


class lstmcpudt:
    def __init__(self, file, ratio, back, forward, accuracy, features, main_feature):
        log.debug("initaite the lstm module")
        if file is None:
            self.train_file = "data/dataset_train.csv"
        else:
            self.train_file = file
        self.dataset = None
        if ratio is None:
            self.trainset_ratio = 0.8
        else:
            self.trainset_ratio = ratio
        self.look_backward = back
        self.look_forward = forward
        if accuracy is None:
            self.desired_accuracy = 0.90
        else:
            self.desired_accuracy = accuracy
        self.model = None
        self.mmscaler = MinMaxScaler(feature_range=(0, 1))
        self.mmscaler_cpu = MinMaxScaler(feature_range=(0, 1))
        
        self.n_features = len(features)
        self.other_features = features
        self.main_feature = main_feature
        self.scaler_db ={}

    def split_sequences(self, dataset, target, start, end, window, horizon):
         # all features, main feature, 0, None, 10, 1
         X = []
         y = []
         start = start + window
         if end is None:
             end = len(dataset) - horizon
         for i in range(start, end-3):
             indices = range(i-window, i)
             X.append(dataset[indices])
             #prendo la quarta y -> y(t+4)
             indicey = range(i+3, i+3+horizon)
             y.append(target[indicey])
         return np.array(X), np.array(y)


    # train the model
    def train(self, save, filename, split):
        '''

        class mycallback(Callback):
            def on_epoch_end(self, epoch, logs={}):
                if (logs.get('accuracy') is not None and logs.get('accuracy') >= 0.65):
                    print("\n Reached 90% accuracy so cancelling training")
                    self.model.stop_training = True

        callback = mycallback()
        '''
        train_df = self.data_preparation(None, train=True)
        X = train_df.to_numpy()
        y = train_df[self.main_feature].to_numpy()
        
        start = 0
        end = None
        X_train, y_train = self.split_sequences(X, y, start, end, window=self.look_backward, horizon=self.look_forward)

        opt = keras.optimizers.Adam(learning_rate=0.0001)
        # define model
        self.model = Sequential()
        #model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(100, return_sequences=True), input_shape=x_train.shape[-2:]))
        self.model.add(LSTM(150, activation='relu', input_shape=X_train.shape[-2:]))
        #self.model.add(LSTM(150, activation='tanh', return_sequences=True, input_shape=X_train.shape[-2:]))
        #self.model.add(LSTM(50, activation='relu'))
        #self.model.add(Dense(units=10))
        #test
        self.model.add(Dense(50, activation='relu'))
        self.model.add(Dense(10, activation='relu'))


        #self.model.add(Dropout(0.5))
        self.model.add(Dense(units=self.look_forward))
        self.model.compile(loss='mse', optimizer=opt, metrics=['mse'])
        #checkpoint_filepath = 'checkpoint'
        checkpoint_path = "training_1/cp.ckpt"
        checkpoint_dir = os.path.dirname(checkpoint_path)
        checkpoint = ModelCheckpoint(filepath=checkpoint_path, monitor='mse',
                                     verbose=1, save_best_only=True, save_weights_only=True, mode='min')

        self.model.fit(X_train, y_train, epochs=400, steps_per_epoch=25, shuffle=False, verbose=1,
                       callbacks=checkpoint)
        os.listdir(checkpoint_dir)
        self.model.load_weights(checkpoint_path)

        if save:
            self.model.save(filename)
        return self.model

    def load_trained_model(self, filename):
        log.info("LSTM: Loading the lstm model from file {}".format(filename))
        self.model = load_model(filename)
        if "cpu" in self.main_feature:
            self.mmscaler = joblib.load("trainedModels/lstm_mmscaler")
            self.mmscaler_cpu = joblib.load("trainedModels/lstm_mmscaler_cpu")
        return self.model

    def predict(self, db):
        log.debug("LSTM: Predicting the value enhanced")
        print("test")
        data = self.data_preparation(db)
        num = self.n_features + 1
        if data is not None:
            y_pred_inv = self.model.predict(data.to_numpy().reshape([1, self.look_backward, num]))
            #print(y_pred_inv)
            #no scaling cpu
            #y_pred_inv = self.mmscaler_cpu.inverse_transform(y_pred_inv)
            log.info("len y pred inv {}".format(len(y_pred_inv)))
            return y_pred_inv
        else:
            return 0

    def set_train_file(self, file):
        self.train_file = file


    def data_preparation(self, db, train=False):
        temp_db = pandas.DataFrame()
        #pandas.options.dispay.float_format = “{:,.5f}”.format
        pandas.set_option('display.float_format', lambda x: f'{x:,.5f}')
        if train:
            df = pandas.read_csv(self.train_file, sep=";", header=0)
        else:
            df = pandas.DataFrame(db)

        for feature in self.other_features:
            temp_db[feature] = df[feature].values
        temp_db[self.main_feature] = df[self.main_feature].values - df[self.main_feature].values[0]

        if train:
            #replica is an array containing the list of features (including the main)
            # temp is a dataframe containing the main feature
            temp = pandas.DataFrame()
            temp = pandas.concat([temp, temp_db[self.main_feature]])
            replica = self.other_features
            replica.append(self.main_feature)
            #scaling
            #df = pandas.DataFrame(hstack([self.mmscaler.fit_transform(temp_db.loc[:, temp_db.columns != self.main_feature]),
            #                              self.mmscaler_cpu.fit_transform(temp)]), columns=replica)
            #partial scaling
            df = pandas.DataFrame(hstack([self.mmscaler.fit_transform(temp_db.loc[:, temp_db.columns != self.main_feature]),
                        temp]), columns=replica)
            # no scaling
            #df = pandas.DataFrame(hstack([temp_db.loc[:, temp_db.columns != self.main_feature],
            #            temp]), columns=replica)

            # save scaler for future use
            joblib.dump(self.mmscaler, "trainedModels/lstm_mmscaler")
            #joblib.dump(self.mmscaler_cpu, "trainedModels/lstm_mmscaler_cpu")

        else:
            temp = pandas.DataFrame()
            temp = pandas.concat([temp, temp_db[self.main_feature]])
            replica = self.other_features
            if self.main_feature not in replica:
                replica.append(self.main_feature)
            #scaling
            #df = pandas.DataFrame(
            #    hstack([self.mmscaler.transform(temp_db.loc[:, temp_db.columns != self.main_feature]),
            #            self.mmscaler_cpu.transform(temp)]), columns=replica)
            #partial scaling
            df = pandas.DataFrame(
                hstack([self.mmscaler.transform(temp_db.loc[:, temp_db.columns != self.main_feature]),
                        temp]), columns=replica)
            # no scaling
            #df = pandas.DataFrame(
                #hstack([temp_db.loc[:, temp_db.columns != self.main_feature],temp]), columns=replica)
        return df
