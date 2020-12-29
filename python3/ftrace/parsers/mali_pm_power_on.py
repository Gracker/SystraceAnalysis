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

TRACEPOINT = 'mali_pm_power_on'

__all__ = [TRACEPOINT]

MaliPMPowerOnBase = namedtuple(TRACEPOINT,
    [
    'event',
    'value',
    ]
)

class MaliPMPowerOn(MaliPMPowerOnBase):
    __slots__ = ()
    def __new__(cls, event, value):

            value=int(value)
            
            return super(cls, MaliPMPowerOn).__new__(
                cls,
                event=event,
                value=value,
            )

mali_pm_power_on_pattern = re.compile(
        r"""
        event=(?P<event>\d+)\s+
        =(?P<value>\d+)
        """,
        re.X|re.M
)

@register_parser
def mali_pm_power_on(payload):
    """Parser for `mali_pm_power_on` tracepoint"""
    try:
        match = re.match(mali_pm_power_on_pattern, payload)
        if match:
            match_group_dict = match.groupdict()
            return MaliPMPowerOn(**match_group_dict)
    except Exception as e:
        raise ParserError(e.message)
