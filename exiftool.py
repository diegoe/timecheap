#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# ExifTool - Context generator wrapper for exiftool.
#
# Author: Sven Marnach
# URL: http://stackoverflow.com/a/10075210
#
# Handy python wrapper to work with exiftool. Note that python modules
# only work on images, but exiftool itself work on videos too. This is
# why we need this, because video files have EXIF data that is not read
# by PIL or others.

import subprocess
import os
import json

class ExifTool(object):

    sentinel = "{ready}\n"

    def __init__(self, executable="/usr/local/bin/exiftool"):
        self.executable = executable

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def  __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.sentinel):
            output += os.read(fd, 4096)
        return output[:-len(self.sentinel)]

    def get_metadata(self, *filenames):
        return json.loads(self.execute("-Duration", "-SubSecCreateDate", "-j", "-n", *filenames))
        #return json.loads(self.execute("-G", "-j", "-n", *filenames))
