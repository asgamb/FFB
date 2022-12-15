from tools.externalConnections import ExternalConnections
from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.error import ConsumeError
import json
import time
import os.path


monIp = "10.5.1.114"
monPort = 8989
monUrl = "/prom-manager"
kPort = 9092

csvfname = "dataset/dati.csv"

if os.path.isfile(csvfname):
    [root, end] = csvfname.split('.')
    for i in range (0,100):
        csvfname = root + str(i) + "." + end
        if not os.path.isfile(csvfname):
            break
print("save data on file {}".format(csvfname))


r1 = []
r2 = []

#ec = ExternalConnections('configC.conf')
ec = ExternalConnections('configC.conf')

clean = 1
createKafka = 0
deleteKafka = 0

startScraper = 0
stopScraper = 1

nsId = "ddt-collector-test"
vnf = "dtdtvvnf"
nsd = "fgt-b1f246a-bd93-4ffa-b32c-b78526b40c92"

topic = nsId + "_forecasting"

req = "1aa0c8e6-c26e-11eb-a8ba-782b46c1eefd"

do_header = True

temp = {}
set_temp = {}
set_temp['rtt_latency'] = False
set_temp['upstream_latency'] = False
set_temp['packet_lost'] = False
set_temp['node_cpu_seconds_total'] = False
'''
metrics["rtt_latency"] = "{instance=\"dtdtvvnf-1\",nsId=\"fgt-b1f246a-bd93-4ffa-b32c-b78526b40c92\", vnfdId=\"dtdtvvnf\"}"
metrics["upstream_latency"] = "{instance=\"dtdtvvnf-1\", nsId=\"fgt-b1f246a-bd93-4ffa-b32c-b78526b40c92\", vnfdId=\"dtdtvvnf\"}
metrics["packet_lost"] = "{instance=\"dtdtvvnf-1\", nsId=\"fgt-b1f246a-bd93-4ffa-b32c-b78526b40c92\", robot_id="10.10.10.76", vnfdId="dtdtvvnf"}
metrics["node_cpu_seconds_total"] = {mode = "idle", nsId ="fgt-b1f246a-bd93-4ffa-b32c-b78526b40c92", vnfdId="dtcontrolvnf"}
'''

metrics = {}
metrics['rtt_latency'] = 'rtt_latency{nsId=\"'+nsd+'\", vnfdId=\"'+vnf+'\"}'
metrics['upstream_latency'] = 'upstream_latency{nsId=\"'+nsd+'\", vnfdId=\"'+vnf+'\"}'
metrics['packet_lost'] = 'packet_lost{nsId=\"'+nsd+'\", vnfdId=\"'+vnf+'\"}'
#metrics['node_cpu_seconds_total'] = 'node_cpu_seconds_total{mode=\"idle\", nsId =\"'+nsd+'\", vnfdId=\"dtcontrolvnf\"}'
metrics['node_cpu_seconds_total'] = "node_cpu_seconds_total{mode=\"idle\", nsId =\""+nsd+"\", vnfdId=\"dtcontrolvnf\"}"

if clean:
   csv_file = open(csvfname, "w")
   csv_file.close()



if deleteKafka:
    print("deleting topic")
    ec.deleteKafkaTopic(topic)
    time.sleep(2)
if createKafka:
    print("creating topic")
    ec.createKafkaTopic(nsId)
    time.sleep(2)

line = ""

if stopScraper:
    print("stop the scraper jobs")
    f = open('ids.txt', 'r')
    ids = f.readline().strip()
    idlist = ids.split(';')
    f.close()
    for jobId in idlist:
        print("stopping jobid {}".format(jobId))
        ec.stopScraperJob(jobId)
        time.sleep(2)


if startScraper:
    for metric in metrics.keys():
        if metric == "node_cpu_seconds_total":
            print("skip")
            #sId = ec.startScraperJob(nsid=nsd, topic=topic, vnfdid="dtcontrolvnf", metric=metric,
            #                  expression=metrics[metric], period=15)
        else:
            sId = ec.startScraperJob(nsid=nsd, topic=topic, vnfdid=vnf, metric=metric,
                              expression=metrics[metric], period=15)
        #print(sId)
        if line != "":
            line = line + ";"
        line = line + sId
        time.sleep(2)

