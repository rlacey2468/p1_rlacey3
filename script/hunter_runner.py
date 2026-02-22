#!/usr/bin/env python3
import rospy
import random
import math
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill

#Algorithm
##Spawn Hunter
#Spawn Runner at random location
#Hunter follows runner, Runners angular velocity changes
#if distance is less than 1, kill runner
#respawn runner at random location

#Functions needed
#Respawn, hunter pose , runner pose 

class HunterRunner:
    def __init__(self):
        self.hx = self.hy = self.ht = None
        self.rx = self.ry = None

        self.hunter_pub = rospy.Publisher("/hunter/cmd_vel", Twist, queue_size=10)
        self.runner_pub = rospy.Publisher("/runner/cmd_vel", Twist, queue_size=10)

        rospy.Subscriber("/hunter/pose", Pose, self.hunter_cb)
        rospy.Subscriber("/runner/pose", Pose, self.runner_cb)

        rospy.wait_for_service("/spawn")
        rospy.wait_for_service("/kill")
        self.spawn_srv = rospy.ServiceProxy("/spawn", Spawn)
        self.kill_srv  = rospy.ServiceProxy("/kill", Kill)

        # clean
        for n in ["turtle1", "hunter", "runner"]:
            try:
                self.kill_srv(n)
            except:
                pass

        #spawn hunter/runner
        self.spawn_srv(2.0, 2.0, 0.0, "hunter")
        self.spawn_runner()

        self.omega = random.uniform(-1.0, 1.0)
        self.last_time = rospy.Time.now()
        self.last_respawn = rospy.Time.now()

    #callback functions
    def hunter_cb(self, msg):
        self.hx = msg.x
        self.hy = msg.y
        self.ht = msg.theta

    def runner_cb(self, msg):
        self.rx = msg.x
        self.ry = msg.y

    #spawn runner in random location
    def spawn_runner(self):
        try:
            self.kill_srv("runner")
        except:
            pass

        x = random.uniform(1.0, 10.0)
        y = random.uniform(1.0, 10.0)
        self.spawn_srv(x, y, 0.0, "runner")
        self.last_respawn = rospy.Time.now() 

    # keep angle between -pi and pi
    def angle_fix(self, a):
        while a > math.pi:
            a -= 2*math.pi
        while a < -math.pi:
            a += 2*math.pi
        return a

    def run(self):
        rate = rospy.Rate(30)

        while not rospy.is_shutdown():
            # runner always moves forward, omega changes every 2 sec
            if (rospy.Time.now() - self.last_time).to_sec() >= 2.0:
                self.omega = random.uniform(-1.0, 1.0)
                self.last_time = rospy.Time.now()
                rospy.loginfo("New angle velocity: %f", self.omega)

            r = Twist()
            r.linear.x = 1.0
            r.angular.z = self.omega
            self.runner_pub.publish(r)

            # hunter chases
            if self.hx is not None and self.rx is not None:
                dist_x = self.rx - self.hx
                dist_y = self.ry - self.hy
                dist = math.sqrt(dist_x*dist_x + dist_y*dist_y)
                
                #edit: respawn problem
                if dist < 1.0 and (rospy.Time.now() - self.last_respawn).to_sec() > 0.5:
                    self.hunter_pub.publish(Twist()) 
                    self.spawn_runner()
                    rate.sleep()
                    continue
                else:
                    target = math.atan2(dist_y, dist_x)
                    err = self.angle_fix(target - self.ht)

                    h = Twist()
                    # max speed 1.0
                    if dist > 1.0:
                        h.linear.x = 1.0
                    else:
                        h.linear.x = dist

                    h.angular.z = 4.0 * err
                    self.hunter_pub.publish(h)

            rate.sleep()

if __name__ == "__main__":
    rospy.init_node("hunter_runner")
    HunterRunner().run()