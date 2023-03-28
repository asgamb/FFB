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
from flask import Flask, make_response, request
from flask_restplus import Resource, Api, fields
from threading import Thread, Event
import multiprocessing
import uuid
import json
from prometheus_client import REGISTRY, generate_latest
from prometheus_client.metrics_core import GaugeMetricFamily
import configparser
import logging
import time
#######

from tools.Classes import ForecastingJob
from tools.externalConnections import ExternalConnections
from tools.adapters import mconverter, instancecheck, ilmapper

devel = True
# New API implemented
# Start job
# POST http://127.0.0.1:8888/Forecasting/
# input json
'''
{ 
    "nsId" : "fgt-82f4710-3d04-429a-8243-5a2ac741fd4d",
    "vnfdId" : "spr2",
    "performanceMetric" :  "VcpuUsageMean",
    "nsdId" : nsEVS_aiml,
    "IL" : 1
}
'''
# Update IL
# PUT http://127.0.0.1:8888/Forecasting?job_id=job&IL=x
# Get list of active jobs
# GET http://127.0.0.1:8888/Forecasting
# Get details of job_id job
# GET http://127.0.0.1:8888/Forecasting?job_id=job
# stop job
# DELETE http://127.0.0.1:8888/Forecasting?job_id=job


# Add data
# PUT http://127.0.0.1:8888/Forecasting/adddata/<string:value>/<string:job>
# control status
# GET http://127.0.0.1:8888/Forecasting/control

#######

PORT = 8888  # default listening port
active_jobs = {}  # dict to store the active jobs
data = {}  # Map to save queue for each peer ip
reqs = {}  # dict to store all the instantiated jobs
aimlip = "192.168.1.1"
aimlport = 12345
aimlurl = '/aiml'

# Flask and Flask-RestPlus configuration
app = Flask(__name__)
api = Api(app, version='1.0', title='5GrForecastingPlatform')
restApi = api.namespace('', description='input REST API for forecasting requests')
prometheusApi = api.namespace('', description='REST API used by the Prometheus exporter')

# module to load FFB configuration
config = configparser.ConfigParser()
# logging configuration
# logging.basicConfig(format='%(asctime)s :: %(message)s', level=logging.DEBUG, filename='5grfbb.log')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, filename='5grfbb.log')
log = logging.getLogger("APIModule")

testForecasting = 0

ec = None

# model definition for the API
model = restApi.model("Model",
                      {
                          "nsId": fields.String,
                          "vnfdId": fields.String,
                          "performanceMetric": fields.String,
                          "nsdId": fields.String,
                          "IL": fields.Integer,
                      }
                      )


# auxiliary class used to preprocess data for the reply
class SummMessages(object):
    def __init__(self):
        self.dict_sum = {}
        self.dict_number = {}

    def add(self, element):
        metric = element.get("metric")
        name = element.get("name")
        del element['metric']
        del element['job']
        del element['name']
        if "cpu" in metric or "CPU" in metric or "Cpu" in metric:
           cpu = element.get("cpu")
           mode = element.get("mode")
           time = element.get("timestamp")
           del element['cpu']
           del element['mode']
           del element['timestamp']

        
        if "cpu" in metric or "CPU" in metric or "Cpu" in metric:
            host = name + '::' + cpu + '::' + mode + '::' + str(time)
            for key, value in element.items():
                if key in self.dict_sum.keys():
                    if host in self.dict_sum[key].keys():
                        self.dict_sum[key][host] += value
                        self.dict_number[key][host] += 1
                    else:
                        self.dict_sum[key].update({host: value})
                        self.dict_number[key].update({host: 1})
                else:
                    self.dict_sum.update({key: {host: value}})
                    self.dict_number.update({key: {host: 1}})
        if "memory_MemFree" in metric:
            host = name
            for key, value in element.items():
                if key in self.dict_sum.keys():
                    if host in self.dict_sum[key].keys():
                        self.dict_sum[key][host] += value
                        self.dict_number[key][host] += 1
                    else:
                        self.dict_sum[key].update({host: value})
                        self.dict_number[key].update({host: 1})
                else:
                    self.dict_sum.update({key: {host: value}})
                    self.dict_number.update({key: {host: 1}})
        if "memory_MemTotal" in metric:
            host = name
            for key, value in element.items():
                if key in self.dict_sum.keys():
                    if host in self.dict_sum[key].keys():
                        self.dict_sum[key][host] += value
                        self.dict_number[key][host] += 1
                    else:
                        self.dict_sum[key].update({host: value})
                        self.dict_number[key].update({host: 1})
                else:
                    self.dict_sum.update({key: {host: value}})
                    self.dict_number.update({key: {host: 1}})


    def get_result(self):
        dict_result = {}
        for parameter, value in self.dict_sum.items():
            for host, value2 in value.items():
                number = self.dict_number[parameter][host]
                result = round(value2 / number, 1)
                if parameter in dict_result.keys():
                    dict_result[parameter].append({
                        "host": host,
                        "value": result})
                else:
                    dict_result.update({parameter: [{
                        "host": host,
                        "value": result}]})
        return dict_result


