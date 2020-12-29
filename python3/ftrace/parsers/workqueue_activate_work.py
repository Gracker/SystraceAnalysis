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
from collections import namedtuple
#from ftrace.third_party.cnamedtuple import namedtuple

TRACEPOINT = 'workqueue_activate_work'


__all__ = [TRACEPOINT]

WorkqueueQueueActivateWorkBase = namedtuple(TRACEPOINT,
    [
    'work_struct', 
    ]
)

class WorkqueueQueueActivateWork(WorkqueueQueueActivateWorkBase):
    __slots__ = ()
    def __new__(cls, work_struct):

            return super(cls, WorkqueueQueueActivateWork).__new__(
                cls,
                work_struct=work_struct
            )

workqueue_activate_work_pattern = re.compile(
        r"""
        work struct (?P<work_struct>.+)
        """,
        re.X|re.M
)

@register_parser
def workqueue_activate_work(payload):
    """Parser for `workqueue_activate_work` tracepoint"""
    try:
        match = re.match(workqueue_activate_work_pattern, payload)
        if match:
            match_group_dict = match.groupdict()
            return WorkqueueQueueActivateWork(**match_group_dict)
    except Exception as e:
        raise ParserError(e.message)
