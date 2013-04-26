#!/usr/bin/env python

# Copyright (c) 2012-2013 Lukasz Bolikowski
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pickle
import re
import sys

mapping = {}
for line in sys.stdin:
   match = re.match('<bht key="/db/(.*)/(.*)/index.bht" title="(.*)">', line.strip())
   if not match:
      continue
   kind = match.group(1)
   if kind not in ('conf', 'journals'):
      continue
   venue = match.group(2)
   title = match.group(3)
   mapping[kind + '/' + venue] = title

dump = open(sys.argv[1], 'w')
pickle.dump(mapping, dump)
dump.close()

ordered = sorted([(k, mapping[k]) for k in mapping])
html = open(sys.argv[2], 'w')
html.write('<ul>\n')
for k, v in ordered:
   html.write('  <li><a href="%s.xml">%s</a></li>\n' % (k, v))
html.write('</ul>\n')
html.close()

# vim:et:sw=3:ts=3
