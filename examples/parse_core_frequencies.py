import argparse
import ftrace
from ftrace import Ftrace
from pandas import DataFrame

LITTLE_CLUSTER_MASK = 0x0F
BIG_CLUSTER_MASK = 0xF0

LITTLE_CPUS = ftrace.common.unpack_bitmap(LITTLE_CLUSTER_MASK)
BIG_CPUS = ftrace.common.unpack_bitmap(BIG_CLUSTER_MASK)
ALL_CPUS = LITTLE_CPUS.union(BIG_CPUS)
FREQ_ALL_CORES =[576000, 614400,806400,864000, 940800,1075200,1094400,1152000 ,1363200,1401600,1478400,1516800,1651200,1728000, 1766400 ,1804800, 1900800,1996800,2188800,2208000,  2400000 ]

parser = argparse.ArgumentParser(description='Per-core frequencies')

parser.add_argument('-f', '--file', dest='file',
                    help='File to parse')

args = parser.parse_args()

trace = Ftrace(args.file)

df_freq = DataFrame( index = ALL_CPUS, columns=FREQ_ALL_CORES)
df_freq.fillna(0, inplace=True)
for cpu in ALL_CPUS:
    for busy_interval in trace.cpu.busy_intervals(cpu=cpu):
        for freq in trace.cpu.frequency_intervals(cpu=cpu, interval=busy_interval.interval):
            df_freq.loc[cpu, freq.frequency] += freq.interval.duration
print df_freq