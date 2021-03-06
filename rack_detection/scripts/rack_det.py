#! /usr/bin/env python

import numpy as np
import math
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import String
THRESH_AREA = 400
THRESH_MOMENT = 0.2


class rack_detect:

	def __init__(self):
		self.image_sub = rospy.Subscriber('mono_front/usb_cam/image_rect_color', Image, self.subscribe_image, queue_size=1)
		self.bridge = CvBridge()
		rospy.loginfo("Initialising Rack detection")
		self.image_pub = rospy.Publisher('racks_from_image',Image,queue_size=1)
		self.coord_pub = rospy.Publisher('racks_pos',String,queue_size=1)
		self.image_pub_thresh = rospy.Publisher('image_thresh',Image,queue_size=1)
		#self.detect_image = np.array([])

	def subscribe_image(self,msg):
    		cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
		rospy.loginfo("Image Received")
		
		# COnverts to hsv inage
		img_hsv = cv2.cvtColor(cv_image,cv2.COLOR_BGR2HSV)
		img2 = cv2.GaussianBlur(img_hsv,(13,13),0)

		#Ranges for Red colour
		lower_red = np.array([0,80,100])
		upper_red = np.array([15,255,255])
		mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
		lower_red = np.array([165,80,100])
		upper_red = np.array([180,255,255])
		mask2 = cv2.inRange(img_hsv,lower_red,upper_red)
		
		# Filters red componenents
		mask_red = mask1+mask2
    		ret,img2 = cv2.threshold(img2,10,255,cv2.THRESH_BINARY_INV) # Getting all the values
		
		self.image_pub_thresh.publish(self.bridge.cv2_to_imgmsg(mask_red))	
		
		# Identifies contours in the image
		contours = image, contours, hierarchy = cv2.findContours(mask_red,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		contours_filtered = []
		for c in contours:
			# Find the area of an contour
			area = cv2.contourArea(c,False)
			# Filters contrours obtained due to noise			
			if(area>THRESH_AREA):
				# identifes bounding rectangles
				x,y,w,h = cv2.boundingRect(c)
				moment = math.pow(float(w)/h,2)
				# area moment analysis of the bounding rectangle to identify legs
				if ( moment < THRESH_MOMENT ):
					cv2.rectangle(cv_image,(x,y),(x+w,y+h),(0,255,0),2)
					contours_filtered.append(c)
					rospy.loginfo("Coordinates : (%d,%d)", (x+w/2),(y+h/2))
					
					self.coord_pub.publish("Coordinates : ("+str(x+w/2)+","+str(y+h/2)+")")

		#cv2.drawContours(cv_image, contours_filtered, -1, (0,255,0), 3)
		self.detect_image = cv_image
		self.publish()

	def publish(self):
		if self.detect_image is not np.array([]):
			self.image_pub.publish(self.bridge.cv2_to_imgmsg(self.detect_image))

rospy.init_node('rack_detect_node')
rc = rack_detect()
rate = rospy.Rate(10)
while not rospy.is_shutdown():
	#rc.publish()
	rate.sleep()
