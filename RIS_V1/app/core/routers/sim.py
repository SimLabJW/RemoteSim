from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, responses, status
from typing import List
from ..models.simulator import Simulator
import json
import queue
import threading
from ..models.base_model import StateRequest


router = APIRouter()

sim_send_queue = queue.Queue()
sim_recv_queue = queue.Queue()
sim_event = threading.Event()


sim = Simulator(sim_send_queue, sim_recv_queue, sim_event)
sim_flag = False
sim.engine_thread_start()

@router.post("/state/")
def control(request: Request, state_request: List[StateRequest]):
    
    req_tolist = [dict(req) for req in state_request]
    # print(req_tolist)
    sim_send_queue.put(req_tolist)
    
    sim_event.wait()
    sim_event.clear()
    
        
    state_response = sim_recv_queue.get()
    # print("From Simulator : ", text)
    print("### [SIM] : " + str(state_response))
    
    return state_response
    
    
