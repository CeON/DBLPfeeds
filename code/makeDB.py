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

import datetime
import gzip
import re
import sqlite3
import sys
import xml.sax

KINDS = ['conf', 'journals']

class EventHandler(xml.sax.handler.ContentHandler):
   """SAX content handler using coroutines.
   See: http://www.dabeaz.com/coroutines/"""

   def __init__(self, target):
      self.target = target

   def startElement(self, name, attrs):
      self.target.send(('start', (name, attrs._attrs)))

   def endElement(self, name):
      self.target.send(('end', name))

   def characters(self, text):
      self.target.send(('text', text))

def parse_xml(target, content):
   """SAX parser using coroutines.
   See: http://www.dabeaz.com/coroutines/"""

   parser = xml.sax.make_parser()
   parser.setContentHandler(EventHandler(target))
   parser.parse(content)

def coroutine(func):
   """Decorator for easier handling of coroutines.
   See: http://www.dabeaz.com/coroutines/"""

   def start(*args, **kwargs):
      cr = func(*args, **kwargs)
      cr.next()
      return cr
   return start

@coroutine
def to_records(target):
   """Converts SAX event to records describing documents."""

   PRIMARY = ['article', 'inproceedings']
   SECONDARY = ['author', 'ee', 'title', 'url']
   MULTIPLE = ['author']

   while True:
      event, args = (yield)
      if event == 'start' and args[0] in PRIMARY:
         record = {'key': args[1]['key'], 'mdate': args[1]['mdate']}
         field, text = None, ''
         while True:
            event, args = (yield)
            if event == 'start' and args[0] in SECONDARY:
               field = str(args[0])
               continue
            if field and event == 'text':
               text += args
               continue
            if field and event == 'end' and args in SECONDARY:
               if args in MULTIPLE:
                  record[field] = record.get(field, []) + [text.strip()]
               else:
                  record[field] = text.strip()
               field, text = None, ''
               continue
            if event == 'end' and args in PRIMARY:
               target.send(record)
               break

@coroutine
def filter_incomplete(target):
   """Discards incomplete document descriptions."""

   while True:
      record = (yield)
      if 'author' not in record:
         continue
      if 'ee' not in record or not record['ee'].startswith('http'):
         continue
      if 'title' not in record:
         continue
      if 'url' not in record:
         continue
      target.send(record)

@coroutine
def filter_by_date(fromDate, target):
   """Picks documents that were modified on or after the given date."""

   while True:
      record = (yield)
      modDate = datetime.datetime.strptime(record['mdate'], "%Y-%m-%d")
      if modDate < fromDate:
         continue
      target.send(record)

@coroutine
def filter_by_venue(target):
   """Picks documents that were published at the given venues."""

   while True:
      record = (yield)
      match = re.match('db/([^/]*)/([^/]*)/.*', record['url'])
      if not match:
         continue
      if not str(match.group(1)) in KINDS:
         continue
      record['venue'] = str(match.group(1)) + '/' + str(match.group(2))
      target.send(record)

@coroutine
def store(conn):
   """Store records in database."""

   while True:
      record = (yield)

      authors = ', '.join(record['author'])

      conn.execute('INSERT INTO record VALUES (?, ?, ?, ?, ?)',
         (record['title'], authors, record['mdate'], record['ee'], record['venue']))

def parse_records(conn, fileName):
   fromDate = datetime.datetime.now() - datetime.timedelta(1000)

   chain = store(conn)
   chain = filter_by_venue(chain)
   chain = filter_by_date(fromDate, chain)
   chain = filter_incomplete(chain)
   chain = to_records(chain)

   handle = gzip.open(fileName, 'r')
   parse_xml(chain, handle)
   handle.close()

def parse_venues(conn, fileName):
   handle = open(fileName, 'r')

   for line in handle:
      match = re.match('<bht key="/db/(.*)/(.*)/index.bht" title="(.*)">', line.strip())
      if not match:
         continue
      kind = match.group(1).strip()
      if kind not in KINDS:
         continue
      acronym = match.group(2).strip()
      name = match.group(3).strip()
      try:
         conn.execute('INSERT INTO venue VALUES (?, ?, ?, ?)',
            (kind + '/' + acronym, kind, acronym, name))
      except sqlite3.IntegrityError:
         pass

   handle.close()

def create_tables(conn):
   conn.execute('CREATE TABLE venue (key TEXT PRIMARY KEY, kind TEXT, acronym TEXT, name TEXT)')
   conn.execute('CREATE TABLE record (title TEXT, authors TEXT, date TEXT, link TEXT, venue TEXT)')
   conn.execute('CREATE INDEX byvenue ON record (venue)')

if __name__ == "__main__":
   def usage():
      print 'Usage: %s <dblp_bht.xml> <dblp.xml.gz> <index.sqlite>' % sys.argv[0]

   if len(sys.argv) < 4:
      usage()
      sys.exit(1)

   conn = sqlite3.connect(sys.argv[3])
   create_tables(conn)
   parse_venues(conn, sys.argv[1])
   conn.commit()
   parse_records(conn, sys.argv[2])
   conn.commit()
   conn.close()

# vim:et:sw=3:ts=3
