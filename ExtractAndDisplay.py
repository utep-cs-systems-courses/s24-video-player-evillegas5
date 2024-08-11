#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64
import queue

class blockQueue:
    def __init__(self, size):
        self.size = size
        self.q = queue.Queue(self.size)
        self.full = threading.Semaphore(0)
        self.empt = threading.Semaphore(self.size)
        self.ql = threading.Lock()

    def put(self, item):
        self.empt.acquire()
        self.ql.acquire()
        self.q.put(item)
        self.ql.release()
        self.full.release()

    def get(self):
        self.full.acquire()
        self.ql.acquire()
        output = self.q.get()
        self.ql.release()
        self.empt.release()

        return output

def extractFrames(fileName, outputBuffer, maxFramesToLoad=9999):
    # Initialize frame count 
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success,image = vidcap.read()
    
    print(f'Reading frame {count} {success}')
    while success and count < maxFramesToLoad:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        # add the frame to the buffer
        outputBuffer.put(image)
       
        success,image = vidcap.read()
        print(f'Reading frame {count} {success}')
        count += 1

    print('Frame extraction complete')

def convertGreyscale(inputBuffer, outputBuffer):
    count = 0
    
    while not inputBuffer.empty():
        curframe = inputBuffer.get()
        
        # conver image to greyscale
        greyFrame = cv2.cvtColor(curframe, cv2.COLOR_BGR2GRAY)

        # output file
        outputBuffer.put(greyFrame)

        count += 1
        

def displayFrames(inputBuffer):
    # initialize frame count
    count = 0 

    # go through each frame in the buffer until the buffer is empty
    while not inputBuffer.empty():
        # get the next frame
        frame = inputBuffer.get()

        print(f'Displaying frame {count}')        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1

    print('Finished displaying all frames')
    # cleanup the windows
    cv2.destroyAllWindows()

# filename of clip to load
filename = 'clip.mp4'

# thread for extraction
extractQueue = blockQueue(10)
extract_thread = threading.Thread(target=lambda: extractFrames(filename, extractQueue, 72))

# thread for greyscale
greyScaleQueue = blockQueue(10)
greyScale_thread = threading.Thread(target=lambda: convertGreyscale(extractQueue, greyScaleQueue))

# thread for display
display_thread = threading.Thread(target=lambda: displayFrames(greyScaleQueue))
threading.Thread()

# initialize threads
extract_thread.start()
greyScale_thread.start()
display_thread.start()

