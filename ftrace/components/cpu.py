#!/usr/bin/python

# Copyright 2015 Huawei Devices USA Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Authors:
#       Chuk Orakwue <chuk.orakwue@huawei.com>

try:
    from logbook import Logger
except ImportError:
    from logging import Logger
from collections import defaultdict, namedtuple
from ftrace.interval import Interval, IntervalList
from ftrace.event import EventList
from ftrace.task import Task, TaskState
from ftrace.ftrace import register_api, FTraceComponent
from ftrace.composites import sorted_items
from ftrace.common import ConstantBase, FtraceError
from ftrace.utils.decorators import requires, memoize

log = Logger('CPU')

# Used to track interval when task is in/out of run-queue & its state.
TaskInterval = namedtuple('TaskInterval', ['task', 'cpu', 'interval', 'state'])
# Used to track state changes (BUSY|IDLE) for cpu
StateChange = namedtuple('StateChange', ['cpu', 'timestamp', 'state'])
# Used to track intervals when N cpus are concurrently active
SimBusyInterval = namedtuple('SimBusyInterval', ['cpus', 'interval'])
# Used to track run-queue depth changes per cpu
RunQueueChange = namedtuple('RunQueueChange', ['cpu', 'runnable', 'running', 'timestamp'])
RunQueueInterval = namedtuple('RunQueueInterval', ['cpu', 'runnable', 'running', 'interval'])
# Track CPU frequency
FreqInterval = namedtuple('FreqInterval', ['cpu', 'frequency', 'interval'])
# Track Idle state
IdleInterval = namedtuple('IdleInterval', ['cpu', 'state', 'interval'])

class BusyState(ConstantBase):
    BUSY = ()
    IDLE = ()
    UNKNOWN = ()

