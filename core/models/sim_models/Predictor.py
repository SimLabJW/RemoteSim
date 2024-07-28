from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
from copy import deepcopy
import heapq
import json

class Predictor(BehaviorModelExecutor) :
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
