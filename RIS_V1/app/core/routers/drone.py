from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, responses, status, Response
from ..models.tello import Tello
import json
from ..models.base_model import Control
from ..models.dict_scheduler import DictScheduler
from .response_format import ResponseFormat
import queue
import io
from starlette.responses import StreamingResponse
from .drone_command import *
import socket

router = APIRouter()

# drones = DictScheduler(timeout=3600, check_interval=60)
drones = {}

# drone_rep_queue = queue.Queue()

# drone_video_queue = queue.Queue(maxsize=1)


ip_table_dict = open("app/core/routers/drone_ip_table.json", 'r')
ip_table_dict = json.load(ip_table_dict)    


# cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# cmd_socket.bind(('0.0.0.0', 8889))
# state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# state_socket.bind(('0.0.0.0', 8890))





    
@router.post("/control/")
def control(request: Request, drone_control: Control):
    """드론 원격 제어를 위한 코드

    Args:
        drone_ip (str): 드론 IP
        cmd (str): 제어문
        description(str): 제어문 설명(옵션)

    Returns:
        _type_: _description_
    """
        
    print("### [DRONE] : " + str(drone_control))
    
    if drone_control.ip in drones:

        drones[drone_control.ip].command(DRONE_COMMAND)
        drones[drone_control.ip].command(drone_control.cmd)
        
        drone_rep = drones[drone_control.ip].drone_rep_queue.get()
        
        if drone_rep == 0:
            command, status_code = ResponseFormat.ok_command(drone_control.ip, drone_control.cmd)
            return Response(command, status_code)
        
        elif drone_rep == 1:
            command, status_code = ResponseFormat.err_command(drone_control.ip)
            return Response(command, status_code)
            
        else:
            command, status_code = ResponseFormat.err_except()
            return Response(command, status_code)
        
    else:
        if not drone_initialize(drone_control.ip):
            command, status_code = ResponseFormat.err_found(drone_control.ip)
            return Response(command, status_code)
        
        drones[drone_control.ip].command(DRONE_COMMAND)
        drones[drone_control.ip].command(drone_control.cmd)
        
        drone_rep = drones[drone_control.ip].drone_rep_queue.get()
        
        if drone_rep == 0:
            command, status_code = ResponseFormat.ok_command(drone_control.ip, drone_control.cmd)
            return Response(command, status_code)
        
        elif drone_rep == 1:
            command, status_code = ResponseFormat.err_command(drone_control.ip)
            return Response(command, status_code)
            
        else:
            command, status_code = ResponseFormat.err_except()
            return Response(command, status_code)         
    
    
    
@router.delete("/{drone_ip}")
def delete_drone(request: Request, drone_ip: str):
    if drone_ip in drones:
        
        del drones[drone_ip]
        content, status_code = ResponseFormat.ok_delete(drone_ip)
        return Response(content, status_code)
    
    else:
        content, status_code = ResponseFormat.err_found(drone_ip)
        return Response(content, status_code)        
    
@router.get("/video/{drone_ip}")
def stream_video(request: Request, drone_ip: str):
    
    if drone_ip in drones:
        try:
            frame = drones[drone_ip].drone_video_queue.get_nowait()
            return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
        
        except queue.Empty:
            content, status_code = ResponseFormat.err_stream(drone_ip)
            return Response(content, status_code)
        
    else:     
        if not drone_initialize(drone_ip):
            content, status_code = ResponseFormat.err_found(drone_ip)
            return Response(content, status_code)            
    
        try:        
            drones[drone_ip].command(DRONE_COMMAND)
            if drones[drone_ip].drone_rep_queue.get() == 1:
                content, status_code = ResponseFormat.err_command(drone_ip)
                return Response(content, status_code)                     

            drones[drone_ip].command(DRONE_STREAMON)
            drones[drone_ip].drone_rep_queue.get()
            
            frame = drones[drone_ip].drone_video_queue.get_nowait()
            
            return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
            
        except:
            content, status_code = ResponseFormat.err_found(drone_ip)
            return Response(content, status_code)
    
@router.get("/state/{drone_ip}")
def stream_video(request: Request, drone_ip: str):
    if drone_ip in drones:
        try:
            drones[drone_ip].command("command")
            drone_rep = drones[drone_ip].drone_rep_queue.get()            
            
            if drone_rep == 1:
                content, status_code = ResponseFormat.err_command(drone_ip)
                return Response(content, status_code)
            
            state = drones[drone_ip].state
            print(state)
            if not state:
                content, status_code = ResponseFormat.err_no_data(drone_ip)
                return Response(content, status_code)
            
            # return Response(ResponseFormat.ok_state(drone_ip, state))
            
            content, status_code = ResponseFormat.ok_state(drone_ip, state)
            return Response(content, status_code)            
            # return ResponseFormat.ok_state(drone_ip, state)
    
        except Exception as e:
            print(e)
            
            content, status_code = ResponseFormat.err_no_data(drone_ip)
            return Response(content, status_code)            
        
    else:     
        if not drone_initialize(drone_ip):
            content, status_code = ResponseFormat.err_found(drone_ip)
            return Response(content, status_code) 
    
        try:
            drones[drone_ip].command("command")
            drone_rep = drones[drone_ip].drone_rep_queue.get()            
            
            if drone_rep == 1:
                content, status_code = ResponseFormat.err_command(drone_ip)
                return Response(content, status_code)            
            
            state = drones[drone_ip].state
            
            if not state:
                content, status_code = ResponseFormat.err_no_data(drone_ip)
                return Response(content, status_code)                

            content, status_code = ResponseFormat.ok_state(drone_ip, state)
            return Response(content, status_code)
    
        except Exception as e:
            
            content, status_code = ResponseFormat.err_no_data(drone_ip)
            return Response(content, status_code)
    
def drone_initialize(_drone_ip) -> Tello:
    try:
        # drone_ip = ip_table_dict[_drone_id]["ip_address"]
                
    # except Exception as e:
    #     return False
    
    # drone_cmd_port = ip_table_dict[_drone_id]["ports"]["command"]
    # drone_state_port = ip_table_dict[_drone_id]["ports"]["state"]
    # drone_video_port = ip_table_dict[_drone_id]["ports"]["video"]
    
        drones[_drone_ip] = Tello(_drone_ip, _drone_ip, \
                    8889, 8890, 11111)
        return True
    except Exception as e:
        print(e)
        return False
    