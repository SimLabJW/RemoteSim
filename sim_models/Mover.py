from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
import json
from copy import deepcopy

class Mover(BehaviorModelExecutor) :
    def __init__(self,  instance_time, destruct_time, name, engine_name, conn):
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
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
        self.conn = conn

    def ext_trans(self, port, msg):
        # initializer -> mover
        if port == "init_done" :
            self.grid_scale = msg.retrieve()[0]
            self.start_point = msg.retrieve()[1]
            self.end_point = msg.retrieve()[2]
            self.key_dict = msg.retrieve()[3]
            self.current_position = deepcopy(self.start_point)
            self.moving_log.append(self.start_point)

            self._cur_state = "Wait"

        # predictor -> mover
        elif port == "pred_done" :
            recommended_key = msg.retrieve()[0]
            if recommended_key == "None" :
                print("No recommended Route. Exit RoutingSim.")
                
                data = self.load_json_template()
                data['msg'] = "Finding Route Failed"
                self.conn.send(data)


            map_grid = [['.'] * self.grid_scale for _ in range(self.grid_scale)]
            if recommended_key != "Goal" :
                recommended_position = self.key_to_position(recommended_key, self.current_position)

                data = self.load_json_template()
                data['msg'] = "Input Next Command"
                data['nextRecommend'] = {'command' : recommended_key, 'location' : list(recommended_position)}
                self.conn.send(data)

                map_grid[recommended_position[1]][recommended_position[0]] = '+'
            map_grid[self.current_position[1]][self.current_position[0]] = 'P'
            for row in map_grid :
                print(' '.join(row))

            if recommended_key == "Goal" :
                print("Goal! Exit RoutingSim.")
                print(f"Your Moving Log : {self.moving_log}")

                data = self.load_json_template()
                data['msg'] = "Goal!"
                data['movingLog'] = list(self.moving_log)
                self.conn.send(data)

            self._cur_state = "Move"

    
    def output(self):
        # if self._cur_state == "Move" :
        # 움직이는거 만들어야함. wasd 키 입력받게 하기
        # 움직인 위치를 moving_log에 넣고, predictor 모델에 전해주기

        if self._cur_state == "Move" :
            # input_key = input("Enter Moving Direction (w, a, s, d) : ")
            
            input_key = self.conn.recv()
            print("mover input "+input_key)
            changed_input_key = self.key_dict.get(input_key)
            print("mover change input "+input_key)
            next_position = self.key_to_position(changed_input_key, self.current_position)
            print(f"Current Position : {self.current_position}, Next Position : {next_position}")
            while next_position[0] < 0 or next_position[1] < 0 :
                print(f"Move Failed")
                
                data = self.load_json_template()
                data['msg'] = "Move Failed. Input Again : "
                self.conn.send(data)

            if next_position == None :
                print(f"Next Position == None.\ninput_key = {input_key}, cur_position = {self.current_position}")
            
            else :
                self.current_position = next_position
                self.moving_log.append(next_position)
                msg = SysMessage(self.get_name(), "move_done")
                msg.insert(next_position)
                return msg
                
    def int_trans(self):
        self._cur_state = "Wait"
    

    def key_to_position(self,input_key, prev_pos) :
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
        
    def load_json_template(self) -> dict :
        data = {'msg' : "-", 'recommendPath' : "-", 'nextRecommend' : "-", 'movingLog' : "-"}
        return data
    
    def position_to_key(self, prev_pos, cur_pos) :
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