if line != "":
   #print(line)
   text_file = open("ids.txt", "w")
   text_file.write(line)
   text_file.close()

def reset():
    #print("after write I reset")
    set_temp['rtt_latency'] = False
    set_temp['upstream_latency'] = False
    set_temp['packet_lost'] = False
    set_temp['node_cpu_seconds_total'] = False
    temp['cpu'] = []
    del(temp['time'])
    temp['cpuv'] = []
    temp['rtt_id'] = []
    temp['rttv'] = []
    temp['up_id'] = []
    temp['upv'] = []
    temp['l_id'] = []
    temp['lv'] = []



def save_file():
    global do_header
    val = ""
    string = ""
    if do_header:
       hstring = ""
    if set_temp['node_cpu_seconds_total'] and set_temp['rtt_latency'] and set_temp['upstream_latency'] and set_temp['packet_lost']:
        temp1 = temp.copy()
        t = temp1['time']
        string = str(t)
        if do_header:
            hstring = "time"
        robs = 0
        
        if 'cpu' in temp1.keys():
           #avg_cpu = sum(temp['cpuv']) / len(temp['cpuv'])
           #string = string + ";" + str(avg_cpu)
           for i in range(0, len(temp1['cpuv'])):
             string = string + ";" + str(temp1['cpuv'][i])
             if do_header:
                hstring = hstring + ";cpu" + str(temp1['cpu'][i])
        if 'rttv' in temp1.keys():
           avg_rtt = sum(temp1['rttv']) / len(temp1['rttv'])
           string = string + ";" +  str(round(avg_rtt,2))
           if do_header:
              hstring = hstring + ";avg_rtt"
           if robs == 0:
               robs = len(temp1['rtt_id'])
           a1_rob = 0
           a2_rob = 0
           val_a1 = 0.0
           val_a2 = 0.0
           for i in range(0, len(temp1['rttv'])):
               rtt=round(float(temp1['rttv'][i]),2)
               if rtt < 150:
                   a1_rob = a1_rob + 1
                   val_a1 = val_a1 + rtt
                   if temp1['rtt_id'][i] not in r1:
                       if temp1['rtt_id'][i] not in r2:
                           r1.append(temp1['rtt_id'][i])
               else:
                   a2_rob = a2_rob + 1
                   val_a2 = val_a2 + rtt
                   if temp1['rtt_id'][i] not in r2:
                       if temp1['rtt_id'][i] not in r1:
                           r2.append(temp1['rtt_id'][i])
           if do_header:
              hstring = hstring + ";avg_rtt_a1"
              hstring = hstring + ";avg_rtt_a2"
           if a1_rob != 0:
               string = string + ";" +  str(round((val_a1/a1_rob),2))
           else:
               string = string + ";0.0"
           if a2_rob != 0:
               string = string + ";" +  str(round((val_a2/a2_rob),2))
           else:
               string = string + ";0.0"
        if 'upv' in temp1.keys():
           avg_up = sum(temp1['upv']) / len(temp1['upv'])
           string = string + ";" +  str(round(avg_up,2))
           if do_header:
              hstring = hstring + ";avg_upstream"
           if robs == 0:
               robs = len(temp1['up_id'])
        if 'lv' in temp1.keys():
           if do_header:
              hstring = hstring + ";avg_loss"
           if robs == 0:
               robs = len(temp1['l_id'])
           a1_rob = 0
           a2_rob = 0
           lv_a1 = 0.0
           lv_a2 = 0.0
           avg_l = sum(temp1['lv']) / len(temp1['lv'])
           string = string + ";" +  str(round(avg_l,2)) 
           for i in range(0, len(temp1['lv'])):
               lv = round(float(temp1['lv'][i]),5)
               if temp1['l_id'][i] in r1:
                   a1_rob = a1_rob + 1
                   lv_a1 = lv_a1 + lv
               elif temp1['l_id'][i] in r2:
                   a2_rob = a2_rob + 1
                   lv_a2 = lv_a2 + lv
           if do_header:
              hstring = hstring + ";avg_loss_a1"
              hstring = hstring + ";avg_loss_a2"
           if a1_rob != 0:
              string = string + ";" +  str(round((lv_a1/a1_rob),5))
           else:
              string = string + ";0.0"
           if a2_rob != 0:
              string = string + ";" +  str(round((lv_a2/a2_rob),5))
           else:
              string = string + ";0.0"
        if robs != 0:
           string = string + ";" +  str(robs)
           if do_header:
              hstring = hstring + ";#robots"
           #f 'upstream_latency' in temp1.keys():
           if 'upv' in temp1.keys():
               string = string + ";" +  str(a1_rob) 
               string = string + ";" +  str(a2_rob) 
               if do_header:
                  hstring = hstring + ";#r_act1" 
                  hstring = hstring + ";#r_act2" 
        csv_file = open(csvfname, "a")
        if do_header:
            hstring = hstring + "\n"
            csv_file.write(hstring)
            reset1()
        string = string + "\n"
        csv_file.write(string)
        csv_file.close()
        reset()
    #else:
    #    print(set_temp)


