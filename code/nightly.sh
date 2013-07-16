#!/bin/sh

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

BASE=..
CODE=$BASE/code
TMP=$BASE/tmp
WWW=$BASE/www

BHT=$TMP/dblp_bht.xml
DB=$TMP/dblp.sqlite
DUMP=$TMP/dblp.xml.gz
JSON=$TMP/index.json
HTML=$TMP/index.html.part

rm -f $TMP/dblp-*.xml.gz
wget http://dblp.uni-trier.de/xml/dblp.xml.gz -O $DUMP
rm -f $DB
python $CODE/makeDB.py $BHT $DUMP $DB
rm -rf $TMP/conf $TMP/journals $JSON $HTML
mkdir -p $TMP/conf $TMP/journals
python $CODE/makeFiles.py $DB $TMP $HTML $JSON
cp -r $TMP/conf $TMP/journals $WWW/
cp $JSON $WWW/
cat $CODE/index.html.template | sed -e "/#########/r $HTML" > $WWW/index.html

