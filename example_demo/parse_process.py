import sys
import argparse
from pandas import DataFrame
import pandas as pd
import numpy as np
import time

class ProcessInfo:
    user = '0'
    pid = '0'
    tid = '0'
    process_name = '0'

processInfolist = []
tidList = []
result_list_tid = []
result_list_pid = []
result_list_process = []

class ProcessInfoParse:

  process_file = ''

  def parse_process_info(self,process_file):
    with open(process_file,'r') as df:
      for line in df:
        if line.count('\n') == len(line):
          continue
        
        processinfo = ProcessInfo()
        # user get start 
        index = line.find(' ')
        processinfo.user = line[0:index]
        # user get ned 

        # pid get start
        while(line[index]==' '):
          index+=1
        index_start = index

        while(line[index]!=' '):
          index +=1
        index_end = index
        processinfo.pid = line[index_start:index_end]
        # pid get end

        # tid get start
        while(line[index]==' '):
          index+=1
        index_start = index

        while(line[index]!=' '):
          index +=1
        index_end = index
        processinfo.tid = line[index_start:index_end]
        # tid get end

        # process_name get start
        while(line[index]==' '):
          index+=1
        processinfo.name = line[index:].strip()
        # tid get process_name    
        processInfolist.append(processinfo)
    
  def get_pid(self,tid):
    for processinfo in processInfolist:
      if processinfo.tid == str(tid):
        return processinfo.pid

  def get_taskname_by_tid(self , tid):
    for processinfo in processInfolist:
      if processinfo.tid == str(tid):
        return processinfo.name

  def get_taskname_by_pid(self , pid):
    for processinfo in processInfolist:
      if processinfo.tid == str(pid):
        return processinfo.name

  def get_all_task_tid(self):
    for processinfo in processInfolist:
      tidList.append(processinfo.tid)
    return tidList

  def get_pid_by_taskname(self, taskname):
    for processinfo in processInfolist:
      if processinfo.process_name == str(taskname):
        return processinfo.pid

  def save_running_info_to_tid_list(self , pid , tid , name , duration):
    # record tid
    if name is not None and result_list_tid is not None and pid is not None and tid is not None:
      for dic_result in result_list_tid:
        if dic_result['tid'] == tid:
          dic_result['duration']+= duration
          dic_result['name'] = name
          return
      dic_new = {'pid' : pid, 'tid' : tid ,'name': name , 'duration' : duration * 1000}
      result_list_tid.append(dic_new)

  def save_running_info_to_pid_list(self , pid , tid , process_name, task_name , duration):
    # record pid
    if task_name is not None and pid is not None and tid is not None:
      if result_list_tid is not None:
        for dic_result in result_list_pid:
          if dic_result['pid'] == pid:
            dic_result['duration'] += (duration * 1000)
            return
      dic_new = {}
      dic_new['pid'] = pid
      dic_new['name'] = process_name
      dic_new['duration'] = duration * 1000
      dic_new['percentage'] = '0'
      result_list_pid.append(dic_new)

  def get_process_running_info(self , pid , tid , process_name, task_name , duration):
    if task_name is not None and pid is not None and tid is not None:
      if result_list_process is not None:
        for dic_result in result_list_process:
          if dic_result['tid'] == tid:
            dic_result['duration'] += (duration * 1000)
            return
      dic_new = {}
      dic_new['pid'] = pid
      dic_new['tid'] = tid
      dic_new['process_name'] = process_name
      dic_new['task_name'] = task_name
      dic_new['duration'] = duration * 1000
      result_list_process.append(dic_new)

  def print_result_sort_by_tid(self):
    print '# cpu time by tid view #'
    for dic_tid in result_list_tid:
      print 'pid = ' + str(dic_tid['pid'])+ ' tid = ' + str(dic_tid['tid']) + '  name = ' + dic_tid['name'] + ' duration = ' + str(dic_tid['duration'])

  def print_result_sort_by_pid(self):
    print '# cpu time by pid view #'
    if result_list_pid is not None:
      # for dic_pid in result_list_pid:
      #   print 'pid = ' + dic_pid['pid']+ '  name = ' + dic_pid['name'] + ' duration = ' + dic_pid['duration']
      df = pd.DataFrame(result_list_pid, columns=['duration','pid','name'])
      df.sort_values("duration",inplace=True, ascending=False)

      now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time())) 
      fname= now+r"_result_sort_by_pid.csv"
      df.to_csv(fname,index=False)

  def print_result_sort_by_process(self):
    print '# cpu time by process view #'
    if result_list_process is not None:
      # for dic_pid in result_list_pid:
      #   print 'pid = ' + dic_pid['pid']+ '  name = ' + dic_pid['name'] + ' duration = ' + dic_pid['duration']
      df = pd.DataFrame(result_list_process, columns=['duration','pid','process_name','task_name','tid'])
      df.sort_values("duration",inplace=True , ascending=False)
      now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time())) 
      fname= now+r"_result_sort_by_process.csv"
      df.to_csv(fname,index=False)

  def print_result_sort_by_all(self):
    print '# cpu time by pid and tid view #'
    for dic_pid in result_list_pid:
      pid = dic_pid['pid']
      print 'pid = ' + str(dic_pid['pid'])+ '  name = ' + dic_pid['name'] + ' duration = ' + str(dic_pid['duration'])
      for dic_tid in result_list_tid:
        if dic_tid['pid'] == pid:
          print 'pid = ' + str(dic_tid['pid'])+ ' tid = ' + str(dic_tid['tid']) + '  name = ' + dic_tid['name'] + ' duration = ' + str(dic_tid['duration'])

  def get_total_running_time(self):
    total_time = 0
    if result_list_pid is not None:
      for result in result_list_pid:
        total_time += result['duration']
      return total_time

  def cal_percentage(self , total_time):
    if result_list_pid is not None:
      for result in result_list_pid:
        result['percentage'] = '{:.0%}'.format(result['duration'] / total_time)