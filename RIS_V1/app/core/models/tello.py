import socket
import time
import threading
import datetime
import queue
import cv2
import numpy as np
import av
# from .base_model import BaseRobot

class Tello:
    def __init__(self, drone_id, drone_ip, cmd_port, state_port, video_port) -> None:

        self.drone_id = drone_id
        self.drone_ip = drone_ip
        
        self.cmd_port, self.state_port, self.video_port = cmd_port, state_port, video_port
        
        # self._server_queue = _server_queue
        # self._video_queue = _video_queue
        
        self.drone_rep_queue = queue.Queue()

        self.drone_video_queue = queue.Queue(maxsize=1)
        
        # Set Cmd Socket -> UDP
        self.cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd_socket.bind(('', cmd_port))
        
        # Set State Socket -> UDP
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(('', state_port))
        
        # stream_url = f'udp://@{self.drone_ip}:{self.video_port}'
        self.stream_url = f'udp://@{self.drone_ip}:{self.video_port}'

        # 비디오 스트림을 열기
        # self.video_container = av.open(stream_url)             
        
        # self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.video_socket.bind(('', video_port))        
        
        self.cmd_queue, self.cmd_event = queue.Queue(), threading.Event()
        
        
        self.cmd_max_time_out = 5
        self.cmd_max_retry = 2
        
        self.cmd_buffer_size = 1024

        self.state = 0
        
        self.thread_start()
    
    def command(self, cmd):
        print(f"Command Line : {cmd}")
        self.cmd_queue.put(cmd)
        
    def sender(self):
        self.cmd_event.set()        # allow the first wait to proceed
        while True:
            self.cmd_event.wait()   # block second queue.get() until an event is set from receiver or failure set
            self.cmd_event.clear()  # block a timeout-enabled waiting
            cmd = self.cmd_queue.get()
            
            self.cmd_socket.sendto(cmd.encode('utf-8'), (self.drone_ip, self.cmd_port))
            cmd_ok = False
            
            # 명령을 보낸 후 Tello에서 응답이 올 때까지 대기
            for i in range(self.cmd_max_retry):
                if self.cmd_event.wait(timeout=self.cmd_max_time_out):
                    cmd_ok = True
                    break
                
                else:
                    print(f' # Sender : Failed to send command: "{cmd}", Failure sequence: {i+1}.')
                    self.cmd_socket.sendto(cmd.encode('utf-8'), (self.drone_ip, self.cmd_port))
                    
                    
            if cmd_ok:
                self.drone_rep_queue.put(0)
                print(f' # Sender : Success To Control "{cmd}".')
                
            else:
                self.cmd_queue = queue.Queue() # Queue 객체 초기화
                self.cmd_event.set() # The failure set
                print(f' # Sender : Stop retry: "{cmd}", Maximum re-tries: {self.cmd_max_retry}.')
                self.drone_rep_queue.put(1)
        
        
    def receiver(self):
        while True:
            bytes_, address = self.cmd_socket.recvfrom(self.cmd_buffer_size)
            
            if bytes_ == b'ok':
                self.cmd_event.set() # one command has been successfully executed. Begin new execution.
                
            else:
                print(f' $ Receiver : From Tello :: {bytes_.decode()}')
                self.drone_rep_queue.put(bytes_.decode())
  
    def update_state(self):     
        while True:
            bytes_, address = self.state_socket.recvfrom(1024)
            str_ = bytes_.decode()
            self.state = str_
            # print(f" % \033[33m{self.drone_id} - {address}\033[0m State Updater : From Tello :: {str_}")
                        
    def video_stream(self):
        video_container = av.open(self.stream_url)       
        for frame in video_container.decode(video=0):
            # PyAV 프레임을 numpy 배열로 변환
            img = frame.to_ndarray(format='bgr24')
            
            ret, buffer = cv2.imencode('.jpg', img)
            
            if ret:
                video_frame = buffer.tobytes()
                
                if self.drone_video_queue.full():
                    self.drone_video_queue.get()
                    self.drone_video_queue.put(video_frame)
                
                else:
                    self.drone_video_queue.put(video_frame)
            # else:
            #     self._video_frame = None
            
    def thread_start(self):
        print(f" @ {self.drone_ip} : Receiver Thread start.")
        threading.Thread(target=self.receiver, daemon=True).start()
        
        print(f" @ {self.drone_ip} : Sender Thread start.")
        threading.Thread(target=self.sender, daemon=True).start()
        
        print(f" @ {self.drone_ip} : Update State Thread start.")
        threading.Thread(target=self.update_state , daemon=True).start()
        
        print(f" @ {self.drone_ip} : Video Stream Thread start.")
        threading.Thread(target=self.video_stream , daemon=True).start()
        
        
        
            
        
    
        
        