# custom Prometheus exporter collector
class CustomCollector(object):
    def __init__(self):
        self.id = ""

    def collect(self):
        global data
        global testForecasting
        found_key = ""
        for key in data.keys():
            if self.id == key:
                found_key = key
        if found_key == "":
            return None

        queue = data[found_key]
        msgs = SummMessages()
        while not queue.empty():
            msgs.add(queue.get())
        result = msgs.get_result()
        metrics = []
        for parameter, values in result.items():
            if testForecasting == 0:
                if "cpu" in parameter or "CPU" in parameter or "Cpu" in parameter:
                    for value in values:
                        [instance, cpu, mode, t] = str(value['host']).split('::', 3)
                        # labels = [cpu, mode, instance, t]
                        # gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['cpu', 'mode', 'instance', 'timestamp'])
                        labels = [cpu, mode, instance]
                        gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['cpu', 'mode', 'instance'])
                        gmf.add_metric(labels, value['value'])
                        #gmf.add_metric(labels, "%.2f" % float(value['value']))
                        metrics.append(gmf)
                if "memory_MemFree" in parameter:
                    for value in values:
                        instance = str(value['host'])
                        # labels = [cpu, mode, instance, t]
                        # gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['cpu', 'mode', 'instance', 'timestamp'])
                        labels = [instance]
                        gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['instance'])
                        gmf.add_metric(labels, value['value'])
                        #gmf.add_metric(labels, "%.2f" % float(value['value']))
                        metrics.append(gmf)
                if "memory_MemTotal" in parameter:
                    for value in values:
                        instance = str(value['host'])
                        # labels = [cpu, mode, instance, t]
                        # gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['cpu', 'mode', 'instance', 'timestamp'])
                        labels = [instance]
                        gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['instance'])
                        gmf.add_metric(labels, value['value'])
                        #gmf.add_metric(labels, "%.2f" % float(value['value']))
                        metrics.append(gmf)
            else:
                if "cpu" in parameter or "CPU" in parameter or "Cpu" in parameter:
                    for value in values:
                        [instance, cpu, mode, t, input_val] = str(value['host']).split('::', 4)
                        # labels = [cpu, mode, instance, t]
                        # gmf = GaugeMetricFamily(parameter, "avg_" + parameter, labels=['cpu', 'mode', 'instance', 'timestamp'])
                        labels = [cpu, mode, instance, input_val]
                        gmf = GaugeMetricFamily(parameter, "avg_" + parameter,
                                                labels=['cpu', 'mode', 'instance', 'input'])
                        gmf.add_metric(labels, value['value'])
                        metrics.append(gmf)
        log.debug('Prometheus Exporter: New metrics computed ' + str(metrics))
        for metric in metrics:
            yield metric

    def set_parameters(self, r):
        log.debug('Prometheus Exporter: new job selected' + str(r))
        self.id = r


cc = CustomCollector()
REGISTRY.register(cc)


