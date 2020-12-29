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

import re
from ftrace.common import ParserError
from .register import register_parser

try:
    from ftrace.third_party.cnamedtuple import namedtuple
except ImportError:
    from collections import namedtuple


TRACEPOINT = 'sched_rq_runnable_ratio'


__all__ = [TRACEPOINT]


SchedRQRunnableRatioBase = namedtuple(TRACEPOINT,
    [
    'cpu',
    'ratio'
    ]
)


class SchedRQRunnableRatio(SchedRQRunnableRatioBase):
    """
    Tracked rq runnable ratio [0..1023].
    """
    __slots__ = ()
    def __new__(cls, cpu, ratio):
            cpu = int(cpu)
            ratio = float(self.ratio)/1023.0

            return super(cls, SchedRQRunnableRatio).__new__(
                cls,
                cpu=cpu,
                ratio=ratio,
            )

sched_rq_runnable_ratio_pattern = re.compile(
        r"""cpu=(?P<cpu>\d+)\s+
        ratio=(?P<ratio>\d+)\s+
        """,
        re.X|re.M
)

@register_parser
def sched_rq_runnable_ratio(payratio):
    """Parser for `sched_rq_runnable_ratio` tracepoint"""
    try:
        match = re.match(sched_rq_runnable_ratio_pattern, payratio)
        if match:
            match_group_dict = match.groupdict()
            return SchedRQRunnableRatio(**match_group_dict)
    except Exception as e:
        raise ParserError(e.message)
