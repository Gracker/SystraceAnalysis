# 使用说明

1. install python2
2. 执行命令 ：python setup.py build
3. 执行命令 : python setup.py install
3. 执行自定义的脚本 ：python xxxxxxx.py (write by yourself)

一旦你修改了源码，就需要重新执行 python setup.py build 和 python setup.py install

# 备注

**Systrace 文件在抓取的时候需要加 --no-compress 参数，才可以正常进行解析**

# 使用案例

## 计算 Running 的进程时间

### 一个示例
示例代码在 ： example_demo 文件夹中

```shell
cd example_demo
python2.7 parse_core_frequencies.py -pf trace_pid.txt -f trace.html -pid 4912 
```

其中 
1. parse_core_frequencies.py 是一个预先写好的解析脚本，可以根据需要自己修改 （必选）
2. -pf trace_pid.txt ， -pf 指定进程信息，这个信息是保存在 Systrace 中的，需要使用文本打开，提取出来并放到单独的文件里面（后续考虑直接写脚本提取），格式如下 （必选）：
    ```
    system        3132  3132 m.huawei.iaware
    system        3132  3141 Jit thread pool
    system        3132  3146 Signal Catcher
    system        3132  3160 HeapTaskDaemon
    system        3132  3161 ReferenceQueueD
    system        3132  3162 FinalizerDaemon
    system        3132  3163 FinalizerWatchd
    system        3132  3164 Binder:3132_1
    system        3132  3172 Binder:3132_2
    system        3132  3175 Timer-0
    system        3132  3221 Profile Saver
    ```
3. -f trace.html , -f 指定需要解析的 Systrace 文件，这个 Systrace 文件在抓取的时候需要加 --no-compress 参数 （必选）
    ```
    python /mnt/d/Android/platform-tools/systrace/systrace.py --no-compress
    ```

4. -pid 4912 , -pid 指定想看这个进程里面各个线程的信息 （可选）

### 示例结果

目前会有三个结果
1. 2020-07-02-09_42_53_result_sort_by_pid.csv   ： 按照 pid 排序
    ```
    duration	pid	name
    140.889	4912	ndroid.launcher
    106.197	1721	system_server
    95.628	768	surfaceflinger
    94.282	790	aptouch_daemon
    67.045	11675	adbd
    61.949	725	composer@2.2-se
    38.987	692	kworker/u16:6
    36.832	373	kworker/u16:4
    34.782	256	kworker/u16:2
    17.187	3132	m.huawei.iaware
    16.233	319	irq/217-thp
    15.855	506	servicemanager
    13.664	505	logd
    12.234	977	chargemonitor
    11.407	3153	m.android.phone
    10.697	756	perfgenius@2.0-
    ```
2. 2020-07-02-09_42_55_result_sort_by_process.csv ： 单个 process 的排序，加了 -pid 参数才会有
    ```
    duration	pid	process_name	task_name	tid
    63.838	4912	ndroid.launcher	RenderThread	8425
    45.609	4912	ndroid.launcher	ndroid.launcher	4912
    10.834	4912	ndroid.launcher	mali-cmar-backe	8444
    6.488	4912	ndroid.launcher	Profile Saver	4953
    5.393	4912	ndroid.launcher	launcher-loader	5072
    3.543	4912	ndroid.launcher	mali-mem-purge	8435
    2.278	4912	ndroid.launcher	mali-hist-dump	8445
    1.496	4912	ndroid.launcher	Jit thread pool	4922
    0.746	4912	ndroid.launcher	GPU completion	11935
    0.417	4912	ndroid.launcher	AppEyeUiProbeTh	8424
    0.154	4912	ndroid.launcher	Binder:4912_7	11884
    0.093	4912	ndroid.launcher	interaction-int	6637
    ```
3. 2020-07-02-09_42_58_cpu_frequency_intervals.csv  ： cpu 频率的情况

    ```
    554000	807000	826000	903000	999000	1172000	1287000	1344000	1392000	1460000
    338.163025	0.003581	0	0.007188	90.344989	0	0	12.049746	0	3.151185
    271.471246	0.007264	0	0.009346	48.205512	0	0	11.516725	0	5.283069
    235.732599	0.002104	0	0.00328	89.276383	0	0	10.050754	0	3.585886
    284.607696	0.006239	0	0.013338	89.026083	0	0	13.977275	0	3.827001
    0	0	9.560512	0	0	0.216869	49.905641	0	0.336019	0
    0	0	1.701353	0	0	0.019997	30.227398	0	0.472217	0
    0	0	0	0	0	0	0	0	0	0
    0	0	0	0	0	0	0	0	0	0
    ```

# TODO
1. 结果直接用网页展示
2. 一次性展示所有进程和线程情况，以 PID 为父