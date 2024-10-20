from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
from .device_info import DRONE, CAR, TRANSITIONS
import random

class ScenarioGenerator(BehaviorModelExecutor):
    def __init__(self, instance_time, destruct_time, name, engine_name):
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        
        self.init_state("IDLE")
        self.insert_state("IDLE", Infinite)
        self.insert_state("PROCESSING", 1)

        self.insert_input_port("generate")
        self.insert_output_port("fin")

    def ext_trans(self, port, msg):
        if port == "generate":
            self.data_msg = msg.retrieve()[0]
            self._cur_state = "PROCESSING"

    def output(self):
        if self._cur_state == "PROCESSING":
            random_data = self.data_msg

            for rd in random_data:
                if rd['state'] == "None":
                    rd['state'] = "STAY"
                else:
                    self.transition_state(rd)

            msg = SysMessage(self.get_name(), "fin")
            msg.insert(random_data)
            # print(" + ", random_data)
            return msg

    def int_trans(self):
        if self._cur_state == "PROCESSING":
            self._cur_state = "IDLE"

    def transition_state(self, device):
        current_state = device['state']
        if current_state not in TRANSITIONS:
            return

        possible_states = list(TRANSITIONS[current_state].keys())
        weights = list(TRANSITIONS[current_state].values())
        selected_state = random.choices(possible_states, weights)[0]
        
        # rand_num = random.randint(1, 101)
        
        # if rand_num < 96:
        #     selected_state = "DELIVERY"
            
        # elif rand_num >= 96 and rand_num <= 98:
        #     selected_state = "ACCIDENT"
            
        # else:
        #     selected_state = "CANCEL"
        

        if current_state == "ACCIDENT":
            device['state'] = "ACCIDENT"
            return  # ACCIDENT 상태에서 다른 상태로 전환 불가

        if current_state == "DELIVERY":
            if selected_state == "ACCIDENT":
                self.handle_accident_state(device)
            elif selected_state == "CANCEL":
                device['state'] = 'CANCEL'
                device['home'] = 0
                device['store'] = 0
                
            else:
                device['state'] = "DELIVERY"  # 유지
                return  # 상태 유지, 변경하지 않음
            
        elif current_state == "STAY":
            if selected_state == "DELIVERY":
                if device['home'] == 0 and device['store'] == 0:
                    numbers = random.sample(range(1, 67), 2)
                    device['home'] = numbers[0]
                    device['store'] = numbers[1]

                    device['state'] = "DELIVERY"

    def handle_accident_state(self, accident_device):
        stay_devices = [d for d in self.data_msg if d['state'] == 'STAY']
        if stay_devices:
            stay_device = random.choice(stay_devices)
            stay_device['home'] = accident_device['home']
            stay_device['store'] = accident_device['store']
            stay_device['state'] = 'DELIVERY'