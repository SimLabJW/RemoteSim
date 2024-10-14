from datetime import datetime
import json
# from multi_robomaster import multi_robot
from robomaster import robot, camera, conn, armor

import sys
import time

class RobotController():
    def __init__(self): 
        self.distance = 0  # 초기 거리 값
        self.hit = "None"
        self.ep_robot = None
        
        self.ip_to_sn = {
        "192.168.50.31": "3JKCK2S00305WL",  # 집게 로봇
        "192.168.50.221": "3JKCK6U0030A6U", # 5층 로봇
        "192.168.50.39": "3JKCK980030EKR"   # 6층 로봇
        }

        self.pitch = 0
        self.yaw = 0
        self.angle = 0
        
    def Research_Device(self):
        self.ip_list = conn.scan_robot_ip_list(timeout=1)
        if self.ip_list:
            selected_ips = self.select_robot_ips(self.ip_list)
            robots = [{"name": f"robot_{self.ip_to_sn[ip][-4:]}", "sn": self.ip_to_sn[ip]} for ip in selected_ips if ip in self.ip_to_sn]
            
            device_connect = self.Device_Connect(robots)
            return device_connect
        else:
            print("No robots found.")

    def select_robot_ips(self, ip_list):

        return [ip_list[i] for i in range(len(ip_list))]

    def Device_Connect(self, robots):
        if robots:
            return robots
        else:
            return print("No valid robots selected.")

     ################################################       


    def Device_Camera(self, ep_robot):
        ep_camera = ep_robot.camera
        ep_camera.start_video_stream(display=False)
        return ep_camera

    def initialize_robot(self, sn):
        self.ep_robot = robot.Robot()
        self.ep_robot.initialize(conn_type="sta", sn=sn)
        self.ep_chassis = self.ep_robot.chassis
        self.ep_gimbal = self.ep_robot.gimbal

        return self.ep_robot

    
    def Device_Sensor(self, ep_robot):
        ep_robot.sensor.sub_distance(freq=1, callback=self.tof_callback)

    def Device_HitSensor(self, ep_robot):

        ep_robot.armor.set_hit_sensitivity(comp="all", sensitivity=5)
        ep_robot.armor.sub_hit_event(self.hit_callback)

    def get_latest_distance(self):
        return [{"timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "distance": self.distance}]
    
    def get_latest_hit(self):
        hit_info = self.hit
        self.hit = "None"
        return [{"timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "hit": hit_info}]
    
    ##################################################

    def tof_callback(self, sub_info):
        # ToF 센서로부터 거리를 업데이트
        self.distance = sub_info[0]

    def hit_callback(self, sub_info):
        # 로봇이 충격을 받을 때 호출
        armor_id, hit_type = sub_info

        if armor_id == 1:
            self.hit = "back"
        
        elif armor_id == 2:
            self.hit = "front"

        elif armor_id == 3:
            self.hit = "left"

        elif armor_id == 4:
            self.hit = "right"

        # else:
        #     self.hit = "None"

    ###############################################################################################

    def Move(self, ep_robot, key):
        
        try:
            # Define body movement based on key
            body_movement = {
                'W': (0.3, 0, 0),
                'S': (-0.3, 0, 0),
                'A': (0, -0.3, 0),
                'D': (0, 0.3, 0),
                'Q': (0, 0, 15),
                'E': (0, 0, -15)
            }
            x, y, z = body_movement[key]

            if key == "Q" or key == "E":
                self.angle += z
            else:
                self.angle = 0

            ep_robot.chassis.move(x=x, y=y, z=self.angle, xy_speed=0.7, z_speed=30).wait_for_completed()


        except KeyError:
            print(f"Invalid key: '{key}'. Terminating program.")
            sys.exit(1)  # 프로그램을 에러 코드와 함께 종료

    def Rotation(self,key):
        try:
            # Define gimbal movement based on key
            gimbal_movement = {
                'J': (0, -15),
                'L': (0, 15),
                'I': (15, 0),
                'K': (-15, 0),
            }

            pitch, yaw = gimbal_movement[key]


            self.ep_gimbal.move(pitch=pitch, yaw=yaw).wait_for_completed()

            

        except KeyError:
            print(f"Invalid key: '{key}'. Terminating program.")
            sys.exit(1)  # 프로그램을 에러 코드와 함께 종료
