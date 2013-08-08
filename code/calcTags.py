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

from lxml import etree
import os
import os.path
import re
import sqlite3
import sys

def parse_chunk(conn, chunk):
   doc = etree.fromstring(chunk)
   items = doc.xpath("//*[local-name() = 'arXiv']")
   for item in items:
      title = re.sub('\W+', ' ', item.xpath("./*[local-name() = 'title']")[0].text).strip()
      raw_categories = item.xpath("./*[local-name() = 'categories']")[0].text.strip().split(' ')
      categories = []
      for raw_category in raw_categories:
         if not raw_category.startswith('cs.'):
            continue
         categories += [raw_category]
      categories = ' '.join(categories)
      conn.execute('INSERT INTO arxiv VALUES (?, ?)', (title, categories))
   conn.commit()

def chunks_from_disk(chunks_dir):
   for root, dirs, files in os.walk(chunks_dir):
       for name in files:
          if not name.endswith('.xml'):
             continue
          handle = open(os.path.join(root, name), 'r')
          chunk = handle.read()
          handle.close()
          yield chunk

def calc_tags(conn):
   lookup = {}
   for t, c in conn.execute('SELECT * FROM arxiv'):
      h = re.sub('[^a-z0-9]', '', t.lower())
      lookup[h] = c

   tag_count = {}
   venue_total = {}
   for t, _, _, _, v, _ in conn.execute('SELECT * FROM record'):
      h = re.sub('[^a-z0-9]', '', t.lower())
      if h not in lookup:
         continue
      for c in lookup[h].split(' '):
         tag_count[(v, c)] = tag_count.get((v, c), 0) + 1
         venue_total[v] = venue_total.get(v, 0) + 1

   tags = []
   for v, c in tag_count:
      count = tag_count[(v, c)]
      fraction = 1.0 * count / venue_total[v]
      if count > 4 and fraction > 0.3:
         tags += [(v, c)]
   return tags

def store_tags(conn, tags):
   conn.execute('CREATE TABLE tags (venue TEXT, tag TEXT)')
   for venue, tag in tags:
      conn.execute('INSERT INTO tags VALUES (?, ?)', (venue, tag))
   conn.commit()

if __name__ == '__main__':
   if len(sys.argv) < 3:
      print >> sys.stderr, 'Usage: %s <db_filename> <chunks_dir>' % sys.argv[0]
      sys.exit(1)
   db_filename, chunks_dir = sys.argv[1], sys.argv[2]

   conn = sqlite3.connect(db_filename)
   conn.execute('CREATE TABLE arxiv (title TEXT, categories TEXT)')
   chunks = chunks_from_disk(chunks_dir)
   for chunk in chunks:
      parse_chunk(conn, chunk)
   tags = calc_tags(conn)
   store_tags(conn, tags)
   conn.close()
