#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# timecheap - Set video metadata timecodes from EXIF tags
#
# Author: Diego Escalante Urrelo <diegoe@gnome.org>
# URL: https://github.com/diegoe/timecheap
# License: GPL 2.0
#
# Sets the "timecode" metadata on video files that mostly come from
# Canon DSLRs or other non professional cameras.
#
# This will make Premiere read a "Media Start" time other than 00:00:00.
# It uses the EXIF data from the video file to set a timecode start
# time.
#
# Note that your camera and audio recorder should be as closely synced
# as possible (time-wise). Try to have them sync their clocks before
# starting your shoot.

from exiftool import ExifTool

import datetime
import time
import os
import glob
import subprocess

files = glob.glob("MVI_*.MOV")

# Magic delta is the time offset between your video files and audio
# files, if there's any.
#
# If you are putting down a fire, then you are gonna need to figure out
# the time difference between the "creation time" of your video and your
# audio file.
#
# Do some Premiere math and use the start of the sequence timeline to
# figure out what time is it should be when your video starts.
# It's worth it, but a little tricky to wrap your head around it.
#MAGIC_DELTA = datetime.timedelta(minutes=01, seconds=35)
MAGIC_DELTA = datetime.timedelta(seconds=18)

# Frame delta is kinda tricky. It's here to help in case you notice a
# set amount of frame divergence between your audio and video files.
#
# It's a lazy man's offset parameter.
#
# Note that there's still human intervention required to get a perfect
# syncro. Not to mention that some stuff between timecodes, non drop
# frames, and Premiere being Adobe-ish, makes this whole business more
# complicated than it should. I don't fully know how this works.
#FRAME_DELTA = "24"
FRAME_DELTA = "00"

# Prefix for the created files
FILE_PREFIX = "TC_"

# We use exiftool to gather specific metadata from the EXIF portion of
# the video files.
#
# If you need more fields, you should check out exiftool.py and edit the
# request in execute()
files_meta = ""
with ExifTool() as e:
    files_meta = e.get_metadata("\n".join(files))

for meta in files_meta:
    file_name = meta['SourceFile']
    new_file_name = "%s%s" % (FILE_PREFIX, file_name)

    if os.path.isfile(new_file_name):
        print "%s already exists, skipping." % new_file_name

    create_date = meta['SubSecCreateDate']
    #video_len = meta['Duration']

    video_date = create_date.split(" ")[1]
    video_time = video_date.split(".")[0]

    video_start_time = datetime.datetime.strptime(video_time, "%H:%M:%S")

    ##########
    # Left-over from when I was trying to figure out sync delta automatically.
    #
    #manual_sync_start = "19:57:49"
    #manual_start_time = datetime.datetime.strptime(manual_sync_start, "%H:%M:%S")

    #video_duration = datetime.timedelta(seconds=video_len)

    # Make sure we get only a minute:second delta, an absolute difference.
    #if MAGIC_DELTA is None:
    #    MAGIC_DELTA = (video_start_time - manual_start_time)
    #    if MAGIC_DELTA.days < 0:
    #        MAGIC_DELTA = datetime.timedelta() - MAGIC_DELTA
    ##########

    # This is the tricky part. We have to correct for time offsets here.
    new_video_time = video_start_time - MAGIC_DELTA
    print video_start_time, new_video_time, MAGIC_DELTA

    write_time = new_video_time.strftime("%H:%M:%S")
    write_date = datetime.datetime.strptime(create_date.split(" ")[0], "%Y:%m:%d").strftime("%Y-%m-%d")
    preserve_date = datetime.datetime.strptime("%s %s" % (write_date, write_time), "%Y-%m-%d %H:%M:%S")

    # Modify timecode and metadata date
    # Do not modify any of the streams, just the container metadata
#    ffmpeg_call = "ffmpeg -i %s -loglevel warning -vcodec copy -acodec copy -timecode %s:%s -metadata date=%s %s" % (
    ffmpeg_call = "ffmpeg -i %s \
                        -vcodec copy -acodec copy \
                        -timecode %s:00 \
                        -metadata creation_time='%s %s' \
                        -metadata date=%s \
                        %s" % (
                    file_name,
                    write_time,
                    write_date,
                    write_time,
                    write_date,
                    new_file_name)
    print ffmpeg_call

    # Copy EXIF data like camera, author, lens, etc.
    # exiftool can be built from homebrew
    exiftool_call = "exiftool -overwrite_original -tagsFromFile  %s %s" % (file_name, new_file_name)
    print exiftool_call

    # Keep creation and modification dates intact.
    # SetFile comes from xcode dev utils.
    setdate_d_call = "SetFile -d '%s' %s" % (preserve_date.strftime("%m/%d/%Y %H:%M:%S"), new_file_name)
    print setdate_d_call

    setdate_m_call = "SetFile -m '%s' %s" % (preserve_date.strftime("%m/%d/%Y %H:%M:%S"), new_file_name)
    print setdate_m_call

    subprocess.call(ffmpeg_call, shell=True)
#    subprocess.call(exiftool_call, shell=True)
#    subprocess.call(setdate_d_call, shell=True)
#    subprocess.call(setdate_m_call, shell=True)
