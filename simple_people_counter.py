#!/usr/bin/env python
# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
import numpy as np
from collections import deque

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=300, help="minimum area size")
ap.add_argument("-b", "--buffer", type=int, default=16, help="max buffer size")
args = vars(ap.parse_args())

pts = deque(maxlen=args["buffer"])
counter = 0
(dX, dY) = (0, 0)
direction = ""
heading_in, heading_out = False, False
went_in, went_out = 0, 0
new = True
time = 0
dirtracker = ""
midpoint = 80
delta = 5

# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
    camera = cv2.VideoCapture(0)
    time.sleep(0.25)
# otherwise, we are reading from a video file
else:
	camera = cv2.VideoCapture(args["video"])

fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
#fgbg = cv2.createBackgroundSubtractorMOG2(history = 100)
# kernel = np.ones((5,5), np.uint8)
# tracker = cv2.Tracker_create("MIL")

while True:
    (grabbed, frame) = camera.read()
    # ret, frame = video_capture.read()
    frame = imutils.resize(frame, width=500)
    frame = frame[0:, 220:380] # shrink the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    fgmask = fgbg.apply(gray) # remove background filter
    thresh = cv2.threshold(fgmask,25,255,cv2.THRESH_BINARY)[1] # adjust threshold
    #blur = cv2.blur(thresh, (5,5)) # blur
    #thresh = cv2.dilate(thresh0,kernel, iterations=1) # dilate image (make blobs bigger)
    thresh = cv2.erode(thresh,None, 2)
    thresh = cv2.dilate(thresh,None, 2) # dilate image (make blobs bigger)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None
    # track = tracker.init(image, cnts)
    # rect = cv2.rectangle(frame, (225,0), (375, 600), (0,0,0), -1)
    # thresh = cv2.bitwise_and(frame, rect)

    # Tracks only 1 object at a time; if field of view is narrow enough, it
    # should be OK. Not the best, but I couldn't figure out how to extract and
    # use feature tracking. To be improved.
    if len(cnts) > 0:
    # for c in cnts:
        c = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c) > args["min_area"]:
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            center = (int(x+w/2), int(y+h/2))
            pts.appendleft(center)
        # ((x, y), radius) = cv2.minEnclosingCircle(c)
        # M = cv2.moments(c)
        # center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        # cv2.putText(frame, "Blob: %s" %c, (x, y),
        #     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        # only proceed if the radius meets a minimum size
        # if radius > args["min_area"]:
        #     # draw the circle and centroid on the frame,
        #     # then update the list of tracked points
        #     cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
        #     cv2.circle(frame, center, 5, (0, 0, 255), -1)
        #     pts.appendleft(center)

    # loop over the set of tracked points
    for i in np.arange(1, len(pts)):
        # if either of the tracked points are None, ignore them
        if pts[i - 1] is None or pts[i] is None:
            continue

        # check to see if enough points have been accumulated in
        # the buffer
        if counter > 30 and i == 1 and pts[-10] is not None:

            if pts[i][0] >= midpoint+delta and new and pts[i][0] <= midpoint+2*delta:
                heading_in = True
                new = False
                time = 0
                dirtracker = "Heading In"
            if pts[i][0] <= midpoint-delta and heading_in:
                # check size of blob for # of people increment
                went_in += 1
                heading_in = False
                new = True
                dirtracker = ""
            if pts[i][0] <= midpoint-delta and new and pts[i][0] >= midpoint-2*delta:
                heading_out = True
                new = False
                time = 0
                dirtracker = "Heading Out"
            if pts[i][0] >= midpoint+delta and heading_out:
                # check size of blob for # of people increment
                went_out += 1
                heading_out = False
                new = True
                dirtracker =""
            if time >= args["buffer"]: # may have skipped, reset
                heading_in, heading_out = False, False
                new = True
                time = 0
                dirtracker = ""

            #print new, dirtracker, time, pts[i][0]

            # # compute the difference between the x and y
            # # coordinates and re-initialize the direction
            # # text variables
            dX = pts[-10][0] - pts[i][0]
            dY = pts[-10][1] - pts[i][1]
            # (dirX, dirY) = ("", "")

            # # ensure there is significant movement in the
            # # x-direction
            # if np.abs(dX) > 20:
            #     dirX = "East" if np.sign(dX) == 1 else "West"

            # # # ensure there is significant movement in the
            # # # y-direction
            # # if np.abs(dY) > 20:
            # #     dirY = "North" if np.sign(dY) == 1 else "South"

            # # # handle when both directions are non-empty
            # # if dirX != "" and dirY != "":
            # #     direction = "{}-{}".format(dirY, dirX)

            # # otherwise, only one direction is non-empty
            # else:
            #     direction = dirX if dirX != "" else dirY

        # otherwise, compute the thickness of the line and
        # draw the connecting lines
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

	# show the movement deltas and the direction of movement on
	# the frame
	# cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
	# 	0.65, (0, 0, 255), 3)
	cv2.putText(frame, "dx: {}, dy: {}".format(dX, dY),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)
	cv2.putText(frame, "In: {}, Out: {}".format(went_in, went_out),
		(10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)
	cv2.putText(frame, dirtracker, (20, 30), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 127, 255), 3)

	# show the frame to our screen and increment the frame counter
	key = cv2.waitKey(1) & 0xFF
	counter += 1
    time += 1

    cv2.imshow('feed', frame) # add more for more video feeds
    # cv2.imshow('fgmask', fgmask)
    cv2.imshow('thresh', thresh)
    #cv2.imshow('frame', dilat)
    #cv2.drawContours(frame, contours, -1, (0,255,0), 3)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
# print "In: %i, Out: %i" %(heading_in, heading_out)
