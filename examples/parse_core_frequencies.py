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
task_tid = []

parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')
parser.add_argument('-pf', '--process file', dest='process_file',
                    help='Process file to parse')
args = parser.parse_args()

trace = Ftrace(args.file)
process_info = ProcessInfoParse()
process_info.parse_process_info(args.process_file)

task_interval = trace.cpu.task_intervals()
task_tid_list = process_info.get_all_task_tid()
print task_tid_list
for busy_interval_item in task_interval:
    for task_tid in task_tid_list:
        if busy_interval_item.task.pid == int(task_tid) and busy_interval_item.state == TaskState.RUNNING:
            pid = process_info.get_pid(task_tid)
            process_info.save_running_info_to_tid_list(pid,task_tid,busy_interval_item.task.name ,busy_interval_item.interval.duration)
            process_info.save_running_info_to_pid_list(pid,task_tid,busy_interval_item.task.name ,busy_interval_item.interval.duration)
            break

print "Total trace time = " + str(trace.duration)
process_info.print_result_sort_by_pid()
# process_info.print_result_sort_by_all()
# process_info.print_result_sort_by_tid()

