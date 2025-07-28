# Copyright (c) 2025, Diogo Duarte @ AIxlab-D^3-NSBE-NMS
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Wrapper / handler for mediamtx 

mediamtx should be added to the system path or ohterwise 
"""

import os
import stream.streamer

class Signals:

    def __init__(self):
        pass   

    def initializeStreams(self):
        # initialize the camera, sound, and other sensors
        # should return a handle to each stream or an indexed list
        pass

    def startRecording(self):
        # should get and change a self.directory for storage
        # should require and input to which strean to start recording
        pass

    def stopRecording(self):
        pass