@restApi.route('/Forecasting')
@restApi.response(200, 'Success')
@restApi.response(404, 'Forecasting job not found')
@restApi.response(410, 'Forecasting job not started')
class _Forecasting(Resource):
    @restApi.doc(description="handling new forecasting requests")
    @restApi.expect(model, envelope='resource')
    # put method receives data as payload in json format
    def post(self):
        global active_jobs
        global data
        global reqs
        global ec

        scraping_period = 5
        request_data = request.get_json()
        log.info('Forecasting API: new job requested \n' + str(request_data))
        # input data in the payload in json format
        nsid = request_data['nsId']
        vnfdid = request_data['vnfdId']
        metricSO = request_data['performanceMetric']
        nsdid = request_data['nsdId']
        ilSO = request_data['IL']

        #easyfix for the il detection 
        il = ilmapper(ilSO)
        if "il_small" in ilSO:
            il = 1
        elif "il_big" in ilSO:
            il = 2

        # dynamic request_id creation
        # todo: development check with no mon platform
        if not devel:
            req_id = uuid.uuid1()
            #todo: fix for testing
            #req_id = "64189e60-6684-11ed-9f52-fa163e96b497"
        else:
            # static id (only for development purpose)
            req_id = "1aa0c8e6-c26e-11eb-a8ba-782b46c1eefd"

        reqs[str(req_id)] = {'nsId': nsid, 'vnfdId': vnfdid, 'IL': il, 'nsdId': nsdid, 'instance_name': "",
                             'performanceMetric': "", 'isActive': True, 'scraperJob': [],
                             'kafkaTopic': None, 'prometheusJob': None, 'model': None, 'metrics': {}}
        log.debug('Forecasting API: new forecasting job allocated with id ' + str(req_id))

        # create kafka topic and update reqs dict
        topic = ec.createKafkaTopic(nsid)
        if topic != 0:
            log.info('Forecasting API: topic ' + topic + ' created')
        else:
            if devel:
                topic = 'fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f_forecasting'
            else:
                log.info('Forecasting API: topic not created')
                topic = nsid+'_forecasting'
                #reqs[str(req_id)]['isActive'] = False
                #return "Kafka topic not created, aborting", 403

        reqs[str(req_id)]['kafkaTopic'] = topic
        metric = mconverter(metricSO)
        reqs[str(req_id)]['performanceMetric'] = metric
        if metric is None:
            return "Problem converting the metric", 403
        # create scraper job and update the reqs dict
        if "node_cpu_seconds_total" in metric:
            expression = metric + "{nsId=\"" + nsid + "\", vnfdId=\"" + vnfdid + "\", mode=\"idle\", forecasted=\"no\"}"
            #reqs[str(req_id)]['metrics'][('node_cpu_seconds_total', vnfdid)] = expression
            '''
            reqs[str(req_id)]['metrics'][('rtt_latency', 'dtdtvvnf')] = 'rtt_latency{nsId=\"' + nsid + '\", vnfdId=\"dtdtvvnf\"}'
            #reqs[str(req_id)]['metrics'][('upstream_latency', 'dtdtvvnf')] = 'upstream_latency{nsId=\"' + nsid + '\", vnfdId=\"dtdtvvnf\"}'
            #reqs[str(req_id)]['metrics'][('packet_lost','dtdtvvnf')] = 'packet_lost{nsId=\"' + nsid + '\", vnfdId=\"dtdtvvnf\"}'
            reqs[str(req_id)]['metrics'][('total_cmd_sent', 'dtdtvvnf')] = 'tottal_cmd_send{nsId=\"' + nsid + '\", vnfdId=\"dtdtvvnf\"}'
            reqs[str(req_id)]['metrics'][('total_cmd_lost', 'dtdtvvnf')] = 'tottal_cmd_lost{nsId=\"' + nsid + '\", vnfdId=\"dtdtvvnf\"}'
            '''
        elif "app_latency" in metric:
            '''
                app_latency example
                app_latency{exporter="applatencydt_exporter", forecasted="no", instance="dtdtvvnf-1",
                            instance_id="fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f-0-dtdtvvnf-1", 
                            job="e3cc978f-965c-4aa1-9189-50ad5719309f", nsId="fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f", 
                            robot_id="10.10.10.221", vnfdId="dtdtvvnf"}
                exporter = "app_latencydt_exporter", forecasted = "no", robot_id = "10.10.10.221", vnfdId = "dtdtvvnf"}
            '''
            expression = metric + "{nsId=\"" + nsid + "\", vnfdId=\"" + vnfdid + "\", forecasted=\"no\"}"
        elif "node_memory" in metric:
            '''
            node_memory_MemFree_bytes{nsId="fgt-a3b70e2-6471-4f78-9d04-96e6671401f4",vnfdId="dtcontrolvnf"}
            '''
            expression = metric + "{nsId=\"" + nsid + "\", vnfdId=\"" + vnfdid + "\", forecasted=\"no\"}"
            #to be activated to get total memory
            reqs[str(req_id)]['metrics'][('node_memory_MemTotal_bytes', 'dtcontrolvnf')] = "node_memory_MemTotal_bytes{nsId=\"" + nsid + "\", vnfdId=\"" + vnfdid + "\", forecasted=\"no\"}"
        else:
            expression = metric + "{nsId=\"" + nsid + "\", vnfdId=\"" + vnfdid + "\", forecasted=\"no\"}"
        #fix to avoid problem with scraper job already present
        already_working = False
        # todo: development check with no mon platform
        if not devel or not already_working:
            sId = ec.startScraperJob(nsid=nsid, topic=topic, vnfdid=vnfdid, metric=metric,
                                 expression=expression, period=scraping_period)
            reqs[str(req_id)]['scraperJob'].append(sId)
            if sId is not None:
                # print("scraper job "+ str(sId)+ " started")
                log.info('Forecasting API: scraper job ' + sId + ' created')
            else:
                ec.deleteKafkaTopic(topic)
                reqs[str(req_id)] = {'isActive': False}
                return "Scraper job not created aborting", 403

        #simple mapping
        if "DTPoC" in nsdid and metric == "node_cpu_seconds_total":
            model_forecasting = "lstmCPUEnhanced"
        if "DTPoC" in nsdid and metric == "node_memory_MemFree_bytes":
            model_forecasting = "convRAM"
        else:
            model_forecasting = "lstmCPUBase"

        reqs[str(req_id)]['model'] = model_forecasting
        log.debug('Forecasting API: Model selected ' + model_forecasting)

        #todo: to be veryfied: #automatic instance detection
        #instances = instancecheck(ec.createKafkaConsumer(req_id, topic), 30, log)
        #il = len(instances)

        #simple assumption that we start with 1 instance
        instances = [vnfdid+'-'+str(il)]
        log.info("Forecasting API: considered IL={}".format(str(il)))
        #start the scraper for the additional application metrics
        # todo: development check with no mon platform
        if not devel:
            for metricx, vnf in reqs[str(req_id)]['metrics'].keys():
                expr = reqs[str(req_id)]['metrics'][(metricx,vnf)]
                log.info('Forecasting API: metric='+metricx+' and vnf='+vnf)
                sId = ec.startScraperJob(nsid=nsid, topic=topic, vnfdid=vnf, metric=metricx,
                                             expression=expr, period=scraping_period)
                reqs[str(req_id)]['scraperJob'].append(sId)
                log.info('Forecasting API: scraper job lists='+str(reqs[str(req_id)]['scraperJob']))

        # single instance case
        if il == 1:
            log.debug('Forecasting API: Single instance detected')
            fj = ForecastingJob(req_id, nsdid, model_forecasting, metric, il, instances[0])
            log.debug('Forecasting API: forecasting job created ' + fj.str())
            steps_back = 130
            steps_forw = 1
            #modelName = 'trainedModels/lstmdiff'+str(steps_back)+'_'+str(steps_forw)+'.h5'
            #features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
            if model_forecasting == "lstmCPUEnhanced":
               modelName = 'trainedModels/lstm5sec.h5'
               features = ['r_a1', 'r_a2']
               main_feature = 'cpu0'
            elif model_forecasting == "convRAM":
               #modelName = 'trainedModels/convRAM_130_14.h5'
               steps_forw = 25
               modelName = "trainedModels/convRAM_{}_{}.h5".format(steps_back, steps_forw)
               features = ['r_a1', 'r_a2']
               main_feature = 'memory_free'
            else:
               features = ['r_a1', 'r_a2']
               main_feature = 'cpu0'
            fj.set_model(steps_back, steps_forw, True, modelName, save, features, main_feature)
            event = Event()
            t = Thread(target=fj.run, args=(event, ec.createKafkaConsumer(il, topic), False))
            t.start()
            active_jobs[str(req_id)] = {'thread': t, 'job': fj, 'kill_event': event, 'subJobs': {}}
            reqs[str(req_id)]['instance_name'] = instances[0]
        # in case of multiple instances
        '''
        # todo: to be verified in case of multiple attivation for the robot classification
        else:
            log.debug("Forecasting API: {} instances detected".format(str(il)))
            instances = []

            for i in range(1, il+1):
                instance = vnfdid + '-' + str(i)
                instances.append(instance)
                fj = ForecastingJob(req_id, nsdid, model_forecasting, metric, i, instance)
                steps_back = 150
                steps_forw = 1
                modelName = 'trainedModels/lstmdiff' + str(steps_back) + '_' + str(steps_forw) + '.h5'
                features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
                main_feature = 'cpu0'
                fj.set_model(steps_back, steps_forw, True, modelName, save, features, main_feature)
                event = Event()
                t = Thread(target=fj.run, args=(event, ec.createKafkaConsumer(i, topic), False))
                t.start()
                # main instance
                if i == 1:
                    log.debug('Forecasting API: Main forecasting job created ' + fj.str())
                    active_jobs[str(req_id)] = {'thread': t, 'job': fj, 'kill_event': event, 'subJobs': {}}
                else:
                    log.debug('Forecasting API: sub forecasting job created ' + fj.str())
                    active_jobs[str(req_id)]['subJobs'][instance] = {'thread': t, 'job': fj, 'kill_event': event}
                i = i + 1
        '''
        # create Prometheus job pointing to the exporter
        if not devel:
            pId = ec.startPrometheusJob(vnfdid, nsid, scraping_period, req_id)
            if pId is not None:
                # print("Prometheus job "+ str(pId)+ " started")
                log.info('Forecasting API: Prometheus job ' + pId + ' created')
            else:
                ec.deleteKafkaTopic(topic)
                ec.stopScraperJob(sId)
                reqs[str(req_id)] = {'isActive': False}
                return "Prometheus job not created aborting", 403

            # print("pj=\""+ str(pId)+ "\"")
            # print("sj=\""+ str(sId)+ "\"")
            reqs[str(req_id)]['prometheusJob'] = pId
            '''
            if model_forecasting == "convRAM":
                pId2 = ec.startPrometheusJob(vnfdid+"__tot", nsid, scraping_period, req_id)
                if pId2 is not None:
                   # print("Prometheus job "+ str(pId)+ " started")
                   log.info('Forecasting API: Prometheus job ' + pId2 + ' created')
                else:
                   log.info('Forecasting API: Error creating additional Prometheus job ')
                reqs[str(req_id)]['other_prometheusJob'] = pId2
            '''
        return str(req_id), 200

    @staticmethod
    def get():
        global reqs
        reply = list(reqs.keys())
        #print(reply)
        return json.dumps(reply), 200


