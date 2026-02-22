#!/usr/bin/env python3
import rospy
import math
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import SetPen

#Algorithm:
# spawn turtle
# Go to start positon
# put down pen
# Draw first letter
# pick up pen
# make a gap 
# go to positon for next letter
# put down pen
# draw next letter
# end

#Functions Needed:
# pen up, pen down, go_to, rotate
#edit: added write letter function
#edit: no need for rotate function
#edit: added angle wrap function 

#helper function
# keeps angle between -pi and pi
def angle_wrap(a):
    while a > math.pi:  a -= 2.0*math.pi
    while a < -math.pi: a += 2.0*math.pi
    return a

class TurtleWriter:
    def __init__(self):
        self.pose = None

        self.pub = rospy.Publisher("/turtle1/cmd_vel", Twist, queue_size=10)
        rospy.Subscriber("/turtle1/pose", Pose, self._pose_cb)

        rospy.wait_for_service("/turtle1/set_pen")
        self.set_pen_srv = rospy.ServiceProxy("/turtle1/set_pen", SetPen)

        # Wait until we have pose
        t0 = rospy.Time.now()
        while self.pose is None and (rospy.Time.now() - t0).to_sec() < 2.0 and not rospy.is_shutdown():
            rospy.sleep(0.05)

    def _pose_cb(self, msg):
        self.pose = msg

    #pen mechanics
    def pen_up(self, width=3):
        self.set_pen_srv(0, 0, 0, width, 1)

    def pen_down(self, width=3):
        self.set_pen_srv(0, 0, 0, width, 0)

    def stop(self):
        self.pub.publish(Twist())


    #go to function, utilizes position
    #edit: problem with driving straight
    #edit: fixed
    def go_to(self, x, y, v_max=1.2, w_max=2.0, tolerance=0.05, timeout=8.0):
        start = rospy.Time.now()
        rate = rospy.Rate(60)

        while not rospy.is_shutdown():
            if (rospy.Time.now() - start).to_sec() > timeout:
                break

            dist_x = x - self.pose.x
            dist_y = y - self.pose.y
            dist = math.sqrt(dist_x*dist_x + dist_y*dist_y)
            if dist < tolerance:
                break

            target = math.atan2(dist_y, dist_x)
            angle_err = angle_wrap(target - self.pose.theta)

            movement = Twist()
            movement.angular.z = max(-w_max, min(w_max, 6.0 * angle_err))

            #don't drive forward unless mostly facing target
            if abs(angle_err) > 0.25:
                movement.linear.x = 0.0
            else:
                movement.linear.x = min(v_max, 1.2 * dist)

            self.pub.publish(movement)
            rate.sleep()

        self.stop()

    #write letter:
        #X starts, Y  starts, width and height
    def write_letter(self, letter, x_0, y_0, w, h):
        # letter R
        if letter == 'R':
            strokes = [
                (0,0,2), (1,0,0),      # left bar
                (0,0,2), (1,1,2),      # top bar
                (1,1,1), (1,0,1),      # mid bar
                (1,1,0)                # diagonal leg
            ]
        #letter L
        elif letter == 'L':
            strokes = [
                (0,0,2), (1,0,0),      # left bar 
                (1,1,0)                # bottom bar
            ]

        for (pen, xx, yy) in strokes:
            if pen:
                self.pen_down()
            else:
                self.pen_up()

            x = x_0 + xx * w
            y = y_0 + yy * h / 2.0
            self.go_to(x, y)

        self.pen_up()

if __name__ == "__main__":
    rospy.init_node("initials_draw")
    tw = TurtleWriter()

    tw.pen_up()

    start_x, start_y = 2.0, 2.0
    letter_a = 1.8
    letter_b = 2.0 * letter_a
    gap = 1.2

    tw.go_to(start_x, start_y)
    tw.write_letter('R', start_x, start_y, letter_a, letter_b)

    tw.go_to(start_x + letter_a + gap, start_y)
    tw.write_letter('L', start_x + letter_a + gap, start_y, letter_a, letter_b)

    tw.stop()