import asyncio
import robomaster
from robomaster import robot, camera, conn
import time
from .base_model import BaseRobot
import threading
import weakref

CMD_CHASSIS_X_UP = "w"
CMD_CHASSIS_X_DOWN = "s"
CMD_CHASSIS_Y_UP = "d"
CMD_CHASSIS_Y_DOWN = "a"

CMD_GIMBAL = "gimbal"

class RoboEP(BaseRobot):
    def __init__(self, sn:str, ip:str = None) -> None:
        super().__init__()
        
        self.sn = sn
        self.ep_robot = None
        self.ep_chassis = None
        self.ep_gimbal = None
        self.ep_camera = None        
        
        self.hit = None
        self.distance = None
        self.image = None
        
        self.is_stream = False
        self.is_running = True
            
        # self._finalizer = weakref.finalize(self, self._cleanup)
        
        # self.initialize()
        
        asyncio.create_task(self.coroutine_start())    
        
        threading.Thread(target=self.video_stream , daemon=True).start()
        # asyncio.create_task(self.sender())
        # asyncio.create_task(self.receiver())
        # asyncio.create_task(self.update_state())
        # asyncio.create_task(self.video_stream())

    #             # self.initialize(),
    #             self.sender(),
    #             self.receiver(),
    #             self.update_state(),
    #             self.video_stream()         

    def destroy(self):
        self.is_running = False
        self.ep_robot.close()
        self.stop_stream()
                         
    async def initialize(self):
        self.ep_robot = robot.Robot()
        try:
            # for _ in range(3):
            self.ep_robot.initialize(conn_type='sta', sn= self.sn)
            self.ep_chassis = self.ep_robot.chassis
            self.ep_camera = self.ep_robot.camera
            self.ep_gimbal = self.ep_robot.gimbal
            
            # Add
            self.ep_robot.armor.set_hit_sensitivity(comp="all", sensitivity=100)
            self.ep_robot.armor.sub_hit_event(self.hit_callback)
            self.ep_robot.sensor.sub_distance(freq=20, callback=self.tof_callback)            
            
            self.start_stream()        
        
            await self.rep_queue.put(0)       
            
        except Exception as e:
            print("Init Exception! : ", e)
            await self.rep_queue.put(1)

    async def command(self, cmd):
        await self.cmd_queue.put(cmd)
    
    async def sender(self):
        while self.is_running:
            cmd = await self.cmd_queue.get()
            try:
                # if cmd == CMD_CHASSIS_X_UP:
                #     self.ep_chassis.move(x=0.3, y=0, z=0, xy_speed=3).wait_for_completed()
                #     # self.ep_chassis.drive_speed(x=1, y=0, z=0, timeout=2)
                    
                #     # self.ep_chassis.move(x=0.3, y=0, z=0, xy_speed=1)
                # elif cmd == CMD_CHASSIS_X_DOWN:
                #     # self.ep_chassis.move(x=-0.1, y=0, z=0, xy_speed=1).wait_for_completed()
                #     self.ep_chassis.move(x=-0.3, y=0, z=0, xy_speed=1).wait_for_completed()
                    
                # elif cmd == CMD_CHASSIS_Y_UP:
                #     self.ep_chassis.move(x=0, y=0.1, z=0, xy_speed=1).wait_for_completed()
                #     # self.ep_chassis.move(x=0, y=0.3, z=0, xy_speed=1)
                    
                # elif cmd == CMD_CHASSIS_Y_DOWN:
                #     self.ep_chassis.move(x=0, y=-0.1, z=0, xy_speed=1).wait_for_completed()
                #     # self.ep_chassis.move(x=0, y=-0.3, z=0, xy_speed=1)
                
                if cmd == "J" or cmd == "L" or cmd == "I" or cmd == "K":
                    
                    gimbal_movement = {
                        'J': (0, -15),
                        'L': (0, 15),
                        'I': (15, 0),
                        'K': (-15, 0),
                    }

                    pitch, yaw = gimbal_movement[cmd]


                    self.ep_gimbal.move(pitch=pitch, yaw=yaw).wait_for_completed()                
                    
                else:
                    body_movement = {
                        'W': (0.3, 0, 0),
                        'S': (-0.3, 0, 0),
                        'A': (0, -0.3, 0),
                        'D': (0, 0.3, 0),
                        'Q': (0, 0, 15),
                        'E': (0, 0, -15)
                    }
                    x, y, z = body_movement[cmd]

                    # if cmd == "Q" or cmd == "E":
                    #     self.angle += z
                    # else:
                    #     self.angle = 0

                    # self.ep_chassis.move(x=x, y=y, z=z, xy_speed=0.7, z_speed=30).wait_for_completed()                    
                    self.ep_chassis.move(x=x, y=y, z=z, xy_speed=0.7, z_speed=30)
                    
                await self.rep_queue.put(0)
                
            except:
                await self.rep_queue.put(1)
    
    
    async def receiver(self):
        pass
    
    async def update_state(self):
        pass
    
    def video_stream(self):
        while self.is_running:
            if self.is_stream:
                try:
                    self.image = self.ep_camera.read_cv2_image(strategy="newest")      
                        
                except:
                    print("Except!")
                    # asyncio.run(self.initialize())
                    # self.ep_camera = self.ep_robot.camera
                    # self.start_stream()   
                    # continue
        
    def start_stream(self):
        if not self.is_stream:
            self.ep_camera.start_video_stream(display=False, resolution=camera.STREAM_360P)
            self.is_stream = True
    
    def stop_stream(self):
        if self.is_stream:
            self.ep_camera.stop_video_stream()
            self.is_stream = False
    
    def hit_callback(self, sub_info):
        armor_id, hit_type = sub_info

        if armor_id == 1:
            self.hit = "back"
        
        elif armor_id == 2:
            self.hit = "front"

        elif armor_id == 3:
            self.hit = "left"

        elif armor_id == 4:
            self.hit = "right"
    
    def tof_callback(self, tof_info):
        # print(tof_info)
        # print(type(tof_info))
        self.distance = tof_info[0]
        
    async def coroutine_start(self):   
        self.async_tasks = [
                # self.initialize(),
                self.sender(),
                self.receiver(),
                self.update_state(),
                # self.video_stream()            
        ]

        await asyncio.gather(*self.async_tasks)
        
        # asyncio.gather(*self.async_tasks)
        