@restApi.route('/Forecasting/<string:job_id>')
@restApi.response(200, 'Success')
@restApi.response(404, 'Forecasting job not found')
@restApi.response(410, 'Forecasting job not started')
class _ForecastingDeleter(Resource):
    # @restApi.doc(description="handling new forecasting requests")
    @staticmethod
    def delete(job_id):
        global active_jobs
        global reqs

        log.info('Forecasting API: request to stop forecasting job ' + job_id + ' received')
        if str(job_id) in active_jobs.keys():
            element = active_jobs[str(job_id)]
            thread = element.get('thread')
            event = element.get('kill_event')
            event.set()
            thread.join()
            #stop related sub_jobs
            if len(active_jobs[str(job_id)]['subJobs'].keys())> 0:
                for inst in active_jobs[str(job_id)]['subJobs'].keys():
                    sjob = active_jobs[str(job_id)]['subJobs'][inst]
                    thread = sjob.get('thread')
                    event = sjob.get('kill_event')
                    event.set()
                    thread.join()
            active_jobs.pop(str(job_id))
            pj = reqs[str(job_id)].get('prometheusJob')
            sjs = reqs[str(job_id)].get('scraperJob')

            if not devel:
                # delete Prometheus job pointing to the exporter
                ec.stopPrometheusJob(pj)
                log.info('Forecasting API: deleted Prometheus job')

                # delete scraper job and update the reqs model
                for sj in sjs:
                    ec.stopScraperJob(sj)
                    log.info('Forecasting API: deleted scraper job')

            # delete kafla topic and update reqs dict
            topic = reqs[str(job_id)].get('kafkaTopic')
            if topic is not None:
                ec.deleteKafkaTopic(topic)
            else:
                ec.deleteKafkaTopic(reqs[str(job_id)].get('nsId') + "_forecasting")
            log.info('Forecasting API: deleted kafka topic')
            if job_id in reqs.keys():
                reqs[str(job_id)] = {'isActive': False}
            return 'Forecasting job ' + job_id + ' Successfully stopped', 200
        else:
            return 'Forecasting job not found', 404

    @staticmethod
    def get(job_id):
        global active_jobs
        global reqs

        if job_id in reqs.keys():
            log.info('Forecasting API: GET job info, ' + str(reqs[str(job_id)]))
            return reqs[str(job_id)], 200
        else:
            log.info('Forecasting API: GET job info, job not found ' + job_id)
            return 'Forecasting job not found', 404


