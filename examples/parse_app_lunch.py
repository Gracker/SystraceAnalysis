import argparse
import ftrace
from ftrace import Ftrace
from pandas import DataFrame
from ftrace.task import TaskState


print 'parse argument start'
parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')
args = parser.parse_args()
print 'parse argument end'

print 'parse trace start'
trace = Ftrace(args.file)
print 'parse trace end'

lunch_info = trace.android.app_launch_latencies(task='com.androidperformance.inputmonitorexample')

print lunch_info