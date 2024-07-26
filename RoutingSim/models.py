from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
import json
import heapq
from copy import deepcopy
import os, sys
import socket
import json

def key_to_position(input_key, prev_pos) :
    if input_key in ['front', 'back', 'left', 'right'] :
        x, y = prev_pos
        if input_key == 'front' : 
            y -= 1
        elif input_key == 'back' :
            y += 1
        elif input_key == 'left' :
            x -= 1
        elif input_key == 'right' :
            x += 1
        cur_pos = (x, y)
        return cur_pos 
    
    else : return None

def position_to_key(prev_pos, cur_pos) :
    dx = cur_pos[0] - prev_pos[0]
    dy = cur_pos[1] - prev_pos[1]
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    if abs_dx + abs_dy != 1 :
        return None
    else :
        if dx == 0 and dy == -1 :
            return 'front'
        elif dx == 0 and dy == 1 :
            return 'back'
        elif dx == 1 and dy == 0 :
            return 'right'
        elif dx == -1 and dy == 0 :
            return 'left'

def load_json_template() -> dict :
    data = {'msg' : "-", 'recommendPath' : "-", 'nextRecommend' : "-", 'movingLog' : "-"}
    return data

class initializer(BehaviorModelExecutor) :
    def __init__(self, instantiate_time, destruct_time, name, engine_name, config_file, server_file):
        BehaviorModelExecutor.__init__(self, instantiate_time, destruct_time, name, engine_name)
        self.init_state("Wait")
        self.insert_state("Wait", Infinite)
        self.insert_state("Init", 1)

        self.insert_input_port("start")
        self.insert_output_port("init_done")

        self.grid_scale = 3 # 사용자 입력 받도록 변경 가능함
        self.start_point = 0
        self.end_point = 0
        self.key_dict = {}
        self.config_file = config_file
        self.server_file = server_file
        self.host = ""
        self.port = 0
        self.client_socket = None


    def ext_trans(self, port, msg) :
        if port == "start" :
            print("Simulator Start")
            self._cur_state = "Init"
    
    def output(self) :
        if self._cur_state == "Init" :

            with open(self.config_file, 'r', encoding='utf-8') as f :
                self.key_dict = json.load(f)
            print(f"moving keywords : {self.key_dict}")

            with open(self.server_file, 'r', encoding='utf-8') as f :
                data = json.load(f)
                self.host = data["ip"]
                self.port = data["port"]

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)

            print(f"Server Open : {self.host}:{self.port}")

            client_socket, client_address = server_socket.accept()
            print(f"Client Connected : {client_address}")
            self.client_socket = client_socket

            
            #while self.grid_scale == 0 :
             #   try :
              #      self.grid_scale = int(input("Grid Scale (ex. 3): "))
               # except TypeError :
                #    print("Please enter the correct format.")
                 #   continue
            while self.start_point == 0 :                
                # input_data = input("Input Start Point x, y. (ex : 0, 0) : ")
                try : 
                    
                    data = load_json_template()
                    data['msg'] = "Input Start Point x, y. (ex : 0, 0)"
                    json_data = json.dumps(data).encode('utf-8')
                    self.client_socket.sendall(json_data)

                    input_data = self.client_socket.recv(1024).decode('utf-8')

                    if not input_data :
                        sys.exit()

                    x_str, y_str = input_data.split(',')
                    x = int(x_str.strip())
                    y = int(y_str.strip())

                    self.start_point = (x, y)
                except ValueError :
                    print("Please enter the correct format.")
                    continue
            while self.end_point == 0 :
                # input_data = input("Input End Point x, y. (ex : 2, 2) : ")
                try : 
                    
                    data = load_json_template()
                    data['msg'] = "Input End Point x, y. (ex : 2, 2)"
                    json_data = json.dumps(data).encode('utf-8')
                    self.client_socket.sendall(json_data)

                    input_data = self.client_socket.recv(1024).decode('utf-8')

                    if not input_data :
                        sys.exit()
                    
                    x_str, y_str = input_data.split(',')
                    x = int(x_str.strip())
                    y = int(y_str.strip())

                    self.end_point = (x, y)
                except ValueError :
                    print("Please enter the correct format.")
                    continue
                
            msg = SysMessage(self.get_name(), "init_done")
            msg.insert(self.grid_scale)
            msg.insert(self.start_point)
            msg.insert(self.end_point)
            msg.insert(self.key_dict)
            msg.insert(self.client_socket)
            return msg

    def int_trans(self):
        if self._cur_state == "Wait" :
            self._cur_state = "Wait"
        elif self._cur_state == "Init" :
            self._cur_state = "Wait"
        