@restApi.route('/Forecasting/<string:job_id>/<string:ilv>')
@restApi.response(200, 'Success')
@restApi.response(404, 'not found')
class _ForecastingSetIL(Resource):
    @staticmethod
    def put(job_id, ilv):
        global active_jobs
        global reqs
        if str(job_id) in reqs.keys():
            oldIL = reqs[str(job_id)].get('IL')
            log.info("Forecasting API: {} instances detected".format(str(oldIL)))
            '''
                    reqs[str(req_id)] = {'nsId': nsid, 'vnfdId': vnfdid, 'IL': 0, 'nsdId': nsdid, 'instance_name': "",
                             'performanceMetric': None, 'isActive': True, 'scraperJob': [],
                             'kafkaTopic': None, 'prometheusJob': None, 'model': None, 'metrics': {} }
            '''
            #todo: check the value passed in case of scaling (+1 or absolute value?)
            ilval = ilmapper(ilv)
            il = 0
            if ilval == 1:
                il = oldIL - 1
            elif ilval == 2:
                il = oldIL + 1
            reqs[str(job_id)]['IL'] = il

            nsdid = reqs[str(job_id)]['nsdId']
            model_forecasting = reqs[str(job_id)]['model']
            metric = reqs[str(job_id)].get('performanceMetric')
            topic = reqs[str(job_id)]['kafkaTopic']

            vnfdid = reqs[str(job_id)]['vnfdId']
            '''
                        log.debug('Forecasting API: Single instance detected')
            fj = ForecastingJob(req_id, nsdid, model_forecasting, metric, il, instances[0])
            log.debug('Forecasting API: forecasting job created ' + fj.str())
            steps_back = 130
            steps_forw = 1
            #modelName = 'trainedModels/lstmdiff'+str(steps_back)+'_'+str(steps_forw)+'.h5'
            #features = ['avg_rtt_a1', 'avg_rtt_a2', 'avg_loss_a1', 'avg_loss_a2', 'r_a1', 'r_a2']
            if model_forecasting == "lstmCPUEnhanced":
               modelName = 'trainedModels/lstm5sec.h5'
               features = ['r_a1', 'r_a2']
               main_feature = 'cpu0'
            elif model_forecasting == "convRAM":
               #modelName = 'trainedModels/convRAM_30.h5'
               modelName = 'trainedModels/convRAM_130.h5'
               #steps_back = 150
               steps_back = 130
               features = ['r_a1', 'r_a2']
               #features = []
               main_feature = 'memory_free'
            else:
               features = ['r_a1', 'r_a2']
               main_feature = 'cpu0'
            fj.set_model(steps_back, steps_forw, True, modelName, save, features, main_feature)
            event = Event()
            t = Thread(target=fj.run, args=(event, ec.createKafkaConsumer(il, topic), False))
            t.start()
            active_jobs[str(req_id)] = {'thread': t, 'job': fj, 'kill_event': event, 'subJobs': {}}
            reqs[str(req_id)]['instance_name'] = instances[0]

            '''
            if oldIL < il:
                log.info("Scaling up the forecastng jobs for nsid {} and metric {}".format(nsdid, metric))
                instance = vnfdid + '-' + str(il)
                fj = ForecastingJob(job_id, nsdid, model_forecasting, metric, il, instance)
                steps_back = 130
                steps_forw = 1
                if model_forecasting == "lstmCPUEnhanced":
                    modelName = 'trainedModels/lstm5sec.h5'
                    features = ['r_a1', 'r_a2']
                    main_feature = 'cpu0'
                elif model_forecasting == "convRAM":
                    modelName = "trainedModels/convRAM_{}_{}.h5".format(steps_back, steps_forw)
                    #modelName = 'trainedModels/convRAM_130.h5'
                    steps_back = 130
                    features = ['r_a1', 'r_a2']
                    main_feature = 'memory_free'
                else:
                    features = ['r_a1', 'r_a2']
                    main_feature = 'cpu0'
                    steps_back = 10
                    steps_forw = 4
                log.info("Forecasting API: model preparation --- features={}, main_feature={}, model={}, steps_back={}".format(features,
                     main_feature, model_forecasting, steps_back))
                fj.set_model(steps_back, steps_forw, True, modelName, save, features, main_feature)
                
                event = Event()
                t = Thread(target=fj.run, args=(event, ec.createKafkaConsumer(il, topic), False))
                t.start()
                log.info('Forecasting API: sub forecasting job created ' + fj.str())

                # disabling the data acquisition from other jobs and get robots already configured
                # active_jobs[str(req_id)] = {'thread': t, 'job': fj, 'kill_event': event, 'subJobs': {}}
                #print(active_jobs[str(job_id)]['job'].get_robots())
                if model_forecasting == "lstmCPUEnhanced":
                    active_robs = []
                    active_robs = active_robs + active_jobs[str(job_id)]['job'].get_robots()
                    active_jobs[str(job_id)]['job'].set_update_robots(False)
                    log.debug("Stopping robot update for instance {} ".format(active_jobs[str(job_id)]['job'].instance_name))
                    log.debug("Scaling, active robots: {} ".format(active_robs))
                    for instance in active_jobs[str(job_id)]['subJobs'].keys():
                        active_robs = active_robs + active_jobs[str(job_id)]['subJobs'][instance]['job'].get_robots()
                        active_jobs[str(job_id)]['subJobs'][instance]['job'].set_update_robots(False)
                        log.debug("Stopping robot update for instance {} ".format(active_jobs[str(job_id)]['subJobs'][instance]['job'].instance_name))
                    log.debug("Scaling, active robots: {} ".format(active_robs))

                #adding the new subjob
                active_jobs[str(job_id)]['subJobs'][instance] = {'thread': t, 'job': fj, 'kill_event': event}
                if model_forecasting == "lstmCPUEnhanced":
                    fj.set_other_robots(active_robs)

            if oldIL > il:
                log.info('Forecasting API: new IL for job ' + job_id + ' is lower than the previous, discarding the change')
                return 'Instantiation level not updated', 200
                '''
                if len(active_jobs[str(job_id)]['subJobs'].keys()) > 0:
                    instanceold = vnfdid + '-' + str(oldIL)
                    instance = vnfdid + '-' + str(il)
                    sjob = active_jobs[str(job_id)]['subJobs'][instanceold]
                    thread = sjob.get('thread')
                    event = sjob.get('kill_event')
                    event.set()
                    thread.join()
                    if model_forecasting == "lstmCPUEnhanced" or model_forecasting == "convRAM":
                        del active_jobs[str(job_id)]['subJobs'][instanceold]
                        if instance in active_jobs[str(job_id)]['subJobs'].keys():
                            active_jobs[str(job_id)]['subJobs'][instance]['job'].set_update_robots(True)
                        else:
                            active_jobs[str(job_id)]['job'].set_update_robots(True)

                '''
            log.info('Forecasting API: IL for job ' + job_id + ' updated to value ' + str(il))
            return 'Instantiation level updated', 200
        else:
            log.info('Forecasting API: PUT IL, job not found ' + job_id)
            return 'Forecasting job not found', 404

