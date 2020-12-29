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

TRACEPOINT = 'softirq_raise'


__all__ = [TRACEPOINT]

SoftIRQRaiseBase = namedtuple(TRACEPOINT,
    [
    'vec',
    'action',
    ]
)

class SoftIRQRaise(SoftIRQRaiseBase):
    __slots__ = ()
    def __new__(cls, vec, action):
            vec = int(vec)
            return super(cls, SoftIRQRaise).__new__(
                cls,
                vec=vec,
                action=action,
            )

softirq_raise_pattern = re.compile(
        r"""
        vec=(?P<vec>\d+)\s+
        \[action=(?P<action>.+)\]
        """,
        re.X|re.M
)

@register_parser
def softirq_raise(payload):
    """Parser for `softirq_raise` tracepoint"""
    try:
        match = re.match(softirq_raise_pattern, payload)
        if match:
            match_group_dict = match.groupdict()
            return SoftIRQRaise(**match_group_dict)
    except Exception as e:
        raise ParserError(e.message)
