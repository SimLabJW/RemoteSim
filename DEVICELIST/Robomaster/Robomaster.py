from robomaster import robot
from robomaster import camera
import sys

class Robomaster():
    def __init__(self) -> None:
        print("robomaster init")
        self.ep_robot = robot.Robot()
        self.ep_robot.initialize(conn_type="sta", sn="3JKCK980030EKR")
        self.ep_chassis = self.ep_robot.chassis
        self.ep_gimbal = self.ep_robot.gimbal
        self.ep_camera = self.ep_robot.camera

    def Move(self, key):
        try:
            # Define body movement based on key
            body_movement = {
                'W': (0.3, 0, 0),
                'S': (-0.3, 0, 0),
                'A': (0, -0.3, 0),
                'D': (0, 0.3, 0),
                'Q': (0, 0, 45),
                'E': (0, 0, -45)
            }
            x, y, z = body_movement[key]
            self.ep_chassis.move(x=x, y=y, z=z, xy_speed=0.7, z_speed=45).wait_for_completed()
        except KeyError:
            print(f"Invalid key: '{key}'. Terminating program.")
            sys.exit(1)  # 프로그램을 에러 코드와 함께 종료

    def Rotation(self,key):

        try:
            # Define gimbal movement based on key
            gimbal_movement = {
                'I': (30, 0),
                'K': (-30, 0),
                'J': (0, -30),
                'L': (0, 30)
            }

            pitch, yaw = gimbal_movement[key]
            self.ep_gimbal.move(pitch=pitch, yaw=yaw).wait_for_completed()
        except KeyError:
            print(f"Invalid key: '{key}'. Terminating program.")
            sys.exit(1)  # 프로그램을 에러 코드와 함께 종료

    def Camera_return(self):
        print("robomaster camera")
        self.ep_camera.start_video_stream(display=False)
    
        return self.ep_camera

        