@restApi.route('/robots/<string:nsid>/<string:r1>/<string:r2>')
@restApi.response(200, 'Success')
@restApi.response(404, 'Not found')
class _Robots(Resource):
    @restApi.doc(description="handling robots update messages")
    # def get(self, job_id, vnfd_id):
    def post(self, nsid, r1, r2):
        global active_jobs
        global reqs
        #log.info('Prometeheus Exporter: new metric request for nsid=' + nsid + ' and vnfdid=' + vnfd_id)

        is_exists = False
        job_id = None
        for key in reqs.keys():
            if str(reqs[str(key)].get('nsId')) == str(nsid):
                job_id = str(key)
                is_exists = True
                break
        if not is_exists:
            return 'Forecasting job not found', 404
        if str(job_id) in active_jobs.keys():
          if int(r1) == 0 and int(r2) == 0:
            if len(active_jobs[str(job_id)]['subJobs'].keys()) > 0:
              for inst in active_jobs[str(job_id)]['subJobs'].keys():
                sjob = active_jobs[str(job_id)]['subJobs'][inst]
                thread = sjob.get('thread')
                event = sjob.get('kill_event')
                event.set()
                thread.join()
            f = active_jobs[str(job_id)].get('job')
            f.set_robots(int(r1), int(r2))
            return 'System reset and subjobs stopped', 200
        else:
            return 'Job not found', 404
        if len(active_jobs[str(job_id)]['subJobs'].keys()) == 0:
            #if no sunjobs robots assigned to the main instance
            f = active_jobs[str(job_id)].get('job')
            f.set_robots(int(r1), int(r2))
        else:
            #if sunjobs robots assigned to the last instance
            f = active_jobs[str(job_id)].get('job')
            (mf_r1, mf_r2) = f.get_num_robots()
            #remove the robots of the main instance
            keys = list(active_jobs[str(job_id)]['subJobs'].keys())
            ur1 = int(r1) - mf_r1
            ur2 = int(r2) - mf_r2
            #and remove the robots assigned to the other sub instances
            if len(keys) > 1:
                for val_instance in range(0, len(keys)-1):
                    instance = keys[val_instance]
                    fx = active_jobs[str(job_id)]['subJobs'][instance].get('job')
                    (fx_r1, fx_r2) = fx.get_num_robots()
                    ur1 = ur1 - fx_r1
                    ur2 = ur2 - fx_r2
            instance = keys[len(keys)-1]
            sf = active_jobs[str(job_id)]['subJobs'][instance].get('job')
            sf.set_robots(int(ur1), int(ur2))
        
        return 'Robots updated', 200


