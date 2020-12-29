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

TRACEPOINT = 'irq_handler_exit'


__all__ = [TRACEPOINT]

IRQHandlerExitBase = namedtuple(TRACEPOINT,
    [
    'irq',
    'name',
    ]
)

class IRQHandlerExit(IRQHandlerExitBase):
    __slots__ = ()
    def __new__(cls, irq, name):
            irq = int(irq)
            return super(cls, IRQHandlerExit).__new__(
                cls,
                irq=irq,
                name=name,
            )

irq_handler_exit_pattern = re.compile(
        r"""
        irq=(?P<irq>\d+)\s+
        name=(?P<name>.+)
        """,
        re.X|re.M
)

@register_parser
def irq_handler_exit(payload):
    """Parser for `irq_handler_exit` tracepoint"""
    try:
        match = re.match(irq_handler_exit_pattern, payload)
        if match:
            match_group_dict = match.groupdict()
            return IRQHandlerExit(**match_group_dict)
    except Exception as e:
        raise ParserError(e.message)
