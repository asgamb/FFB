from ..tools.Classes import ForecastingJob


il = 1
load = False
save = True
fj = ForecastingJob("aa", "aa", "lstmCPUEnhanced", "node_cpu_seconds_total", il, "dtcontrolvnf-1")
steps_back = 15
steps_forw = 4
if load:
    loadfile = 'trainedModels/lstmdiff' + str(steps_back) + '_' + str(steps_forw) + '.h5'
else:
    loadfile = 'data/dataset_train.csv'
savefile = 'trainedModels/test.h5'
features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
#features = ['avg_rtt_a1', 'avg_rtt_a2', 'r_a1', 'r_a2']
main_feature = 'cpu0'

fj.set_model(steps_back, steps_forw, load, loadfile, save, features, main_feature, savefile)

data ={}

data['cpu0'] = [0.0, 15.82, 29.78, 43.78, 57.73, 71.73, 85.73, 99.72, 113.7, 127.72]
data['avg_rtt_a1'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_rtt_a2'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_loss_a1'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['avg_loss_a2'] = ['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0']
data['#robots'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
data['r_a1'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
data['r_a2'] = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0']

fj.set_data(data)
fj.config_t0(main_feature, 0.0)
value = fj.get_forecasting_value(10, 4)
print(data['cpu0'][9], value)