# @prometheusApi.route('/metrics/<string:job_id>/<string:vnfd_id>')
@prometheusApi.route('/metrics/<string:nsid>/<string:vnfd_id>')
@prometheusApi.response(200, 'Success')
@prometheusApi.response(404, 'Not found')
class _PrometheusExporter(Resource):
    @prometheusApi.doc(description="handling Prometheus connections")
    # def get(self, job_id, vnfd_id):
    def get(self, nsid, vnfd_id):
        global data
        global active_jobs
        global reqs
        log.info('Prometeheus Exporter: new metric request for nsid=' + nsid + ' and vnfdid=' + vnfd_id)

        is_exists = False
        job_id = None
        for key in reqs.keys():
            if str(reqs[str(key)].get('nsId')) == str(nsid):
                if str(reqs[str(key)].get('vnfdId')) == str(vnfd_id):
                    job_id = str(key)
                    is_exists = True
                    break
        jobid = job_id
        if not is_exists:
            log.info("Prometeheus Exporter: nsid/vnfdid {}/{} not found ".format(nsid, vnfd_id))
            return 'Forecasting job not found', 404
        f = active_jobs[str(job_id)].get('job')
        # get forecasting value
        value = 0
        if f.get_model() == "Test":
            value = f.get_forecasting_value(None)
        elif f.get_model() == "lstmCPUBase":
            value = f.get_forecasting_value(5, 2)
        elif f.get_model() == "lstmCPUEnhanced":
            value = f.get_forecasting_value(10, 4)
        elif f.get_model() == "convRAM":
            metric2 = "node_memory_MemTotal_bytes"
            value = f.get_forecasting_value(10, 14)
            value2 = f.get_t0(metric2)
            log.debug("memTotal = {}".format(value2))
        metric = reqs[str(job_id)].get('performanceMetric')
        log.debug("metric = {}".format(metric))
        # creating replicas for the average data
        names = f.get_names()
        if "cpu" in metric or "CPU" in metric or "Cpu" in metric:
            log.debug("inside CPU names= {} ".format(names))
            for instance in names.keys():
                for c in range(0, len(names[instance]['cpus'])):
                    cpu = str(names[instance]['cpus'][c])
                    mode = str(names[instance]['modes'][c])
                    timestamp = str(names[instance]['timestamp'][c])
                    return_data = {
                        'job': job_id,
                        'metric': metric,
                        'name': instance,
                        'cpu': cpu,
                        'mode': mode,
                        'timestamp': round(float(timestamp), 2) + 15.0,
                        str(metric): value
                    }

                    return_data_str = json.dumps(return_data)
                    json_obj2 = json.loads(return_data_str)
                    if json_obj2['job'] not in data.keys():
                        data[jobid] = multiprocessing.Queue()
                    # print(return_data_str)
                    data[jobid].put(json_obj2)
                    # print("push")
                    # print(data[id].qsize())
        if "memory_MemFree" in metric:
            log.debug("inside RAM names= {} ".format(names))
            for instance in names.keys():
                return_data = {
                    'job': job_id,
                    'name': instance,
                    'metric': metric,
                    str(metric): value,
                    str(metric2): value2
                    }
                return_data_str = json.dumps(return_data)
                json_obj2 = json.loads(return_data_str)
                if json_obj2['job'] not in data.keys():
                    data[jobid] = multiprocessing.Queue()
                # print(return_data_str)
                data[jobid].put(json_obj2)

        
        #subjobs
        #todo check with ram
        if len(active_jobs[str(job_id)]['subJobs'].keys()) > 0:
            sfjs = active_jobs[str(job_id)]['subJobs']
            for instance in sfjs.keys():
                value = 0
                f1 = active_jobs[str(job_id)]['subJobs'][instance]['job']
                if f1.get_model() == "Test":
                    value = f.get_forecasting_value(None)
                elif f1.get_model() == "lstmCPUBase":
                    value = f.get_forecasting_value(5, 2)
                elif f1.get_model() == "lstmCPUEnhanced":
                    value = f.get_forecasting_value(10, 1)
                    log.info("5GrAPI: the fprecasting value is {}".format(value))
                elif f1.get_model() == "convRAM":
                    metric2 = "node_memory_MemTotal_bytes"
                    value = f1.get_forecasting_value(10, 4)
                    value2 = f1.get_t0(metric2)
                    log.debug("memTotal = {}".format(value2))

                metric = reqs[str(job_id)].get('performanceMetric')
                # creating replicas for the average data
                names = f1.get_names()    
                if "cpu" in metric or "CPU" in metric or "Cpu" in metric:
                    log.debug("inside CPU names= {} ".format(names))
                    for instancex in names.keys():
                        for c in range(0, len(names[instancex]['cpus'])):
                            cpu = str(names[instancex]['cpus'][c])
                            mode = str(names[instancex]['modes'][c])
                            timestamp = str(names[instancex]['timestamp'][c])
                            return_data = {
                                'job': job_id,
                                'metric': metric,
                                'name': instance,
                                'cpu': cpu,
                                'mode': mode,
                                'timestamp': round(float(timestamp), 2) + 15.0,
                                str(metric): value
                            }

                            return_data_str = json.dumps(return_data)
                            json_obj2 = json.loads(return_data_str)
                            if json_obj2['job'] not in data.keys():
                                data[jobid] = multiprocessing.Queue()
                            # print(return_data_str)
                            data[jobid].put(json_obj2)
                if "memory_MemFree" in metric:
                    log.debug("inside RAM names= {} ".format(names))
                    for instance in names.keys():
                        return_data = {
                        'job': job_id,
                        'name': instance,
                        'metric': metric,
                        str(metric): value,
                        str(metric2): value2
                            }
                        return_data_str = json.dumps(return_data)
                        json_obj2 = json.loads(return_data_str)
                        if json_obj2['job'] not in data.keys():
                           data[jobid] = multiprocessing.Queue()
                        # print(return_data_str)
                        data[jobid].put(json_obj2)
        time.sleep(0.1)
        cc.set_parameters(jobid)
        reply = generate_latest(REGISTRY)
        response = make_response(reply, 200)
        response.mimetype = "text/plain"
        log.info('Prometheus Exporter: response= ' + str(response))
        return response


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.conf')
    log.debug('Forecasting API: Configuration file parsed and read')

    # ec = ExternalConnections('config.conf', logging)
    ec = ExternalConnections('config.conf')
    log.debug('Forecasting API: External connection module initialized')
    if 'local' in config:
        ip = config['local']['localIP']
        port = config['local']['localPort']
        testForecasting = int(config['local']['testingEnabled'])
        devel = True if int(config['local']['development']) == 1 else False
        save = True if int(config['local']['save_dataset']) == 1 else False
        scraping_period = int(config['local']['scraping_period'])
    else:
        port = PORT
    if 'AIML' in config:
        aimlip = config['AIML']['aimlIP']
        aimlport = config['AIML']['aimlPort']
        aimlurl = config['AIML']['aimlUrl']
    else:
        port = PORT

    app.run(host='0.0.0.0', port=port)
    log.info('Forecasting API: API server started on port ' + str(port))