class predictor(BehaviorModelExecutor) :
    def __init__(self, instantiate_time, destruct_time, name, engine_name):
        BehaviorModelExecutor.__init__(self, instantiate_time, destruct_time, name, engine_name)
        self.init_state("Wait")
        self.insert_state("Wait", Infinite)        
        self.insert_state("Predict", 1)

        self.insert_input_port("init_done")
        self.insert_input_port("move_done")
        self.insert_output_port("pred_done")

        self.grid_scale = 0 
        self.start_point = 0
        self.end_point = 0
        self.current_position = ()
        self.client_socket = None

        self.key_dict = {}
        self.distances = {}
        self.priority_queue = []
        self.recommend_path = []
        self.came_from = {}

        self.previous_position = ()





    def ext_trans(self, port, msg):
        # initializer -> predictor
        if port == "init_done" :
            self.grid_scale = msg.retrieve()[0] # int
            self.start_point = msg.retrieve()[1] # tuple (x, y)
            self.end_point = msg.retrieve()[2] # tuple (x, y)
            self.key_dict = msg.retrieve()[3] 
            self.client_socket = msg.retrieve()[4]
            self.distances = {(i, j) : float('inf') for i in range(self.grid_scale) for j in range(self.grid_scale)}
            self.distances[self.start_point] = 0
            self.current_position = deepcopy(self.start_point)
            self.priority_queue = [(0, self.start_point)]

            self._cur_state = "Predict"

        # mover -> predictor
        elif port == "move_done" :
            # 마지막 이동이 어디서 온건지 전달받음. 그걸 previous_position에 저장해야함
            # 마지막 갔던 위치로는 가지 않기 위함
            
            self.previous_position = deepcopy(self.current_position)
            self.current_position = msg.retrieve()[0]
            
            self._cur_state = "Predict"
        

    def output(self):
        if self._cur_state == "Predict" :
            # previos_position을 제외한 나머지 위치로의 이동을 해야함 (다익스트라)
            # 만약에, 마지막 이동이 recommend_path[0] 과 같을 경우 == 추천한 대로 움직였을 경우
            # 별다른 조치 없이 바로 다음 추천 위치를 mover에 전달함.
            # 마지막 이동이 recommend_path[0]과 다를 경우 == 추천한 대로 움직이지 않았을 경우
            # 새 루트를 짜줌
            msg = SysMessage(self.get_name(), "pred_done")
            print(f"previous_position : {self.previous_position}, current_position : {self.current_position}")
            print(f"recommend_path : {self.recommend_path}")
            

            if self.current_position == self.start_point or self.current_position != self.recommend_path[0] :
                print("dijkstra start")

                if self.current_position != self.start_point :
                    self.start_point = deepcopy(self.current_position)
                    self.distances = {(i, j) : float('inf') for i in range(self.grid_scale) for j in range(self.grid_scale)}
                    self.distances[self.current_position] = 0
                    self.priority_queue = [(0, self.current_position)]
                    self.recommend_path = []
                    self.came_from = {}

                while self.priority_queue:
                    current_distance, current_node = heapq.heappop(self.priority_queue)

                    if current_node == self.end_point : # end_point는 x, y로 구성
                        # 현재 노드가 도착 지점과 같으면
                        # 도착 지점까지 어떻게 이어졌는지 came_from 리스트에서 뽑으면서 저장함
                        self.recommend_path = []
                        while current_node in self.came_from :
                            self.recommend_path.append(current_node)
                            current_node = self.came_from[current_node]
                        
                        # self.recommend_path.append(self.start_point)
                        # 마지막에 뒤집어서 경로를 표현함
                        self.recommend_path.reverse()
                        # 시작 위치를 제외한 경로가 나와있는 상태
                        # 따라서, recommend_path[0]은 현 위치에서 추천하는 이동 위치
                        
                        data = load_json_template()
                        data['msg'] = "New Recommend Path"
                        data['recommendPath'] = list(self.recommend_path)
                        json_data = json.dumps(data).encode('utf-8')
                        self.client_socket.sendall(json_data)

                        msg = SysMessage(self.get_name(), "pred_done")
                        msg.insert(position_to_key(self.current_position, self.recommend_path[0]))
                        return msg

                    x, y = current_node
                    for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)] :
                        # 상, 하, 좌, 우
                        neighbor = (x + dx, y + dy)
                        if 0 <= neighbor[0] < self.grid_scale and 0 <= neighbor[1] < self.grid_scale:
                            # 이전에 온 곳으로는 이동하지 않는 로직
                            # if neighbor == self.previous_position:
                                # continue
                            new_distance = current_distance + 1
                            if new_distance < self.distances[neighbor] :
                                self.distances[neighbor] = new_distance
                                self.came_from[neighbor] = current_node
                                heapq.heappush(self.priority_queue, (new_distance, neighbor))

                msg.insert("None")
                return msg 
            
            if self.current_position == self.recommend_path[0] :
                del(self.recommend_path[0])
                print(f"new recommend path : {self.recommend_path}")
                if len(self.recommend_path) > 0 :
                    msg.insert(position_to_key(self.current_position, self.recommend_path[0]))
                else :
                    msg.insert("Goal")

                return msg
            
    
    def int_trans(self):
        self._cur_state = "Wait"