@register_api('cpu')
class CPU(FTraceComponent):
    """
    Class with APIs to process all CPU related events such as:
        - number of simultaneously active cores [x]
        - active time for each cpu (filterable by task) [x]
        - frequency residencies

    todo: Additional support for HMP platforms [homework] -- b.L comp analysis
    """
    def __init__(self, trace):
        self._trace = trace
        self._events = trace.events

    def _initialize(self):
        """
        """
        self._parse_rq_events()
        self._parse_freq_events()
        self._parse_cpu_idle_events()

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def seen_tasks(self, cpu=None):
        """Return iterable (list or set) of all tasks seen"""
        if cpu is not None:
            return self._tasks_by_cpu[cpu]

        tasks = set()
        for _per_cpu_tasks in self._tasks_by_cpu.itervalues():
            tasks = tasks.union(set(_per_cpu_tasks))
        return tasks

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def idle_time(self, cpu, interval=None):
        """Return Idle time for specified cpu [including in LPM state]"""
        duration = interval.duration if interval else self._trace.duration
        return duration - self.busy_time(cpu=cpu, interval=interval)

    @requires('cpu_idle')
    @memoize
    def lpm_time(self, cpu, interval=None):
        """Return time for specified cpu when in LPM.
        This is an approximation as we can exit LPM if CPU was in LPM
        for long time after tracing began.
        """
        try:
            lpm_intervals = self.lpm_intervals(cpu=cpu, interval=interval)
            return lpm_intervals.duration
        except KeyError:
            return 0.0
        except:
            # could be busy or idle entire time.
            return float('nan')

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def task_time(self, task, cpu=None, interval=None):
        """Returns time for specified task for given cpu/interval (if any)"""
        try:
            task_intervals = self.task_intervals(cpu=cpu, task=task, interval=interval)
            return task_intervals.duration
        except KeyError:
            return 0.0
        except:
            return float('nan')

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def busy_time(self, cpu, interval=None):
        """Return Idle time for specified cpu when its not offline.
        todo: filter by task
        """
        try:
            busy_intervals = self.busy_intervals(cpu=cpu, interval=interval)
            return sum(ti.interval.duration for ti in busy_intervals)
        except KeyError:
            return 0.0
        except:
            # could be busy or idle entire time.
            return float('nan')

    @requires('sched_switch', 'sched_wakeup')
    def simultaneously_busy_time(self, num_cores, cpus=None, interval=None):
        """Returns total time when `num_cores` in `cpus` are busy"""
        filter_func = lambda sbi: len(sbi.cpus.intersection(cpus)) == num_cores \
            if cpus else len(sbi.cpus) == num_cores
        iterable = filter(filter_func, self.simultaneously_busy_intervals(interval=interval))
        return sum(it.interval.duration for it in iterable)

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def runqueue_depth_time(self, cpu, rq_depth, interval=None):
        """Returns total time when rq_depth is `rq_depth`"""
        filter_func = lambda rqi: rqi.runnable == rq_depth
        iterable = filter(filter_func, self.runqueue_depth_intervals(cpu=cpu, interval=interval))
        return sum(it.interval.duration for it in iterable)

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def idle_intervals(self, cpu=None, interval=None):
        """Return Idle interval for specified cpu & interval
        when CPU is active before entering LPM state i.e. idle loop

        IMPORTANT: This does not included time in LPM states.
        For that, see `trace.cpu.lpm_intervals()`
        """
        if cpu is not None:
            intervals = self._task_intervals_by_cpu[cpu]
        else:
            intervals = IntervalList(sorted_items(self._task_intervals_by_cpu.values()))

        try:
            return IntervalList(filter(lambda ti: ti.task.pid==0,
                                       intervals.slice(interval=interval)))
        except:
            return IntervalList()


    @requires('cpu_idle')
    @memoize
    def lpm_intervals(self, cpu, interval=None):
        """Return lpm interval for specified cpu & interval
        when CPU is in LPM state.
        """
        try:
            self._cpu_idle_intervals_by_cpu.keys()
        except AttributeError:
            _ = self._cpu_idle_events_handler()

        if cpu is not None:
            intervals = self._cpu_idle_intervals_by_cpu[cpu]
        else:
            intervals = IntervalList(sorted_items(self._cpu_idle_intervals_by_cpu.values()))

        return IntervalList(intervals.slice(interval=interval))

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def simultaneously_busy_intervals(self, interval=None):
        """Returns IntervalList with for simultaneously busy cores"""
        try:
            return self._sim_busy_intervals.slice(interval=interval)
        except AttributeError:
            return IntervalList(self._sim_busy_interval_handler().slice(interval=interval))

    @requires('cpu_frequency')
    @memoize
    def frequency_intervals(self, cpu, interval=None):
        """Returns freq intervals for specified task on cpu"""
        try:
            return IntervalList(self._freq_intervals_by_cpu[cpu].slice(interval=interval))
        except AttributeError:
            return IntervalList(self._freq_events_handler()[cpu].slice(interval=interval))

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def busy_intervals(self, cpu, task=None, interval=None):
        """Returns busy intervals for specified task (if any) on cpu (if any)
        over the specified interval (if any) when TaskState = RUNNING
        i.e. running or runnable
        """
        task_intervals = self.task_intervals(cpu=cpu, task=task, interval=interval)
        if task is None: # any non-idle task
            filter_func = lambda ti: ti.task.pid != 0 and ti.state is TaskState.RUNNING
        else:
            filter_func = lambda ti: ti.state is TaskState.RUNNING

        return IntervalList(filter(filter_func, task_intervals))

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def task_intervals(self, cpu=None, task=None, interval=None):
        """Returns task intervals for specified task (if any) on cpu (if any)
        over the specified interval (if any).
        TODO: filter by task_state
        """
        try:
            if cpu is not None:
                intervals = self._task_intervals_by_cpu[cpu]
            else:
                intervals = IntervalList(
                                sorted_items(
                                    self._task_intervals_by_cpu.values()))

            filter_func = (lambda ti: ti.task == task) if task else None
            return IntervalList(filter(filter_func,
                                       intervals.slice(interval=interval)))
        except Exception, e:
            raise FtraceError(msg=e.message)

    @requires('sched_switch', 'sched_wakeup')
    @memoize
    def runqueue_depth_intervals(self, cpu, interval=None):
        """
        Returns interval of RQ-depth by CPU.
        IMPORTANT: This is a rough estimate of RQ-depth per core. If CPUs were
        heavily busy prior to trace collection, then this will be less accurate!
        """
        try:
            return self._rq_intervals_by_cpu[cpu].slice(interval=interval)
        except AttributeError:
            return self._rq_interval_handler()[cpu].slice(interval=interval)

    def _rq_interval_handler(self):
        """Handler function for rq-depth"""

        def rq_gen(cpu):
            for rq_a, rq_b in zip(self._rq_events_by_cpu[cpu], self._rq_events_by_cpu[cpu][1:]):
                interval = Interval(rq_a.timestamp, rq_b.timestamp)
                rq_interval = RunQueueInterval(cpu=cpu,
                                               runnable=rq_a.runnable,
                                               running=rq_a.running,
                                               interval=interval,
                                              )
                yield rq_interval
            # let's get some closure.
            if self._rq_events_by_cpu[cpu]:
                yield RunQueueInterval(cpu=cpu,
                                       runnable=rq_b.runnable,
                                       running=rq_b.running,
                                       interval=Interval(rq_b.timestamp, self._trace.duration),
                                      )
        self._rq_intervals_by_cpu = defaultdict(IntervalList)

        for cpu in self._trace.seen_cpus:
            for rq_interval in rq_gen(cpu):
                self._rq_intervals_by_cpu[cpu].append(rq_interval)

        return self._rq_intervals_by_cpu

    def _freq_events_handler(self):
        """Handler function for CPU frequency events"""
        self._freq_intervals_by_cpu = defaultdict(IntervalList)
        if not 'cpu_frequency_switch_start' in self.freq_tracepoints:
            for cpu, events in self._freq_events_by_cpu.iteritems():
                for freq_a, freq_b in zip(events, events[1:]):
                    interval = Interval(freq_a.timestamp, freq_b.timestamp)
                    freq_interval = FreqInterval(cpu=cpu,
                                               frequency=freq_a.data.state,
                                               interval=interval,
                                               )
                    self._freq_intervals_by_cpu[cpu].append(freq_interval)
                # again, we need some closure.
                self._freq_intervals_by_cpu[cpu].append(FreqInterval(
                                                        cpu=cpu,
                                                        frequency=freq_b.data.state,
                                                        interval=Interval(
                                                            freq_b.timestamp,
                                                            self._trace.duration
                                                        )
                                                    )
                                                )
        else:
            # we have cpu_frequency_switch_start
            for cpu, events in self._freq_events_by_cpu.iteritems():
                last_timestamp = 0.0
                for freq in events:
                    interval = Interval(last_timestamp, freq.timestamp)
                    freq_interval = FreqInterval(cpu=cpu,
                                               frequency=freq.data.start,
                                               interval=interval,
                                               )
                    self._freq_intervals_by_cpu[cpu].append(freq_interval)
                    last_timestamp = freq.timestamp
                # closure
                self._freq_intervals_by_cpu[cpu].append(FreqInterval(
                                                        cpu=cpu,
                                                        frequency=freq.data.end,
                                                        interval=Interval(
                                                            last_timestamp,
                                                            self._trace.duration
                                                        )
                                                    )
                                                )

        return self._freq_intervals_by_cpu

    def _cpu_idle_events_handler(self):
        """Handler function for CPU Idle events"""
        self._cpu_idle_intervals_by_cpu = defaultdict(IntervalList)
        if 'cpu_idle' in self.idle_tracepoints:
            for cpu, events in self._cpu_idle_events_by_cpu.iteritems():
                last_event = None
                for cpu_idle_a in events:
                    state = cpu_idle_a.data.state
                    if state == 4294967295 and last_event and \
                        last_event.data.state != 4294967295: # exit from LPM
                        interval = Interval(last_event.timestamp, cpu_idle_a.timestamp)
                        idle_interval = IdleInterval(cpu=cpu,
                                                     state=last_event.data.state,
                                                     interval=interval,
                                                    )
                        self._cpu_idle_intervals_by_cpu[cpu].append(idle_interval)
                    last_event = cpu_idle_a

                # again, we need some closure.
                if last_event and last_event.data.state != 4294967295L:
                    self._cpu_idle_intervals_by_cpu[cpu].append(IdleInterval(
                                                        cpu=cpu,
                                                        state=last_event.data.state,
                                                        interval=Interval(
                                                            last_event.timestamp,
                                                            self._trace.duration
                                                        )
                                                    )
                                                )
        else: # Use cpu_idle_enter/exit
            for cpu, events in self._cpu_idle_events_by_cpu.iteritems():
                last_event = None
                last_timestamp = 0.0
                for cpu_idle_a in events:
                    tp = cpu_idle_a.tracepoint
                    # use just exit as we may have CPU in LPM before trace started.
                    if tp == 'cpu_idle_exit': # exit from LPM
                        interval = Interval(last_timestamp, cpu_idle_a.timestamp)
                        idle_interval = IdleInterval(cpu=cpu,
                                                     state=cpu_idle_a.data.idx,
                                                     interval=interval,
                                                    )
                        self._cpu_idle_intervals_by_cpu[cpu].append(idle_interval)
                    else: # enter LPM
                        last_timestamp = cpu_idle_a.timestamp
                    last_event = cpu_idle_a

                # again, we need some closure.
                if last_event and last_event.tracepoint != 'cpu_idle_exit':
                    self._cpu_idle_intervals_by_cpu[cpu].append(IdleInterval(
                                                        cpu=cpu,
                                                        state=last_event.data.idx,
                                                        interval=Interval(
                                                            last_event.timestamp,
                                                            self._trace.duration
                                                        )
                                                    )
                                                )

        return self._cpu_idle_intervals_by_cpu

    def _sim_busy_interval_handler(self):
        """Handler function for simultaneously busy cores"""

        def sim_busy_gen():
            busy_cores = []
            last_ts = 0.0
            for state_change in self._state_changes:
                current_ts = state_change.timestamp
                sim_busy_interval = \
                    SimBusyInterval(cpus=set(busy_cores),
                                    interval=Interval(last_ts, current_ts)
                                    )
                yield sim_busy_interval
                if state_change.state is BusyState.BUSY:
                    busy_cores.append(state_change.cpu)
                elif state_change.state is BusyState.IDLE:
                    try:
                        busy_cores.remove(state_change.cpu)
                    except ValueError:
                        pass # already seen as idle
                last_ts = current_ts

            # closure.
            yield SimBusyInterval(cpus=set(busy_cores),
                                  interval=Interval(last_ts, self._trace.duration)
                                 )

        self._sim_busy_intervals = IntervalList(sim_busy_gen())
        return self._sim_busy_intervals

    def _parse_freq_events(self):
        """Parse CPU frequency intervals"""
        self._freq_events_by_cpu = defaultdict(EventList)
        self.freq_tracepoints = set(['cpu_frequency_switch_start'])
        if not self.freq_tracepoints.intersection(self._trace.tracepoints):
            self.freq_tracepoints = set(['cpu_frequency'])

        def freq_events_gen():
            filter_func = lambda event: event.tracepoint in self.freq_tracepoints
            for event in filter(filter_func, self._events):
                yield event

        for event in freq_events_gen():
            self._freq_events_by_cpu[event.data.cpu_id].append(event)

    def _parse_cpu_idle_events(self):
        """Parse CPU idle intervals"""
        self._cpu_idle_events_by_cpu = defaultdict(EventList)
        self.idle_tracepoints = set(['cpu_idle_enter', 'cpu_idle_exit'])
        if not self.idle_tracepoints.intersection(self._trace.tracepoints):
            self.idle_tracepoints = set(['cpu_idle'])
        def cpu_idle_events_gen():
            # Best to use different tracepoint.
            filter_func = lambda event: event.tracepoint in self.idle_tracepoints
            for event in filter(filter_func, self._events):
                    yield event

        if 'cpu_idle' in self.idle_tracepoints:
            for event in cpu_idle_events_gen():
                self._cpu_idle_events_by_cpu[event.data.cpu_id].append(event)
        else:
            for event in cpu_idle_events_gen():
                self._cpu_idle_events_by_cpu[event.cpu].append(event)

    def _parse_rq_events(self):
        print """Parses CPU run-queue events"""
        self._task_intervals_by_cpu = defaultdict(IntervalList)
        self._rq_events_by_cpu = defaultdict(EventList)
        self._state_changes = EventList()
        self._tasks_by_cpu = defaultdict(set)
        self.sched_tracepoints = set(['sched_switch', 'sched_wakeup'])
        
        def sched_events_gen():
            filter_func = lambda event: event.tracepoint in self.sched_tracepoints
            for event in filter(filter_func, self._events):
                yield event

        runnable_tasks = defaultdict(set)
        update_running = defaultdict(lambda: False)
        last_seen_timestamps = defaultdict(lambda: defaultdict(lambda: self._trace.interval.start))
        last_seen_state = defaultdict(lambda: defaultdict(lambda: TaskState.UNKNOWN))
        last_state = defaultdict(lambda: BusyState.UNKNOWN)
        last_rq_depth = defaultdict(lambda: self._trace.interval.start)
        next_task_by_cpu = defaultdict(lambda: None)

        for event in sched_events_gen():
            tracepoint, timestamp, data = event.tracepoint, event.timestamp, event.data
            if tracepoint == 'sched_switch':
                cpu = event.cpu
                prev_task = Task(name=data.prev_comm, pid=data.prev_pid, prio=data.prev_prio)
                # Getting descheduled (fix: note correct state in task_intervals)
                prev_task_state = TaskState.RUNNING # last_seen_state[cpu][prev_task]
                prev_task_interval = TaskInterval(task=prev_task, cpu=cpu,
                    interval=Interval(last_seen_timestamps[cpu][prev_task], timestamp),
                    state=prev_task_state)

                next_task = Task(name=data.next_comm, pid=data.next_pid, 
                                 prio=data.next_prio)
                next_task_by_cpu[cpu] = next_task
                
                next_task_interval = TaskInterval(task=next_task, cpu=cpu, 
                    interval=Interval(last_seen_timestamps[cpu][next_task], timestamp), 
                    state=last_seen_state[cpu][next_task])

                self._task_intervals_by_cpu[cpu].append(prev_task_interval)
                self._task_intervals_by_cpu[cpu].append(next_task_interval)
                
                adjusted_runstate = data.prev_state
                if adjusted_runstate in (TaskState.RUNNING, TaskState.RUNNABLE):
                    adjusted_runstate = TaskState.RUNNABLE
                # helps track when things are running/runnable and dequeued
                # in task_intervals
                last_seen_timestamps[cpu][next_task] = timestamp
                last_seen_timestamps[cpu][prev_task] = timestamp
                last_seen_state[cpu][prev_task] = adjusted_runstate
                last_seen_state[cpu][next_task] = TaskState.RUNNING
                
                # track state changes
                if next_task.pid == 0:
                    current_state = BusyState.IDLE
                elif last_state != BusyState.BUSY:
                    current_state = BusyState.BUSY

                if current_state != last_state[cpu]:
                    state_change = StateChange(cpu=cpu,
                                               timestamp=timestamp,
                                               state=current_state)
                    self._state_changes.append(state_change)
                    last_state[cpu] = current_state
                    update_running[cpu] = True

                # Track runnable tasks
                if adjusted_runstate is TaskState.RUNNABLE:
                    runnable_tasks[cpu].add(prev_task)
                else:
                    try:
                        runnable_tasks[cpu].remove(prev_task)
                    except KeyError:
                        pass

                # idle task runs only when nothing to run.
                runnable_tasks[cpu].clear() if next_task.pid == 0 else \
                    runnable_tasks[cpu].add(next_task)
                # useful to track seen tasks
                self._tasks_by_cpu[cpu].add(next_task)
                self._tasks_by_cpu[cpu].add(prev_task)

            elif tracepoint == 'sched_wakeup':
                target_cpu = data.target_cpu
                cpu = event.cpu
                # When a task wakeup occurs, its placed on run-queue (RQ)
                # but may not be RUNNING right-away (depending on priority)
                # during this time & if anything is runnable
                task = Task(name=data.comm, pid=data.pid, prio=data.prio)
                # woken-up task can run right-away if nothing is on queue.
                # we handle this later.
                
                # first we note last seen state on cpu it was last seen
                # since this tracepoint can occur in context of any cpu, 
                # we simply have to do a search to find where this was running
                last_seen_cpu = None
                for _cpu in last_seen_timestamps.keys():
                    if last_seen_timestamps[_cpu][task] != 0.0:
                        last_seen_cpu = _cpu
                        break
                if last_seen_cpu is not None:
                    prev_task_state = last_seen_state[last_seen_cpu][task]
                    prev_task_interval = TaskInterval(task=task, cpu=last_seen_cpu,
                        interval=Interval(last_seen_timestamps[last_seen_cpu][task], timestamp),
                        state=prev_task_state)
                    self._task_intervals_by_cpu[last_seen_cpu].append(prev_task_interval)
                    last_seen_timestamps[last_seen_cpu][task] = timestamp
                else:
                    pass #oh no, likely first time queued or traced
                    
                last_seen_state[target_cpu][task] = TaskState.TASK_WAKING
                try:
                    runnable_tasks[last_seen_cpu].remove(task)
                    
                except KeyError:
                    pass
                runnable_tasks[target_cpu].add(task)
                #if data.success: # most likely true
                last_seen_timestamps[target_cpu][task] = timestamp
                self._tasks_by_cpu[target_cpu].add(task)


            num_runnable = len(runnable_tasks[cpu])
            if num_runnable != last_rq_depth[cpu] or update_running[cpu]:
                running = 1 if last_state[cpu] == BusyState.BUSY else 0
                rq_changes = RunQueueChange(cpu=cpu, timestamp=timestamp,
                    runnable=num_runnable, running=running)
                self._rq_events_by_cpu[cpu].append(rq_changes)

            last_rq_depth[cpu] = num_runnable

        # closure
        for cpu, task in next_task_by_cpu.iteritems():
            if task:
                task_interval = TaskInterval(task=task, cpu=cpu, # what's cpu.
                                    interval=Interval(last_seen_timestamps[cpu][task], self._trace.duration),
                                    state=last_seen_state[cpu][task],
                                )
                self._task_intervals_by_cpu[cpu].append(task_interval)
