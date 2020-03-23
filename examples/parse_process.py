import sys
import argparse
from pandas import DataFrame
import pandas as pd

class ProcessInfo:
    user = ''
    pid = ''
    tid = ''
    process_name = ''

processInfolist = []
tidList = []
dic = {}
result_list_tid = []
result_list_pid = []

class ProcessInfoParse:

  process_file = ''

  def parse_process_info(self,process_file):
    with open(process_file,'r') as df:
      for line in df:
        if line.count('\n') == len(line):
          continue
        
        processInfo = ProcessInfo()

        # user get start 
        index = line.find(' ')
        processInfo.user = line[0:index]
        # user get ned 

        # pid get start
        while(line[index]==' '):
          index+=1
        index_start = index

        while(line[index]!=' '):
          index +=1
        index_end = index
        processInfo.pid =  line[index_start:index_end]
        # pid get end

        # tid get start
        while(line[index]==' '):
          index+=1
        index_start = index

        while(line[index]!=' '):
          index +=1
        index_end = index
        processInfo.tid =  line[index_start:index_end]
        # tid get end

        # process_name get start
        while(line[index]==' '):
          index+=1
        processInfo.process_name = line[index:]

        # tid get process_name    
        processInfolist.append(processInfo)
    return processInfolist
    
  def get_pid(self,tid):
    for processInfos in processInfolist:
      if(processInfos.tid == tid):
        return processInfos.pid

  def get_all_task_tid(self):
    for processInfos in processInfolist:
      tidList.append(processInfos.tid)
    return tidList

  def get_taskname_by_tid(self , tid):
    for processInfos in processInfolist:
      if processInfos.tid == tid:
        return processInfos.process_name

  def save_running_info_to_tid_list(self , pid , tid , name , duration):
    # record tid
    if result_list_tid is not None:
      for dic in result_list_tid:
        if dic['tid'] == tid:
          dic['duration']+= duration
          dic['name'] = name
          return
    dics = {'pid' : pid, 'tid' : tid ,'name': name , 'duration' : duration * 1000}
    result_list_tid.append(dics)

  def save_running_info_to_pid_list(self , pid , tid , name , duration):
    # record pid
    if result_list_pid is not None:
      for dic in result_list_pid:
        if tid == pid:
          dic['duration'] += duration
          return
    
    #pid_name = self.get_taskname_by_tid(tid)
    dic_pid = {'pid' : pid,'name': name , 'duration' : duration * 1000}
    result_list_pid.append(dic_pid)

  def print_result_sort_by_tid(self):
    print '# cpu time by tid view #'
    for dic_tid in result_list_tid:
      print 'pid = ' + str(dic_tid['pid'])+ ' tid = ' + str(dic_tid['tid']) + '  name = ' + dic_tid['name'] + ' duration = ' + str(dic_tid['duration'])

  def print_result_sort_by_pid(self):
    print '# cpu time by pid view #'
    # for dic_pid in result_list_pid:
    #   pid = dic_pid['pid']
      # print 'pid = ' + str(dic_pid['pid'])+ '  name = ' + dic_pid['name'] + ' duration = ' + str(dic_pid['duration']* 1000)
    df = pd.DataFrame(result_list_pid, columns=['name','pid','duration'])
    df.to_csv("lock_to_launcher_2020_3_23_15.csv")

  def print_result_sort_by_all(self):
    print '# cpu time by pid and tid view #'
    for dic_pid in result_list_pid:
      pid = dic_pid['pid']
      print 'pid = ' + str(dic_pid['pid'])+ '  name = ' + dic_pid['name'] + ' duration = ' + str(dic_pid['duration'])
      for dic_tid in result_list_tid:
        if dic_tid['pid'] == pid:
          print 'pid = ' + str(dic_tid['pid'])+ ' tid = ' + str(dic_tid['tid']) + '  name = ' + dic_tid['name'] + ' duration = ' + str(dic_tid['duration'])