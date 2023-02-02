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

#ec = ExternalConnections('configC.conf')
ec = ExternalConnections('configC.conf')

period = 5
'''
{'nsId': 'fgt-1c80901-8419-4673-8019-c4db0e22b903', 'vnfdId': 'dtcontrolvnf', 'nsdId': 'DTPoC_nsDT_Forecasting_Test_Memory', 'performanceMetric': 'VmemoryUsageMean', 'IL': 'DT_aiml_il_small'}
2023-01-16 09:50:40,961 - Forecasting API: topic fgt-1c80901-8419-4673-8019-c4db0e22b903_forecasting created
2023-01-16 09:50:40,967 - Forecasting API: scraper job 20be4c8b-687b-479b-b791-afa73392c76d created
2023-01-16 09:50:40,967 - Forecasting API: considered IL=1
2023-01-16 09:50:40,967 - Forecasting API: metric=node_memory_MemTotal_bytes and vnf=dtcontrolvnf
2023-01-16 09:50:40,973 - Forecasting API: scraper job lists=['20be4c8b-687b-479b-b791-afa73392c76d', '9e0b9a99-b8c5-4e97-9c3b-30816eec4b5c']
2023-01-16 09:50:40,973 - dtcontrolvnf-1 save data on file data/ds_dtcontrolvnf-1_6.csv
2023-01-16 09:50:40,974 - LSTM: Loading the lstm model from file trainedModels/convRAM_130_14.h5
2023-01-16 09:50:41,077 - Exception on /Forecasting [POST]
Traceback (most recent call last):
'''

vnf = "dtcontrolvnf"
nsd = "fgt-ef16443-ffc5-4f2c-b321-eff6c1eb03de"

topic = nsd + "_forecasting"

print("deleting topic")
a = ec.deleteKafkaTopic(topic)
print(a)
time.sleep(2)


line = ""

f1 = open('pjs.txt', 'r')
pjs = f1.readline().strip()
pjlist = pjs.split(';')
f1.close()
for pj in pjlist:
    print("deleting prometheus job {}".format(pj))
    a = ec.stopPrometheusJob(pj)
    print(a)
    time.sleep(2)


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
