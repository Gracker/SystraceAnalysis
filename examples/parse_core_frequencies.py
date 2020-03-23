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
print 'parse process info start'
process_info = ProcessInfoParse()
lsit = process_info.parse_process_info(args.process_file)
task_tid_list = process_info.get_all_task_tid()
print 'parse process info end'

print 'cpu.task_intervals start'
task_interval = trace.cpu.task_intervals()
task_tid_list = process_info.get_all_task_tid()
print 'cpu.task_intervals end'

print 'main parse start'
for busy_interval_item in task_interval:
    if busy_interval_item.state == TaskState.RUNNING:
        task_tid = busy_interval_item.task.pid
        task_pid = process_info.get_pid(task_tid)
        task_name = process_info.get_taskname_by_tid(task_tid)
        process_info.save_running_info_to_pid_list(task_pid,task_tid,task_name ,busy_interval_item.interval.duration)
print 'main parse end'
    # for task_tid in task_tid_list:
    #     if busy_interval_item.task.pid == int(task_tid) and busy_interval_item.state == TaskState.RUNNING:
    #         pid = process_info.get_pid(task_tid)
    #         # process_info.save_running_info_to_tid_list(pid,task_tid,busy_interval_item.task.name ,busy_interval_item.interval.duration)
    #         process_info.save_running_info_to_pid_list(pid,task_tid,busy_interval_item.task.name ,busy_interval_item.interval.duration)
    #         break

print "Total trace time = " + str(trace.duration)
process_info.print_result_sort_by_pid()
# process_info.print_result_sort_by_all()
# process_info.print_result_sort_by_tid()

print 'freq parse start'
df_freq = DataFrame( index = ALL_CPUS, columns=FREQ_ALL_CORES)
df_freq.fillna(0, inplace=True)
for cpu in ALL_CPUS:
    for busy_interval in trace.cpu.busy_intervals(cpu=cpu):
        for freq in trace.cpu.frequency_intervals(cpu=cpu, interval=busy_interval.interval):
            df_freq.loc[cpu, freq.frequency] += freq.interval.duration

print df_freq.to_string()
df_freq.to_csv("lock_to_launcher_2020_3_23_freq.csv")
print 'freq parse end'

print 'All done'