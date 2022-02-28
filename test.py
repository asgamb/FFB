from tools.Classes import ForecastingJob


il = 1
load = True
save = False
fj = ForecastingJob("aa", "aa", "lstmCPUEnhanced", "node_cpu_seconds_total", il, "dtcontrolvnf-1")
steps_back = 10
steps_forw = 1
if load:
    loadfile = 'trainedModels/test.h5'
else:
    loadfile = 'data/dataset_train.csv'
savefile = 'trainedModels/test.h5'
features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
#features = ['avg_rtt_a1', 'avg_rtt_a2', 'r_a1', 'r_a2']
main_feature = 'cpu0'

fj.set_model(steps_back, steps_forw, load, loadfile, save, features, main_feature, savefile)

data ={}
'''
data['cpu0'] = [0.0, 15.82, 29.78, 43.78, 57.73, 71.73, 85.73, 99.72, 113.7, 127.72]
data['avg_rtt_a1'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_rtt_a2'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_loss_a1'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_loss_a2'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['#robots'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
data['r_a1'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
data['r_a2'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
'''

a = []
a.append("1309420.95;217.7;0.0;217.7;1.18;0.0;0.0;0.0;1;0;1")
a.append("1309434.87;216.8;0.0;216.8;1.37;0.0;0.0;0.0;1;0;1")
a.append("1309448.79;215.5;0.0;215.5;1.27;0.0;0.0;0.0;1;0;1")
a.append("1309462.78;215.9;0.0;215.9;1.44;0.0;0.0;0.0;1;0;1")
a.append("1309476.77;216.4;0.0;216.4;1.31;0.0;0.0;0.0;1;0;1")
a.append("1309490.74;218.4;0.0;218.4;1.47;0.0;0.0;0.0;1;0;1")
a.append("1309504.68;216.7;0.0;216.7;1.36;0.0;0.0;0.0;1;0;1")
a.append("1309518.64;215.5;0.0;215.5;1.29;0.0;0.0;0.0;1;0;1")
a.append("1309532.57;214.7;0.0;214.7;1.32;0.0;0.0;0.0;1;0;1")
a.append("1309546.51;214.5;0.0;214.5;1.26;0.0;0.0;0.0;1;0;1")
a.append("1309560.47;216.8;0.0;216.8;1.30;0.0;0.0;0.0;1;0;1")
a.append("1309574.43;214.3;0.0;214.3;1.39;0.0;0.0;0.0;1;0;1")
a.append("1309588.40;216.2;0.0;216.2;1.25;0.0;0.0;0.0;1;0;1")
a.append("1309602.36;216.3;0.0;216.3;1.34;0.0;0.0;0.0;1;0;1")

cpu = []
data['cpu0'] =[]
data['avg_rtt_a1'] = []
data['avg_rtt_a2'] = []
data['avg_loss_a1'] = []
data['avg_loss_a2'] = []
#data['#robots'] = []
data['r_a1'] = []
data['r_a2'] = []

for row in range(0, 10):
    line = a[row].split(';')
    data['cpu0'].append(round(float(line[0]), 1))
    data['avg_rtt_a1'].append(round(float(line[2]), 1))
    data['avg_rtt_a2'].append(round(float(line[3]), 1))
    data['avg_loss_a1'].append(round(float(line[6]), 1))
    data['avg_loss_a2'].append(round(float(line[7]), 1))
    #data['#robots'].append(round(float(line[8]), 1))
    data['r_a1'].append(round(float(line[9]), 1))
    data['r_a2'].append(round(float(line[10]), 1))

fj.set_data(data)
fj.config_t0(main_feature, 0.0)
value = fj.get_forecasting_value(10,4)

#print(1309602.36)
print(value+data['cpu0'][0])

#print(data['cpu0'][9], value)







