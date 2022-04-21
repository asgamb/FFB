
#from tools.externalConnections import ExternalConnections
from externalConnections import ExternalConnections


createKafka = 0
deleteKafka = 0

startScraper = 0
stopScraper = 0
stopScraperList = 0
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
sjs = []
sj="e5700ffe-a548-4341-8dc3-5929205e2a6f"
pj="041b9cb4-3cef-4519-8596-9caba0dbd277"

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


if stopScraperList:
    for sjdx in  sjs:
      sId = ec.stopScraperJob(sjdx)
      print(sId)