class mover(BehaviorModelExecutor) :
    def __init__(self, instantiate_time, destruct_time, name, engine_name):
        BehaviorModelExecutor.__init__(self, instantiate_time, destruct_time, name, engine_name)
        self.init_state("Wait")
        self.insert_state("Wait", Infinite)
        self.insert_state("Move", 1)

        self.insert_input_port("init_done")
        self.insert_input_port("pred_done")
        self.insert_output_port("move_done")

        self.current_position = ()
        self.moving_log = []
        
        self.grid_scale = 0 
        self.start_point = 0
        self.end_point = 0
        self.key_dict = {}
        self.client_socket = None

    def ext_trans(self, port, msg):
        # initializer -> mover
        if port == "init_done" :
            self.grid_scale = msg.retrieve()[0]
            self.start_point = msg.retrieve()[1]
            self.end_point = msg.retrieve()[2]
            self.key_dict = msg.retrieve()[3]
            self.client_socket = msg.retrieve()[4]
            self.current_position = deepcopy(self.start_point)
            self.moving_log.append(self.start_point)

            self._cur_state = "Wait"

        # predictor -> mover
        elif port == "pred_done" :
            recommended_key = msg.retrieve()[0]
            if recommended_key == "None" :
                print("No recommended Route. Exit RoutingSim.")
                
                data = load_json_template()
                data['msg'] = "Finding Route Failed"
                json_data = json.dumps(data).encode('utf-8')
                self.client_socket.sendall(json_data)

                sys.exit()

            # self.client_socket.sendall(recommended_key.encode('utf-8'))
            # 맵 그려줘야함. 이동 할 수 있는 곳은 '.' 으로 표시, 추천 경로는 '+' 로 표시, 현위치는 P로 표시
            # 입력, 저장하는 좌표는 xy 좌표. 
            os.system('cls')
            map_grid = [['.'] * self.grid_scale for _ in range(self.grid_scale)]
            if recommended_key != "Goal" :
                recommended_position = key_to_position(recommended_key, self.current_position)

                data = load_json_template()
                data['msg'] = "Input Next Command"
                data['nextRecommend'] = {'command' : recommended_key, 'location' : list(recommended_position)}
                json_data = json.dumps(data).encode('utf-8')
                self.client_socket.sendall(json_data)

                map_grid[recommended_position[1]][recommended_position[0]] = '+'
            map_grid[self.current_position[1]][self.current_position[0]] = 'P'
            for row in map_grid :
                print(' '.join(row))

            if recommended_key == "Goal" :
                print("Goal! Exit RoutingSim.")
                print(f"Your Moving Log : {self.moving_log}")

                data = load_json_template()
                data['msg'] = "Goal!"
                data['movingLog'] = list(self.moving_log)
                json_data = json.dumps(data).encode('utf-8')
                self.client_socket.sendall(json_data)

                sys.exit()

            self._cur_state = "Move"

    
    def output(self):
        # if self._cur_state == "Move" :
        # 움직이는거 만들어야함. wasd 키 입력받게 하기
        # 움직인 위치를 moving_log에 넣고, predictor 모델에 전해주기

        if self._cur_state == "Move" :
            # input_key = input("Enter Moving Direction (w, a, s, d) : ")
            
            input_key = self.client_socket.recv(1024).decode('utf-8')
            changed_input_key = self.key_dict.get(input_key)
            next_position = key_to_position(changed_input_key, self.current_position)
            print(f"Current Position : {self.current_position}, Next Position : {next_position}")
            while next_position[0] < 0 or next_position[1] < 0 :
                print(f"Move Failed")
                
                data = load_json_template()
                data['msg'] = "Move Failed. Input Again : "
                json_data = json.dumps(data).encode('utf-8')
                self.client_socket.sendall(json_data)

            if next_position == None :
                print(f"Next Position == None.\ninput_key = {input_key}, cur_position = {self.current_position}")
                sys.exit()
            
            else :
                self.current_position = next_position
                self.moving_log.append(next_position)
                msg = SysMessage(self.get_name(), "move_done")
                msg.insert(next_position)
                return msg
                
    def int_trans(self):
        self._cur_state = "Wait"
    