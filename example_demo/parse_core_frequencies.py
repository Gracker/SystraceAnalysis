import argparse
import ftrace
from ftrace import Ftrace
from pandas import DataFrame
from ftrace.task import TaskState
from parse_process import ProcessInfoParse
import time
import numpy as np

LITTLE_CLUSTER_MASK = 0x0F
BIG_CLUSTER_MASK = 0xF0

LITTLE_CPUS = ftrace.common.unpack_bitmap(LITTLE_CLUSTER_MASK)
BIG_CPUS = ftrace.common.unpack_bitmap(BIG_CLUSTER_MASK)
ALL_CPUS = LITTLE_CPUS.union(BIG_CPUS)
FREQ_ALL_CORES=[]

print 'parse argument start'
parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')
parser.add_argument('-pf', '--process file', dest='process_file',
                    help='Process file to parse')
parser.add_argument('-pid', '--process pid', dest='process_pid',
                    help='Process pid')          
parser.add_argument('-pn', '--process name', dest='process_name',
                    help='Process name')   
args = parser.parse_args()
print 'parse argument end'

print 'parse trace start'
trace = Ftrace(args.file)
print 'parse trace end'

print 'parse process info start'
process_info = ProcessInfoParse()
process_info.parse_process_info(args.process_file)
print 'parse process info end'

print 'cpu.task_intervals start'
task_interval = trace.cpu.task_intervals()
# task_tid_list = process_info.get_all_task_tid()
print 'cpu.task_intervals end'

print 'main parse start'
for busy_interval_item in task_interval:
    if busy_interval_item.state == TaskState.RUNNING:
        task_tid = busy_interval_item.task.pid
        if task_tid != 0:
            task_pid = process_info.get_pid(task_tid)
            task_name = process_info.get_taskname_by_tid(task_tid)
            process_name = process_info.get_taskname_by_pid(task_pid)
            process_info.save_running_info_to_pid_list(task_pid ,task_tid , process_name,task_name , busy_interval_item.interval.duration)
total_time = process_info.get_total_running_time()
print 'Total running time = ' + str(total_time)
process_info.cal_percentage(total_time)
process_info.print_result_sort_by_pid()
# process_info.print_result_sort_by_process()
print 'main parse end'

if args.process_pid is not None:
    print 'target process parse by process pid start'
    target_pid = args.process_pid  # input your target process id
    process_name = None
    for busy_interval_item in task_interval:
        # print busy_interval_item
        if busy_interval_item.state == TaskState.RUNNING:
            task_tid = busy_interval_item.task.pid
            if task_tid != 0:
                task_pid = process_info.get_pid(task_tid)
                if task_pid == target_pid:
                    task_name = process_info.get_taskname_by_tid(task_tid)
                    if process_name is None:
                        process_name = process_info.get_taskname_by_pid(task_pid)
                    process_info.get_process_running_info(task_pid ,task_tid , process_name,task_name , busy_interval_item.interval.duration)
    process_info.print_result_sort_by_process()
    print 'target process parse by process pid end'

if args.process_name is not None:
    print 'target process parse by process name start'
    target_process_name = args.process_name
    target_pid = process_info.get_pid_by_taskname(target_process_name)
    print 'target_pid : ' + str(target_pid)
    if target_pid is not None:
        for busy_interval_item in task_interval:
            # print busy_interval_item
            if busy_interval_item.state == TaskState.RUNNING:
                task_tid = busy_interval_item.task.pid
                if task_tid != 0:
                    task_pid = process_info.get_pid(task_tid)
                    if task_pid == target_pid:
                        task_name = process_info.get_taskname_by_tid(task_tid)
                        if process_name is None:
                            process_name = process_info.get_taskname_by_pid(task_pid)
                        process_info.get_process_running_info(task_pid ,task_tid , process_name,task_name , busy_interval_item.interval.duration)
        process_info.print_result_sort_by_process()
    print 'target process parse by process name end'
# print "Total trace time = " + str(trace.duration)

# process_info.print_result_sort_by_all()
# process_info.print_result_sort_by_tid()

print 'freq level parse start'
for cpu in ALL_CPUS:
    for busy_interval in trace.cpu.busy_intervals(cpu=cpu):
        for freq in trace.cpu.frequency_intervals(cpu=cpu, interval=busy_interval.interval):
            if freq.frequency not in FREQ_ALL_CORES:
                FREQ_ALL_CORES.append(freq.frequency)
FREQ_ALL_CORES.sort()
print FREQ_ALL_CORES
print 'freq level parse end'

print 'freq parse start'
df_freq = DataFrame( index = ALL_CPUS, columns=FREQ_ALL_CORES)
df_freq.fillna(0, inplace=True)
for cpu in ALL_CPUS:
    for busy_interval in trace.cpu.busy_intervals(cpu=cpu):
        # print busy_interval
        for freq in trace.cpu.frequency_intervals(cpu=cpu, interval=busy_interval.interval):
            # print freq
            df_freq.loc[cpu, freq.frequency] += freq.interval.duration
print df_freq.to_string()

now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time())) 
fname= now + r"_cpu_frequency_intervals.csv"
df_freq.to_csv(fname,index=False)
# df_freq.to_csv("lock_to_launcher_2020_3_23_freq.csv")
print 'freq parse end'

print 'All done'