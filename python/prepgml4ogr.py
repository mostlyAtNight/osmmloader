#!/usr/bin/python

## Copyright (c) 2011 Astun Technology

## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.

''' SAX parser implementation to prepare an Ordnance Survey
    GML file (.gml or .gz) so that it is ready to be loaded by OGR 1.8
    or above.
    The parser changes the srsName attribute to EPSG:27700 and
    promotes the fid attribute to a child element.
    Output is via stdout and is UTF-8 encoded.
    
    usage: python prepgml4ogr.py file.gml
'''

import sys
import os.path
import gzip
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax import saxutils

import prep_osmm
import timer

class gmlhandler(ContentHandler):

    def __init__ (self, preparer):
        # The class that will prepare the features
        self.preparer = preparer
        self.feat = None
        self.recording = False

    def startDocument(self):
        self.output('<?xml version="1.0" ?>')

    def startElement(self, name, attrs):
        name = name.split(':')[1]
        # Determine if we are interested
        # in starting to record the raw
        # XML string so we can prepare
        # the feature when the feature ends
        if name in self.preparer.feat_types:
            self.buffer = []
            self.recording = True
        # Update all srsName attributes to EPSG:27700
        tmp = '<' + name
        for (name, value) in attrs.items():
            if name == 'srsName':
                value = 'EPSG:27700'
            elif name == 'xlink:href':
                name = 'href'
            tmp += ' %s=%s' % (name, saxutils.quoteattr(value))
        tmp += '>'
        if self.recording:
            self.buffer.append(tmp)
        else:
            self.output(tmp)
        return

    def characters (self, ch):
        if len(ch.strip()) > 0:
            if self.recording:
                self.buffer.append(saxutils.escape(ch))
            else:
                self.output(saxutils.escape(ch))

    def endElement(self, name):
        name = name.split(':')[1]
        if self.recording:
            self.buffer.append('</' + name + '>')
        else:
            self.output('</' + name + '>')
        if name in self.preparer.feat_types:
            self.recording = False            
            self.output(self.preparer.prepare_feature(''.join(self.buffer)))
            self.buffer = []

    def output(self, str):
        sys.stdout.write(str.encode('utf-8'))

class prep_gml():

    def __init__ (self):
        self.feat_types = []

    def get_feat_types(self):
        return self.feat_types

    def prepare_feature(self, feat_str):
        return feat_str

def main():
    if len(sys.argv) < 2:
        print 'usage: python prepgml4ogr.py gmlfile [[prep_module.]prep_class]'
        sys.exit(1)

    inputfile = sys.argv[1]
    if os.path.exists(inputfile):

        # Create an instance of a preparer
        # class which is used to prepare
        # features as they are read
        prep_class = 'prep_gml'
        try:
            prep_class = sys.argv[2]
        except IndexError:
            pass
        preparer = get_preparer(prep_class)
        
        parser = make_parser()
        parser.setContentHandler(gmlhandler(preparer))

        if os.path.splitext(inputfile)[1].lower() == '.gz':
            file = gzip.open(inputfile, 'r')
        else:
            # Assume non compressed gml, xml or no extension
            file = open(inputfile, 'r')

        #with timer.Timer():
        parser.parse(file)

    else:
        print 'Could not find input file: ' + inputfile

def get_preparer(prep_class):
    parts = prep_class.split('.')
    if len(parts) > 1:
        prep_module = parts[0]
        prep_module = __import__(prep_module)
        prep_class = getattr(prep_module, parts[1])
    else:
        prep_class = globals()[prep_class]
    return prep_class()

if __name__ == '__main__':
    main()
