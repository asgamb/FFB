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

import logging

log = logging.getLogger("Forecaster")


class lstmcpudt:
    def __init__(self, file, ratio, back, forward, accuracy, features, main_feature):
        log.debug("initaite the lstm module")
        if file is None:
            self.train_file = "../data/example-fin.csv"
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
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.n_features = len(features)
        self.other_features = features
        self.main_feature = main_feature

    def split_sequences(self, sequences, n_steps_in, n_steps_out):
        X, y = list(), list()
        for i in range(len(sequences)):
            # find the end of this pattern
            end_ix = i + n_steps_in
            out_end_ix = end_ix + n_steps_out - 1
            # check if we are beyond the dataset
            if out_end_ix > len(sequences):
                break
            # gather input and output parts of the pattern
            seq_x, seq_y = sequences[i:end_ix, :-1], sequences[end_ix - 1:out_end_ix, -1]
            X.append(seq_x)
            y.append(seq_y)
        return array(X), array(y)

    # train the model
    def train(self, save, filename, split):
        class mycallback(Callback):
            def on_epoch_end(self, epoch, logs={}):
                if (logs.get('accuracy') is not None and logs.get('accuracy') >= 0.9):
                    print("\n Reached 90% accuracy so cancelling training")
                    self.model.stop_training = True

        callback = mycallback()

        train_df = self.data_preparation(None, train=True)
        X, y = self.split_sequences(train_df, self.look_backward, self.look_forward)
        split_point = split
        train_X, train_y = X[:split_point, :], y[:split_point, :]
        test_X, test_y = X[split_point:, :], y[split_point:, :]
        opt = keras.optimizers.Adam(learning_rate=0.0001)
        # define model
        n_features = len(self.other_features) + 1
        self.model = Sequential()
        self.model.add(LSTM(50, activation='relu', return_sequences=True, input_shape=(self.look_backward, n_features)))
        self.model.add(LSTM(50, activation='relu'))
        self.model.add(Dense(self.look_forward))
        self.model.add(Activation('linear'))
        #self.model.compile(loss='mse', optimizer=opt, metrics=['mse'])
        # Fit network
        #self.model.fit(train_X, train_y, epochs=60, steps_per_epoch=25, verbose=1,
        #                    validation_data=(test_X, test_y), shuffle=False)

        self.model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
        self.model.fit(train_X, train_y, epochs=1200, steps_per_epoch=25, callbacks=[callback],
                       validation_data=(test_X, test_y), shuffle=False)
        if save:
            self.model.save(filename)
        return self.model

    def load_trained_model(self, filename):
        log.info("LSTM: Loading the lstm model from file {}".format(filename))
        self.model = load_model(filename)
        return self.model

    def predict(self, db):
        log.debug("LSTM: Predicting the value")
        other_fatures, main_feature = self.data_preparation(db);
        if other_fatures is not None:
            y_pred_inv = self.predict_deep(other_fatures, main_feature, 1, self.look_backward,
                                           (self.look_backward+self.look_forward))
            #print(y_pred_inv)
            temp = []
            for val in y_pred_inv:
                temp.append("%.2f" % val)
            #print(temp)
            return temp
        else:
            return 0

    def set_train_file(self, file):
        self.train_file = file

    def predict_deep(self, dataset_test, y_test, start, end, last):

        # prepare test data X
        dataset_test_X = dataset_test[start:end, :]
        test_X_new = dataset_test_X.reshape(1, dataset_test_X.shape[0], dataset_test_X.shape[1])
        dataset_test_y = y_test[end:last, :]
        df = pandas.read_csv("algorithms/dataset_test.csv", sep=";", header=0)

        df = df.drop(labels=0, axis=0)
        cpu0 = df['cpu0'].values

        cpu0 = cpu0.reshape((len(cpu0), 1))

        scaler1 = MinMaxScaler(feature_range=(0, 1))
        scaler1.fit(cpu0)

        # predictions
        y_pred = self.model.predict(test_X_new)
        y_pred_inv = scaler1.inverse_transform(y_pred)
        y_pred_inv = y_pred_inv.reshape(self.look_forward, 1)
        #y_pred_inv = y_pred.reshape(self.look_forward, 1)

        y_pred_inv = y_pred_inv[:, 0]

        return y_pred_inv

    def data_preparation(self, db, train=False):
        temp_db = {}
        scaled_db = {}

        if train:
            print(self.train_file)
            df = pandas.read_csv(self.train_file, sep=";", header=0 )
            df = df.drop(labels=0, axis=0)
        else:
            #print(len(self.other_features))
            #print(len(db.keys()))
            if len(self.other_features) != len(db.keys())-2:
                return None, None
            else:
                df = pandas.DataFrame(data=db)

        for feature in self.other_features:
            temp_db[feature] = df[feature].values
        temp_db[self.main_feature] = df[self.main_feature].values

        # convert to [rows, columns] structure
        for feature in self.other_features:
            temp_db[feature] = temp_db[feature].reshape((len(temp_db[feature]), 1))
        temp_db[self.main_feature] = temp_db[self.main_feature].reshape((len(temp_db[self.main_feature]), 1))

        # normalization
        scaler = MinMaxScaler(feature_range=(0, 1))
        for feature in self.other_features:
            scaled_db[feature] = scaler.fit_transform(temp_db[feature])

        if train:
            main_feature_scaled = scaler.fit_transform(temp_db[self.main_feature])
            # features order
            #static
            # dataset_stacked = hstack((scaled_db['avg_rtt_a1'], scaled_db['avg_rtt_a2'],
            #                          scaled_db['avg_loss_a1'], scaled_db['avg_loss_a2'],
            #                          scaled_db['r_a1'], scaled_db['r_a2'], main_feature_scaled))
            #dynamic creation
            dataset_stacked = np.empty((len(temp_db[self.main_feature]), 1))
            for i in range(0, len(self.other_features)):
                dataset_stacked = hstack((dataset_stacked, scaled_db[self.other_features[i]]))
            dataset_stacked = hstack((dataset_stacked, main_feature_scaled))
            return dataset_stacked  # dataset_train
        #dynamic generation
        dataset_stacked = np.empty((len(temp_db[self.main_feature]), 1))
        for i in range(0, len(self.other_features)):
            dataset_stacked = hstack((dataset_stacked, scaled_db[self.other_features[i]]))
        #static generation
        # #dataset_stacked = hstack((scaled_db['avg_rtt_a1'], scaled_db['avg_rtt_a2'],
        #                          scaled_db['avg_loss_a1'], scaled_db['avg_loss_a2'],
        #                          scaled_db['r_a1'], scaled_db['r_a2']))
        return dataset_stacked, temp_db[self.main_feature]  # dataset_test
