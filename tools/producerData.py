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

# python imports

from confluent_kafka import Producer
import sys
import time
kafkaIP = "10.5.0.3"
kafkaPort = 9092

topic = "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f_forecasting"
#topic = "Test"
conf = {'bootstrap.servers': kafkaIP + ":" + str(kafkaPort)}

N1 = 10
N2 = 0
m_id = 0

p = Producer(**conf)

message = {}
# Producer configuration
message[0] = """
[
    {
        "metric": {
            "__name__": "node_cpu_seconds_total",
            "cpu": "0",
            "exporter": "node_exporter",
            "instance": "dtcontrolvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "mode": "idle",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtcontrolvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "rtt_latency",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_sent",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_lost",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    }
]
"""

message[1] = """
[
    {
        "metric": {
            "__name__": "node_cpu_seconds_total",
            "cpu": "0",
            "exporter": "node_exporter",
            "instance": "dtcontrolvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "mode": "idle",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtcontrolvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    }
]
"""

message[2] = """
[
        {
        "metric": {
            "__name__": "node_cpu_seconds_total",
            "cpu": "0",
            "exporter": "node_exporter",
            "instance": "dtcontrolvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "mode": "idle",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtcontrolvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "rtt_latency",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_sent",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_lost",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "node_cpu_seconds_total",
            "cpu": "0",
            "exporter": "node_exporter",
            "instance": "dtcontrolvnf-2",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "mode": "idle",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtcontrolvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "rtt_latency",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_sent",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_lost",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    }
]
"""

message[3] = """
[
    {
        "metric": {
            "__name__": "node_cpu_seconds_total",
            "cpu": "0",
            "exporter": "node_exporter",
            "instance": "dtcontrolvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "mode": "idle",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtcontrolvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "rtt_latency",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "total_cmd_sent",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
   },
   {
        "metric": {
            "__name__": "total_cmd_lost",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.76",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
    {
        "metric": {
            "__name__": "rtt_latency",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    },
   {
        "metric": {
            "__name__": "total_cmd_sent",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
   },
   {
        "metric": {
            "__name__": "total_cmd_lost",
            "exporter": "node_exporter",
            "instance": "dtdtvvnf-1",
            "job": "58d10e62-bdf5-44a9-9b35-0ba4ddd14b74",
            "robot_id": "10.10.10.77",
            "nsId": "fgt-6e44566-121b-4b8a-ba59-7cd0be562d4f",
            "vnfdId": "dtdtvvnf",
            "forecasted": "no"
        },
        "value": [
            %.2f,
            "%s"
        ],
        "type_message": "metric"
    }
]
"""



def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d] @ %d\n' %
                         (msg.topic(), msg.partition(), msg.offset()))


row = {}
row[0] = "1639561743.65;1230659.12;219.3;0.0;219.3;1.24;0.0;0.0;0.0;1;0;1"
row[1] = "1639561758.65;1230674.94;219.3;0.0;219.3;1.34;0.0;0.0;0.0;1;0;1"
row[2] = "1639561773.65;1230688.9;219.3;0.0;219.3;1.71;0.0;0.0;0.0;1;0;1"
row[3] = "1639561788.66;1230702.9;219.3;0.0;219.3;1.34;0.0;0.0;0.0;1;0;1"
row[4] = "1639561803.66;1230716.85;219.2;0.0;219.2;0.98;0.0;0.0;0.0;1;0;1"
row[5] = "1639561818.66;1230730.85;219.3;0.0;219.3;1.27;0.0;0.0;0.0;1;0;1"
row[6] = "1639561833.66;1230744.85;218.4;0.0;218.4;1.34;0.0;0.0;0.0;1;0;1"
row[7] = "1639561788.66;1230758.84;219.7;0.0;219.7;1.3;0.0;0.0;0.0;1;0;1"
row[8] = "1639561863.66;1230772.82;218.0;0.0;218.0;1.28;0.0;0.0;0.0;1;0;1"
row[9] = "1639561878.66;1230786.84;218.4;0.0;218.4;1.19;0.0;0.0;0.0;1;0;1"
row[10] = "1639561893.66;1230800.77;219.3;0.0;219.3;1.3;0.0;0.0;0.0;1;0;1"
row[11] = "1639561908.66;1230814.72;219.3;0.0;219.3;1.28;0.0;0.0;0.0;1;0;1"
row[12] = "1639561923.66;1230828.68;217.6;0.0;217.6;1.3;0.0;0.0;0.0;1;0;1"
row[13] = "1639561938.66;1230842.67;219.3;0.0;219.3;1.3;0.0;0.0;0.0;1;0;1"
row[14] = "1639561953.66;1230856.65;219.3;0.0;219.3;1.38;0.0;0.0;0.0;1;0;1"
row[15] = "1639561968.66;1230870.63;219.3;0.0;219.3;1.38;0.0;0.0;0.0;1;0;1"
row[16] = "1639561983.66;1230884.61;218.4;0.0;218.4;1.4;0.0;0.0;0.0;1;0;12"
row[17] = "1639561998.66;1230898.59;219.6;0.0;219.6;1.47;0.0;0.0;0.0;1;0;1"
row[18] = "1639562013.66;1230912.55;218.5;0.0;218.5;1.39;0.0;0.0;0.0;1;0;1"
row[19] = "1639562028.66;1230917.72;218.4;0.0;218.4;1.38;0.0;0.0;0.0;1;0;1"

for i in range(0, N1):
    a = row[i].split(';')
    print(a)
    t = a[0]
    cpu = a[1]
    rtt = a[2]
    mess = ""
    if m_id == 0:
        mess = message[m_id] % (float(t), cpu, float(t), rtt, float(t), "10", float(t), "0")
    elif m_id == 1:
        mess = message[m_id] % (float(t), cpu)

    p.produce(topic, value=mess, callback=delivery_callback)
    p.flush()

    p.poll(1)
    print(mess)

    time.sleep(2)


for i in range(0, N2):
    a = row[i].split(';')
    print(a)
    t = a[0]
    cpu = a[1]
    rtt = a[2]
    if m_id == 2:
        mess = message[m_id] % (float(t), cpu, float(t), rtt, float(t), "10", float(t), "0", float(t), cpu, float(t), rtt, float(t), "10", float(t), "0")
    if m_id == 3:
        mess = message[m_id] % (
        float(t), cpu, float(t), rtt, float(t), "10", float(t), "0", float(t), rtt, float(t), "10",
        float(t), "0")

    p.produce(topic, value=mess, callback=delivery_callback)
    p.flush()

    p.poll(1)

    print(mess)
    time.sleep(0.5)
