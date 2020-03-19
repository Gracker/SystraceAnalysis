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

TRACEPOINT = 'kgsl_rail'


__all__ = [TRACEPOINT]

#kgsl_rail: d_name=kgsl-3d0 flag=off

KgslRailBase = namedtuple(TRACEPOINT,
    [
    'd_name',
    'flag',
    ]
)

class KgslRail(KgslRailBase):
    __slots__ = ()
    def __new__(cls, d_name, flag):

            return super(cls, KgslRail).__new__(
                cls,
                d_name=d_name,
                flag=flag,
            )

kgsl_rail_pattern = re.compile(
        r"""
        d_name=(?P<d_name>.+)\s+
        flag=(?P<flag>\w+)
        """,
        re.X|re.M
)

@register_parser
def kgsl_rail(payload):
    """Parser for `kgsl_rail` tracepoint"""
    try:
        match = re.match(kgsl_rail_pattern, payload)
        if match:
            match_group_dict = match.groupdict()
            return KgslRail(**match_group_dict)
    except Exception, e:
        raise ParserError(e.message)
