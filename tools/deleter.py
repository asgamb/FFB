
#from tools.externalConnections import ExternalConnections
from externalConnections import ExternalConnections


createKafka = 0
deleteKafka = 0

startScraper = 0
stopScraper = 0
stopProm = 1

'''
example
{ 
        "nsId" : "fgt-8b20af7-ebc5-4fbb-9ce4-ec6b136eb6b8",
        "vnfdId" : "dtdtvvnf",
        "performanceMetric" :  "node_cpu_seconds_total",
        "nsdId" : "DTwin",
        "IL" : 1
}
'''

sj="f89e76a2-1f1c-44fe-b5d9-ec7f5c768257"
pj="6f73f902-9278-4657-b486-5f51dbc864bb"

nsId = "fgt-4f61c57-9ce2-441e-9919-7674dda57c9d"
vnfdId =  "dtdtvvnf"
performanceMetric =  "node_cpu_seconds_total"
nsdId = "DTwin"
il = 1

#expression = "avg((1 - avg by(instance) (irate("+performanceMetric+"{mode=\"idle\",nsId=\""+nsId+"\",vnfdId=\""+vnfdId+"\"}[1m]))) * 100)"
expression = performanceMetric+"{nsId=\""+nsId+"\", vnfdId=\""+vnfdId+"\" forecasted=\"no\"}"
topic = nsId + "_forecasting"


ec = ExternalConnections('../config.conf')

if deleteKafka:
    ec.deleteKafkaTopic(topic)

if createKafka:
    ec.createKafkaTopic(nsId)

if startScraper:
    sId = ec.startScraperJob(nsid = nsId, topic = topic, vnfdid = vnfdid, metric = performanceMetric,
                              expression = expression, period = 15)
    print(sId)


if stopScraper:
    sId = ec.stopScraperJob(sj)
    print(sId)

if stopProm:
    sId = ec.stopPrometheusJob(pj)
    print(sId)


