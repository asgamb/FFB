from tools.externalConnections import ExternalConnections
from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.error import ConsumeError
import json
import time
import os.path


monIp = "10.5.1.131"
monPort = 8989
monUrl = "/prom-manager"
kPort = 9092

csvfname = "dataset/datiRAM.csv"

clean = 1
autodelete = 0
createKafka = 0
startScraper = 0
stopPJob = 1

pj = "18458cf8-ba19-4db2-a88c-5ff9387ebdbb"

if os.path.isfile(csvfname) and createKafka:
    [root, end] = csvfname.split('.')
    for i in range (0,100):
        csvfname = root + str(i) + "." + end
        if not os.path.isfile(csvfname):
            break
    print("save data on file {}".format(csvfname))


r1 = 0
r2 = 0

#ec = ExternalConnections('configC.conf')
ec = ExternalConnections('configC.conf')

period = 5


vnf = "dtcontrolvnf"
nsd = "fgt-5303095-8945-42c2-8559-1db7be94cca3"

topic = nsd + "_forecasting"

do_header = True

temp = {}
t0 = {}
t0 ['node_memory_MemFree_bytes'] = None

set_temp = {}
set_temp['node_memory_MemFree_bytes'] = False

metrics = {}
metrics['node_memory_MemFree_bytes'] = 'node_memory_MemFree_bytes{nsId=\"'+nsd+'\", forecasted=\"no\", vnfdId=\"'+vnf+'\"}'

if clean:
   csv_file = open(csvfname, "w")
   csv_file.close()



if createKafka:
    print("creating topic")
    a = ec.createKafkaTopic(nsd)
    print(a)
    time.sleep(2)
else:
    print("deleting topic")
    a = ec.deleteKafkaTopic(topic)
    print(a)
    time.sleep(2)


line = ""

if stopPJob:
    f1 = open('pjs.txt', 'r')
    pjs = f1.readline().strip()
    pjlist = pjs.split(';')
    f1.close()
    for pj in pjlist:
        print("deleting prometheus job {}".format(pj))
        a = ec.stopPrometheusJob(pj)
        print(a)
        time.sleep(2)


if startScraper:
    for metric in metrics.keys():
        if metric == "node_memory_MemFree_bytes":
            print(metrics[metric])
            #sId = ec.startScraperJob(nsid=nsd, topic=topic, vnfdid=vnf, metric=metric,
            #                  expression=metrics[metric], period=period)
        #print(sId)
        if line != "":
            line = line + ";"
        #line = line + sId
        time.sleep(2)
else:
    print("stop the scraper jobs")
    f = open('ids.txt', 'r')
    ids = f.readline().strip()
    idlist = ids.split(';')
    f.close()
    for jobId in idlist:
        print("stopping jobid {}".format(jobId))
        a = ec.stopScraperJob(jobId)
        print(a)
        time.sleep(2)

if line != "":
   #print(line)
   text_file = open("ids.txt", "w")
   text_file.write(line)
   text_file.close()

def reset():
    #print("after write I reset")
    set_temp['node_memory_MemFree_bytes'] = False
    temp['memfree_v'] = []



def save_file():
    global do_header
    val = ""
    string = ""
    if do_header:
       hstring = ""
    if set_temp['node_memory_MemFree_bytes']:
        print("done")
        temp1 = temp.copy()
        t = temp1['time']
        string = str(t)
        if do_header:
            hstring = "time"
        robs = 0
        
        if 'memfv' in temp1.keys():
           mf = int(temp1['memfv'][len(temp1['memfv'])-1])
           if t0["node_memory_MemFree_bytes"] == None:
              t0["node_memory_MemFree_bytes"] = mf
           string = string + ";" +  str(t0["node_memory_MemFree_bytes"] - mf)
           if do_header:
              hstring = hstring + ";memory_free"
        #r1
        string = string + ";" +  str(r1)
        if do_header:
            hstring = hstring + ";r_a1"
        #r2
        string = string + ";" +  str(r2)
        if do_header:
            hstring = hstring + ";r_a2"
        #write
        csv_file = open(csvfname, "a")
        if do_header:
            hstring = hstring + "\n"
            csv_file.write(hstring)
            reset1()
        string = string + "\n"
        csv_file.write(string)
        csv_file.close()
        reset()
        print("done")
    #else:
    #    print(set_temp)


def reset1():
    global do_header
    do_header = False



def data_parser(json_data):
    loaded_json = json.loads(json_data)
    print("New message: \n{}".format(loaded_json))
    '''
        'metric': {
                '__name__': 'node_memory_MemFree_bytes',
                'exporter': 'node_exporter',
                'forecasted': 'no',
                'instance': 'dtcontrolvnf-1',
                'job': '036412b5-1fae-4c47-a46d-fe584248e6bf',
                'mode': 'idle',
                'nsId': 'fgt-a3b70e2-6471-4f78-9d04-96e6671401f4'
                'vnfdId': 'dtcontrolvnf'
        },
        'value': [
                1635870778.757,
                '7001890816'
        ],
        'type_message': 'metric'
    '''
    for element in loaded_json:
       mtype = element['type_message']
       if mtype == "metric":
          m = element['metric']['__name__']
          if "MemFree" in m:
            set_temp['node_memory_MemFree_bytes'] = True
            t = element['value'][0]
            val = int(element['value'][1])
            if not 'time' in temp.keys():
               temp['time'] = t
            if not 'memfv' in temp.keys():
               temp['memfv'] = []
            temp['memfv'].append(val)
    save_file()

if createKafka:
   print("Creating the consumer on topic={}".format(topic))

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

   
   if autodelete:
       print("autodele enabled")
       print("deleting topic")
       a = ec.deleteKafkaTopic(topic)
       print(a)
       time.sleep(2)
       print("stop the scraper jobs")
       f = open('ids.txt', 'r')
       ids = f.readline().strip()
       idlist = ids.split(';')
       f.close()
       for jobId in idlist:
         print("stopping jobid {}".format(jobId))
         ec.stopScraperJob(jobId)
         time.sleep(2)

