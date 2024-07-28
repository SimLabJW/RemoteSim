from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
from copy import deepcopy
import json

class Mover(BehaviorModelExecutor) :
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
        if self._cur_state == "Move" :
            
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