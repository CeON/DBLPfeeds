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

import os, re, sys, time, urllib, xml.dom.minidom

class OAIHarvester:
	def __init__(self, url, settings, path = '.'):
		self.url = url
		self.settings = settings
		self.path = path
		self.counter = -1

	def getFirst(self):
		self.counter += 1
		print "Chunk #" + str(self.counter)
		url = '%s?verb=ListRecords&%s' % (self.url, self.settings)
		return self.getCommon(url)

	def getNext(self, token):
		self.counter += 1
		print "Chunk #%d, token: %s" % (self.counter, token)
		url = '%s?verb=ListRecords&resumptionToken=%s' % (self.url, token)
		return self.getCommon(url)

	def getCommon(self, url):
		attempt = 0
		while attempt < 3:
			try:
				data = urllib.urlopen(url).read()
				path = self.path + os.sep + ('%04x' % (self.counter / 65536)) + os.sep + ('%02x' % (self.counter % 65536 / 256))
				if not os.path.isdir(path):
					os.makedirs(path)
				name = path + os.sep + ('%08x' % self.counter) + '.xml'
				file = open(name, 'w')
				file.write(data)
				file.close()
				token = self.getToken(data)
				return token
			except:
				attempt += 1
			finally:
				time.sleep(30)
		return None

	def getToken(self, data):
		dom = xml.dom.minidom.parseString(data)
		tmp = dom.getElementsByTagName('resumptionToken')
		if tmp == None or len(tmp) == 0:
			return None
		token = tmp[0].childNodes[0].data
		return token

	def harvest(self, chunk = None, token = None):
		if chunk <> None:
			self.counter = chunk - 1
		if token == None:
			token = self.getFirst()
		while token <> None:
			token = oai.getNext(token)
		print "Done"

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print 'Usage: ' + sys.argv[0] + ' <url> <settings> [<path>] [<chunk> <token>]'
		sys.exit(1)
	url, settings, path, chunk, token = sys.argv[1], sys.argv[2], '.', 0, None
	if len(sys.argv) > 3:
		path = sys.argv[3]
	if len(sys.argv) > 4:
		chunk = int(sys.argv[4])
	if len(sys.argv) > 5:
		token = sys.argv[5]
	oai = OAIHarvester(url, settings, path)
	oai.harvest(chunk, token)
