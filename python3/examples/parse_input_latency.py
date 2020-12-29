import argparse
import ftrace
from ftrace import Ftrace
from pandas import DataFrame
from ftrace.task import TaskState
from parse_process import ProcessInfoParse

LITTLE_CLUSTER_MASK = 0x0F
BIG_CLUSTER_MASK = 0xF0

LITTLE_CPUS = ftrace.common.unpack_bitmap(LITTLE_CLUSTER_MASK)
BIG_CPUS = ftrace.common.unpack_bitmap(BIG_CLUSTER_MASK)
ALL_CPUS = LITTLE_CPUS.union(BIG_CPUS)
FREQ_ALL_CORES = [300000, 576000, 614400, 864000, 1075200, 1363200, 1516800, 1651200, 1804800, 652800, 940800, 1152000,
                  1478400, 1728000, 1900800, 2092800, 2208000, 806400, 1094400, 1401600, 1766400, 1996800, 2188800,
                  2304000, 2400000]

print('parse argument start')
parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')

args = parser.parse_args()
print('parse argument end')

print('parse trace start')
trace = Ftrace(args.file)
print('parse trace end')

print('trace.android.input_latencies start')
irq_name_oppo = 'irq/287-touchpa'
irq_name_huawei = 'irq/189-thp'
letancy = trace.android.input_latencies(irq_name=irq_name_huawei, interval=None)
for item in letancy:
    print('Letency(ms) = ' + str(item.interval.duration * 1000)[0:6] + ' Irq start time = ' + str(item.interval.start)[
                                                                                              0:6] + 'Frame display ' \
                                                                                                     'time = ' + str(
        item.interval.end)[0:6])
# task_tid_list = process_info.get_all_task_tid()
print('trace.android.input_latencies end')

print('All done')