#     async def robot_close(self):
#         self.ep_robot.close()
        
        
#     def robot_command(self):
#         pass
    
#     async def robot_camera(self):
#         pass
    
#     async def robo_init(self):
#         await asyncio.gather(
#                         self.perform_task(1),
#                         self.perform_task(2),
#                         self.perform_task(3)
#                     )
        
#     async def perform_task(self, task_id):
#         print(f"{task_id} will perform")
#         total = 0
#         for i in range(101):
#             total += i
#             print(f"{self.obj_num} / {task_id} : total = {total}")
#             await asyncio.sleep(10 / 100)        
    
# async def roop_exe():
#     i = 1
#     while True:
#         print("while")
#         # await asyncio.gather(RoboEP(i).robo_init())
#         asyncio.create_task(RoboEP(i).robo_init())
#         await asyncio.sleep(1)
#         i += 1    
    

    
# if __name__ == "__main__":
#     asyncio.run(RoboEP("3JKCK980030EKR").robot_initialize())
    
    # asyncio.run(roop_exe())
    # i = 1
    # while True:
    #     print("while")
    #     asyncio.gather(RoboEP(i).robo_init())
    #     time.sleep(1)
    #     i += 1
        # robo_ep1 = RoboEP
        # robo_ep2 = RoboEP
        
        # asyncio.run(init())
    
    
    