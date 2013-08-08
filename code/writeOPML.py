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

import cgi
import datetime
import json
import re
import sqlite3
import sys

LABELS = {'AI': 'Artificial Intelligence'}

def write_opml(conn, opmlDirName):
   by_tags = {}
   for v, t in conn.execute('SELECT * FROM tags'):
      by_tags[t] = by_tags.get(t, []) + [v]

   for t in by_tags:
      if not t.startswith('cs.'):
         raise Exception, 'Expecting only cs.* tags'
      sanitizedTag = re.sub('[^A-Z]', '', t)
      label = LABELS.get(sanitizedTag, sanitizedTag)
      handle = open(opmlDirName + '/' + sanitizedTag + '.opml', 'w')
      handle.write("""<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>%s feeds</title>
  </head>
  <body>
    <outline text="%s" title="%s">\n""" % (label, label, label))
      for v in by_tags[t]:
         name = conn.execute('SELECT name FROM venue WHERE key = ?', (v,)).fetchone()
         if not name:
            continue
         name = name[0]
         handle.write("""<outline type="rss" text="%s" title="%s" xmlUrl="http://services.ceon.pl/dblpfeeds/%s.xml" htmlUrl="http://dblp.uni-trier.de/db/%s/index.html"/>\n""" % (name, name, v, v))
      handle.write("""    </outline>\n  </body>\n</opml>""")
      handle.close()

if __name__ == "__main__":
   def usage():
      print 'Usage: %s <dblp.sqlite> <opml_dir>' % sys.argv[0]

   if len(sys.argv) < 3:
      usage()
      sys.exit(1)

   conn = sqlite3.connect(sys.argv[1])
   write_opml(conn, sys.argv[2])
   conn.close()

# vim:et:sw=3:ts=3