def reset1():
    global do_header
    do_header = False



def data_parser(json_data):
    loaded_json = json.loads(json_data)
    #print("New message: \n{}".format(loaded_json))
    '''
        'metric': {
		'__name__': 'node_cpu_seconds_total',
		'cpu': '0',
		'exporter': 'node_exporter',
		'forecasted': 'no',
		'instance': 'dtmotionvnf-1',
		'job': '036412b5-1fae-4c47-a46d-fe584248e6bf',
		'mode': 'idle',
		'nsId': 'fgt-4f61c57-9ce2-441e-9919-7674dda57c9d',
		'vnfdId': 'dtmotionvnf'
	},
	'value': [
		1635870778.757,
		'4079.07'
	],
	'type_message': 'metric'
    '''
    for element in loaded_json:
       mtype = element['type_message']
       if mtype == "metric":
          m = element['metric']['__name__']
          if "cpu" in m:
            set_temp['node_cpu_seconds_total'] = True
            cpu = element['metric']['cpu']
            t = element['value'][0]
            val = round(float(element['value'][1]),2)
            if not 'cpu' in temp.keys():
               temp['cpu'] = []
            if cpu not in temp['cpu']:
               temp['cpu'].append(cpu)
            if not 'time' in temp.keys():
               temp['time'] = t
            if not 'cpuv' in temp.keys():
               temp['cpuv'] = []
            index = temp['cpu'].index(cpu)
            if len(temp['cpuv']) == index:
               temp['cpuv'].append(val)
            else:
               temp['cpuv'][index] = val
          elif "rtt" in m:
            set_temp['rtt_latency'] = True
            rob = element['metric']['robot_id']
            t = element['value'][0]
            val = round(float(element['value'][1]),2)
            if not 'rtt_id' in temp.keys():
               temp['rtt_id'] = []
            temp['rtt_id'].append(rob)
            if not 'time' in temp.keys():
               temp['time'] = t
            if not 'rttv' in temp.keys():
               temp['rttv'] = []
            val = round(float(element['value'][1]),2)
            temp['rttv'].append(val)
          elif "upstream" in m:
            set_temp['upstream_latency'] = True
            rob = element['metric']['robot_id']
            t = element['value'][0]
            val = round(float(element['value'][1]),2)
            if not 'up_id' in temp.keys():
               temp['up_id'] = []
            temp['up_id'].append(rob)
            if not 'time' in temp.keys():
               temp['time'] = t
            if not 'upv' in temp.keys():
               temp['upv'] = []
            temp['upv'].append(val)
          elif "lost" in m:
            set_temp['packet_lost'] = True
            rob = element['metric']['robot_id']
            t = element['value'][0]
            val = round(float(element['value'][1]),5)
            if not 'l_id' in temp.keys():
               temp['l_id'] = []
            temp['l_id'].append(rob)
            if not 'time' in temp.keys():
               temp['time'] = t
            if not 'lv' in temp.keys():
               temp['lv'] = []
            temp['lv'].append(val)
    save_file()

print("Creating the consumer")

consumer = ec.createKafkaConsumer("1", topic)

while True:
    try:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                print('Forecatsing Job: %% %s [%d] reached end at offset %d\n' %
                          (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            # no error -> message received
            data_parser(msg.value())

    except KeyboardInterrupt:
        # quit
        consumer.close()
        break
    except ConsumeError as e:
        print("Forecasting Job: Consumer error: {}".format(str(e)))
        # Should be commits manually handled?
        consumer.close()


