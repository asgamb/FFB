from tools.Classes import ForecastingJob
from tools.externalConnections import ExternalConnections
from threading import Thread, Event
from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.error import ConsumeError
import sys

ec = ExternalConnections('config.conf')

il = 1
load = True
save = False

intopic = "inputTopic"
outopic = "outputTopic"

producer = ec.createKafkaProducer()

fj = ForecastingJob("test", "test", "lstmCPUEnhanced", "node_cpu_seconds_total", il, "dtcontrolvnf-1", outTopic=outopic,
                    output=producer)
#input and output features
steps_back = 10
steps_forw = 4
if load:
    # input model file to be loaded (no train)
    #loadfile = 'trainedModels/lstmdiff' + str(steps_back) + '_' + str(steps_forw) + '.h5'
    loadfile = 'trainedModels/newLSTM.h5'
else:
    #dataset to be used for training in case load is False
    loadfile = 'data/dataset_train.csv'
#output model file
savefile = 'trainedModels/newLSTM.h5'
features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
#features = ['avg_rtt_a1', 'avg_rtt_a2', 'r_a1', 'r_a2']
main_feature = 'cpu0'

fj.set_model(steps_back, steps_forw, load, loadfile, save, features, main_feature, savefile)

data ={}

'''
data['cpu0'] = [0.0, 15.82, 29.78, 43.78, 57.73, 71.73, 85.73, 99.72, 113.7, 127.72]
data['avg_rtt_a1'] =  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
data['avg_rtt_a2'] =  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
data['avg_loss_a1'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
data['avg_loss_a2'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
data['#robots'] =     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
data['r_a1'] =        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
data['r_a2'] =        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
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
data['#robots'] = []
data['r_a1'] = []
data['r_a2'] = []

for row in range(0, 10):
    line = a[row].split(';')
    data['cpu0'].append(round(float(line[0]), 1))
    data['avg_rtt_a1'].append(round(float(line[2]), 1))
    data['avg_rtt_a2'].append(round(float(line[3]), 1))
    data['avg_loss_a1'].append(round(float(line[6]), 1))
    data['avg_loss_a2'].append(round(float(line[7]), 1))
    data['#robots'].append(round(float(line[8]), 1))
    data['r_a1'].append(round(float(line[9]), 1))
    data['r_a2'].append(round(float(line[10]), 1))

fj.set_data(data)
fj.config_t0(main_feature, data['cpu0'][0])
value = fj.get_forecasting_value(10, 4)

for row in range(10, len(a)):
    line = a[row].split(';')
    data['cpu0'].append(round(float(line[0]), 1))
    data['avg_rtt_a1'].append(round(float(line[2]), 1))
    data['avg_rtt_a2'].append(round(float(line[3]), 1))
    data['avg_loss_a1'].append(round(float(line[6]), 1))
    data['avg_loss_a2'].append(round(float(line[7]), 1))
    data['#robots'].append(round(float(line[8]), 1))
    data['r_a1'].append(round(float(line[9]), 1))
    data['r_a2'].append(round(float(line[10]), 1))

print(data['cpu0'][13], value)


event = Event()
t = Thread(target=fj.run, args=(event, ec.createKafkaConsumer(il, intopic), False))
t.start()

consumer = ec.createKafkaConsumer(il, outopic)

while True:
    try:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                sys.stderr.write('%% %s [%d] reached end at offset %d\n' % (msg.topic(),
                                                                                      msg.partition(),
                                                                                      msg.offset()))
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            sys.stderr.write(msg.value())

    except ConsumeError as e:
        sys.stderr.write("Consumer error: {}".format(str(e)))
        # Should be commits manually handled?
        consumer.close()
    except KeyboardInterrupt:
        event.set()
        t.join()
        #ec.deleteKafkaTopic(intopic)
        #ec.deleteKafkaTopic(outopic)
        break





