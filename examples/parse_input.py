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
FREQ_ALL_CORES =[300000,576000 ,614400, 864000, 1075200 ,1363200, 1516800, 1651200 ,1804800,652800,  940800,  1152000,  1478400,  1728000,  1900800 , 2092800,  2208000, 806400,  1094400 , 1401600 , 1766400,  1996800 , 2188800,  2304000 , 2400000]

print 'parse argument start'
parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')
parser.add_argument('-pf', '--process file', dest='process_file',
                    help='Process file to parse')
args = parser.parse_args()
print 'parse argument end'

print 'parse trace start'
trace = Ftrace(args.file)
print 'parse trace end'


print 'cpu.task_intervals start'
input_interval = trace.android.input_events()
print input_interval
# irq = 'irq/287-touchpa'
letancy = trace.android.input_latencies(irq_name = 'irq/287-touchpa',interval=None)
print letancy
# task_tid_list = process_info.get_all_task_tid()
print 'cpu.task_intervals end'


print 'All done'