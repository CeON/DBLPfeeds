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
import getopt
import re
import sys
import xml.sax

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
                  record[field] = record.get(field, []) + [text]
               else:
                  record[field] = text
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

   TYPES = ['conf', 'journals']

   while True:
      record = (yield)
      match = re.match('db/([^/]*)/([^/]*)/.*', record['url'])
      if not match:
         continue
      if not str(match.group(1)) in TYPES:
         continue
      record['venue'] = str(match.group(1)) + '/' + str(match.group(2))
      target.send(record)

@coroutine
def collect(collected):
   """Groups records by venues."""

   while True:
      record = (yield)
      venue = record['venue']
      if venue not in collected:
         collected[venue] = []
      collected[venue].append(record)

def store(collected, outDir):
   """Store records in files."""

   DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'

   now = datetime.datetime.utcnow()
   nowStr = now.strftime(DATETIME_FORMAT)

   for venue in collected:
      fileName = re.sub('[^a-zA-Z0-9_/-]', '', venue)
      handle = open(outDir + '/' + fileName + '.xml', 'w')
      handle.write('<?xml version="1.0" encoding="UTF-8" ?>\n<rss version="2.0">\n<channel>\n')
      handle.write('  <title>%s</title>\n' % venue)
      handle.write('  <description>%s</description>\n' % 'TODO')
      handle.write('  <link>http://dblp.uni-trier.de/db/%s/index.html</link>\n' % venue)
      handle.write('  <lastBuildDate>%s</lastBuildDate>\n\n' % nowStr)

      for record in collected[venue]:
         modDate = datetime.datetime.strptime(record['mdate'], "%Y-%m-%d")
         handle.write('  <item>\n    <title>%s</title>\n' % record['title'].encode('utf-8'))
         handle.write('    <description>%s</description>\n' % 'TODO')
         handle.write('    <author>%s</author>\n' % ', '.join(record['author']).encode('utf-8'))
         handle.write('    <link>%s</link>\n' % record['ee'].encode('utf-8'))
         handle.write('    <guid>%s</guid>\n' % record['ee'].encode('utf-8'))
         handle.write('    <pubDate>%s</pubDate>\n' % modDate.strftime(DATETIME_FORMAT))
         handle.write('  </item>\n\n')

      handle.write('</channel>\n</rss>\n')
      handle.close()

if __name__ == "__main__":
   def usage():
      print 'Usage: %s <outDir>' % sys.argv[0]

   if len(sys.argv) < 2:
      usage()
      sys.exit(1)

   fromDate = datetime.datetime.now() - datetime.timedelta(400)

   collected = {}

   chain = collect(collected)
   chain = filter_by_venue(chain)
   chain = filter_by_date(fromDate, chain)
   chain = filter_incomplete(chain)
   chain = to_records(chain)

   parse_xml(chain, sys.stdin)

   store(collected, sys.argv[1])

# vim:et:sw=3:ts=3
