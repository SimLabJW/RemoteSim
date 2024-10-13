import socket
import threading
import time
import os
import json
from RobotController import *
import torch
import cv2
from datetime import datetime


class TCPServer:
    def __init__(self, host='0.0.0.0', ports=[11013,]):

        self.robotcontroller = RobotController()
        self.connect_message = None
        self.sensor_message = None

        self.host = host
        self.ports = ports
        self.servers = []
        self.stop_event = threading.Event()
        self.remote_flag = False

        self.unitysim_conn = None
        self.sim_conn = None 
        self.image_conn = None  

        self.image_conn_lock = threading.Lock()

        self.ep_robot = None  
        self.robotcamera = None
        self.robotsensor = None
        self.robots = {}  
        self.initialized_robots = set()  
        self.init_lock = threading.Lock()  

        self.confidence_threshold = 0.7
        # 모델 파일 경로 (best.pt 또는 last.pt)
        model_path = './new_v25_2/best.pt'  # 혹은 'last.pt'

        # YOLOv5 모델 로드
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)

        for port in self.ports:
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self.host, port))
                server.listen(5)
                self.servers.append(server)
                print(f"Server is running on port {port}...")
            except socket.error as e:
                print(f"Error binding to port {port}: {e}")
                os._exit(1)

        

    def send_periodically(self, conn, message, stop_event):
        while not stop_event.is_set():
            if self.remote_flag:
                self.sensor_message = self.robotcontroller.get_latest_distance()
                message = json.dumps(self.sensor_message).encode()
            else:
                self.connect_message = self.robotcontroller.Research_Device()
                message = json.dumps(self.connect_message).encode()

            try:
                conn.sendall(message)
            except socket.error as e:
                print(f"Error sending message: {e}")
                break
            time.sleep(1) 

    def send_image(self, robotcamera):
        with self.image_conn_lock:
            if self.image_conn:
                if robotcamera:
                    try:
                        image_data = robotcamera.read_cv2_image(strategy="newest")
                        img = cv2.resize(image_data, (480, 300)) 
                        encoded_image = self.convert_image_to_bytes(img)
                        self.image_conn.sendall(encoded_image)
                    except Exception as e:
                        print(f"Failed to send image: {e}")
                        self.image_conn = None

    def initialize_robot(self, serial_number):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.init_lock:
                    if serial_number not in self.robots:
                        ep_robot = self.robotcontroller.initialize_robot(serial_number)
                        if ep_robot:
                            robotcamera = self.robotcontroller.Device_Camera(ep_robot)
                            robotsensor = self.robotcontroller.Device_Sensor(ep_robot)
                            self.robots[serial_number] = {
                                'robot': ep_robot,
                                'camera': robotcamera,
                                'sensor': robotsensor
                            }
                            self.initialized_robots.add(serial_number)
                            print(f"Successfully initialized robot with serial number: {serial_number}")
                            break
                        else:
                            print(f"Failed to initialize robot with serial number: {serial_number}")

                    if serial_number in self.robots:
                        self.ep_robot = self.robots[serial_number]['robot']
                        self.robotcamera = self.robots[serial_number]['camera']
                        self.robotsensor = self.robots[serial_number]['sensor']
                        break
            except socket.timeout:
                print(f"Attempt {attempt + 1}/{max_retries} - Socket timeout during robot initialization for serial number: {serial_number}")
                continue
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} - Error during robot initialization for serial number: {serial_number}: {e}")
                time.sleep(2)  
        else:
            print(f"Failed to initialize robot after {max_retries} attempts for serial number: {serial_number}")

    def handle_client(self, conn, addr, port):
        print(f"Client connected on port {port}: {addr}")
        stop_event = threading.Event()
        send_thread = None

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    data = data.decode()
                    json_data = json.loads(data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

                if port == 11013:
                    print(f"Received from {addr} on port {port}: {data}")
                    if json_data[0] == 'Unity Start':
                        self.remote_flag = False
                    
                        if send_thread and send_thread.is_alive():
                            stop_event.set()
                            send_thread.join()

                        stop_event.clear()
                        connect_m = self.robotcontroller.Research_Device()

                        if not connect_m or connect_m == "No robots found.":
                            connect_m = b"No robots found."
                        else:
                            connect_m = json.dumps(connect_m).encode()
                        send_thread = threading.Thread(target=self.send_periodically, args=(conn, connect_m, stop_event))
                        send_thread.start()

                    elif json_data[0] == 'Remote':
                        self.remote_flag = True
                        serial_number = json_data[1]

                        if serial_number not in self.initialized_robots:
                            init_thread = threading.Thread(target=self.initialize_robot, args=(serial_number,))
                            init_thread.start()
                            init_thread.join()  
                        else:
                            print(f"Robot with serial number {serial_number} already initialized.")
                            self.ep_robot = self.robots[serial_number]['robot']
                            self.robotcamera = self.robots[serial_number]['camera']
                            self.robotsensor = self.robots[serial_number]['sensor']

                        if send_thread and send_thread.is_alive():
                            stop_event.set()
                            send_thread.join()
                        stop_event.clear()
                        sensor_m = self.robotcontroller.get_latest_distance()

                        if not sensor_m:
                            sensor_m = b"No robots found."
                        else:
                            sensor_m = json.dumps(sensor_m).encode()
                        send_thread = threading.Thread(target=self.send_periodically, args=(conn, sensor_m, stop_event))
                        send_thread.start()

                elif port == 11014: 
                    if json_data[0] == 'Remote':
                        time.sleep(1)
                        print(f"Received from {addr} on port {port}: {data}")
                        with threading.Lock():
                            self.image_conn = conn

                        command_thread = threading.Thread(target=self.handle_commands, args=(conn,))
                        command_thread.start()

                        while True:
                            try:
                                self.send_image(self.robotcamera)

                            except Exception as e:
                                print(f"Exception keeping 11014 alive: {e}")
                                with threading.Lock():
                                    self.image_conn = None
                                break
                    else:
                        pass

        except Exception as e:
            print(f"Exception in client handler on port {port}: {e}")
            if self.ep_robot:
                self.ep_robot.close()
        finally:
            if send_thread and send_thread.is_alive():
                stop_event.set()
                send_thread.join()
            if port == 11014:
                with threading.Lock():
                    self.image_conn = None
            if self.ep_robot:
                self.ep_robot.close()
            conn.close()
            print(f"Client disconnected on port {port}: {addr}")

    # def convert_image_to_bytes(self, image_data): yolov5 없이 사용할때
    #     success, encoded_image = cv2.imencode('.jpg', image_data)
    #     if success:
    #         return encoded_image.tobytes()
    #     else:
    #         return None
        
    def convert_image_to_bytes(self, image_data):
        # YOLO 모델에 전달할 원본 이미지 사용
        original_image = image_data.copy()
        
        # YOLOv5 모델에 원본 이미지 전달하여 객체 감지
        results = self.model(original_image)

        # 감지된 객체 중 confidence score가 0.7 이상인 것만 필터링
        results = results.pandas().xyxy[0]  # YOLOv5 결과를 판다스 DataFrame으로 변환
        filtered_results = results[results['confidence'] >= self.confidence_threshold]

        # 필터링된 결과를 기반으로 바운딩 박스 그리기
        for index, row in filtered_results.iterrows():
            # 좌표 추출
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            confidence = row['confidence']
            label = f"{row['name']} {confidence:.2f}"

            # 바운딩 박스와 라벨을 원본 이미지에 그리기
            cv2.rectangle(original_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(original_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # 원본 이미지에 바운딩 박스를 그린 후, 이를 JPEG 형식으로 인코딩
        success, encoded_image = cv2.imencode('.jpg', original_image)
        
        if success:
            return encoded_image.tobytes()
        else:
            return None

    def handle_commands(self, conn):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                data = data.decode()
                try:
                    current_time = datetime.now()
                    json_data = json.loads(data)
                     # 첫 번째 데이터 무시
                    if 'Item1' in json_data[1] and 'Item2' in json_data[1]:
                        command = json_data[1]['Item1']
                        date_time = json_data[1]['Item2']

                        received_time_obj = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f")  # 문자열을 datetime 객체로 변환

                        time_difference = current_time - received_time_obj  # 시간 차이 계산

                        print(f"Time difference: {time_difference.total_seconds()} seconds")

                        # 로봇 명령어 처리
                        if self.remote_flag and command in ['W', 'S', 'A', 'D', 'Q', 'E']:
                            self.robomaster_move(command) 

                        if self.remote_flag and command in ['J', 'L', 'I', 'K']:  # 대가리 회전
                            self.robomaster_head_rotation(command)

                except json.JSONDecodeError as e:
                    print(f"JSON decode error in handle_commands: {e}")
                    continue

        except Exception as e:
            print(f"Exception in command handler: {e}")

    def robomaster_move(self, cmd):
        self.robotcontroller.Move(self.ep_robot, cmd)

    def robomaster_head_rotation(self, cmd):
        self.robotcontroller.Rotation(cmd)

    def start_server(self):

        threads = []
        try:
            for i, server in enumerate(self.servers):
                thread = threading.Thread(target=self.accept_connections, args=(server, self.ports[i]))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            print("Server is shutting down.")
            for server in self.servers:
                server.close()
            os._exit(1)

    def accept_connections(self, server, port):
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr, port)).start()

if __name__ == "__main__":
    ports = [11013, 11014]  
    tcp_server = TCPServer(ports=ports)
    # tcp_server.start_server()

    server_thread = threading.Thread(target=tcp_server.start_server)
    server_thread.start()


    server_thread.join()




