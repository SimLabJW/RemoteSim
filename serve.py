import socket
import threading
import time
import signal
import os
from RobotController import *

class TCPServer:
    def __init__(self, host='0.0.0.0', ports=[11013, 11014]):
        self.robotcontroller = RobotController()
        self.connect_message = None
        self.sensor_message = None

        self.host = host
        self.ports = ports
        self.servers = []
        self.stop_event = threading.Event()
        self.remote_flag = False
        self.image_conn = None  # To hold the connection for image transfer
        self.image_conn_lock = threading.Lock()

        self.ep_robot = None  # 로봇을 나중에 초기화하기 위해 None으로 설정
        self.robotcamera = None
        self.robotsensor = None
        self.robots = {}  # 변경된 부분: 여러 로봇을 관리하기 위한 딕셔너리
        self.initialized_robots = set()  # 이미 초기화된 로봇을 추적하기 위한 집합
        self.init_lock = threading.Lock()  # 초기화에 사용할 락

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
            time.sleep(1)  # 1초마다 메시지 전송

    def send_image(self, robotcamera):
        with self.image_conn_lock:
            if self.image_conn:
                if robotcamera:
                    try:
                        image_data = robotcamera.read_cv2_image(strategy="newest")
                        img = cv2.resize(image_data, (480, 300))  # 해상도를 조정
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
                time.sleep(2)  # 재시도 전 대기 시간
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
                    if json_data[0] == 'Unity Start' or json_data[0] == 'Simulation':
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
                            # 로봇 초기화 작업을 별도의 스레드에서 실행
                            init_thread = threading.Thread(target=self.initialize_robot, args=(serial_number,))
                            init_thread.start()
                            init_thread.join()  # 초기화가 완료될 때까지 기다림
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

                elif port == 11014:  # 유니티로부터 명령을 전달 받음
                    if json_data[0] == 'Remote':
                        time.sleep(3)
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
            self.ep_robot.close()
        finally:
            if send_thread and send_thread.is_alive():
                stop_event.set()
                send_thread.join()
            if port == 11014:
                with threading.Lock():
                    self.image_conn = None
            conn.close()
            print(f"Client disconnected on port {port}: {addr}")
            self.ep_robot.close()


    def convert_image_to_bytes(self, image_data):
        success, encoded_image = cv2.imencode('.jpg', image_data)
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
                    json_data = json.loads(data)

                except json.JSONDecodeError as e:
                    print(f"JSON decode error in handle_commands: {e}")
                    continue

                if self.remote_flag and json_data[1] in ['W', 'S', 'A', 'D','Q', 'E']:
                    self.robomaster_move(json_data[1])  # 올바른 데이터 전달

                # if self.remote_flag and json_data[1] in ['Q', 'E']: #대가리 회전임
                #     self.robomaster_rotation(json_data[1])  # 올바른 데이터 전달

        except Exception as e:
            print(f"Exception in command handler: {e}")

    def robomaster_move(self, cmd):
        self.robotcontroller.Move(self.ep_robot, cmd)
        print(f"robomaster unity cmd : {cmd}")

    def robomaster_head_rotation(self, cmd):
        self.robotcontroller.Rotation(cmd)
        print(f"robomaster unity cmd : {cmd}")

    def start_server(self):
        signal.signal(signal.SIGINT, self.shutdown)
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

    def shutdown(self, signum, frame):
        print("Shutting down server...")
        self.stop_event.set()
        for server in self.servers:
            server.close()
        os._exit(0)

if __name__ == "__main__":
    ports = [11013, 11014]  # 필요한 포트를 추가
    tcp_server = TCPServer(ports=ports)
    tcp_server.start_server()
