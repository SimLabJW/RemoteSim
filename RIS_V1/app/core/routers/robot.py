from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, responses, status, Response
from typing import List
import json
import queue
import threading
import asyncio
from robomaster import conn
import time
from datetime import datetime
import io
import base64
from starlette.responses import StreamingResponse
import cv2
import gc

from ..models.robo_ep import RoboEP
from ..models.base_model import Control
from .response_format import ResponseFormat



router = APIRouter()

robots = {}

robot_ip_table = open("app/core/routers/robot_ip_table.json", 'r')
robot_ip_table = json.load(robot_ip_table)

ip_dict = None

def robot_scan():
    global ip_dict
    # while True:
    print(" * Robot Scanning... " + datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
    ip_dict = conn.scan_robot_ip_list(timeout=1)
    # ip_dict = conn.scan_robot_ip_list()
        # time.sleep(10)

# threading.Thread(target=robot_scan, daemon=True).start()

# async def robot_scan():
#     global ip_dict
#     while True:
#         ip_dict = conn.scan_robot_ip_list(timeout=0.5)
#         await asyncio.sleep(10)
        
# asyncio.create_task(robot_scan())

@router.post("/control/")
async def control(request: Request, robot_control: Control):
    print("### [ROBOT] : " + str(robot_control))
    
    
    if robot_control.ip in robots:
        await robots[robot_control.ip].command(robot_control.cmd)
        
        robot_rep = await robots[robot_control.ip].rep_queue.get()
    
        if robot_rep == 0:
            content, status_code = ResponseFormat.ok_command(robot_control.ip, robot_control.cmd)
            return Response(content, status_code)
        
        elif robot_rep == 1:
            content, status_code = ResponseFormat.err_command(robot_control.ip)
            return Response(content, status_code)            
            
        else:
            content, status_code = ResponseFormat.err_except()
            return Response(content, status_code)
    
    else:
        if not robot_initialize(robot_control.ip):
            content, status_code = ResponseFormat.err_found(robot_control.ip)
            return Response(content, status_code)            
        
        # 로봇 수신 가능 확인
        await robots[robot_control.ip].initialize()
                
        if await robots[robot_control.ip].rep_queue.get() == 1:
            robot_destroy(robot_control.ip)
            
            content, status_code = ResponseFormat.err_command(robot_control.ip)
            return Response(content, status_code)               
        
        await robots[robot_control.ip].command(robot_control.cmd)
        
        robot_rep = await robots[robot_control.ip].rep_queue.get()
    
        if robot_rep == 0:
            content, status_code = ResponseFormat.ok_command(robot_control.ip, robot_control.cmd)
            return Response(content, status_code)
        
        elif robot_rep == 1:
            content, status_code = ResponseFormat.err_command(robot_control.ip)
            return Response(content, status_code)           
            
        else:
            content, status_code = ResponseFormat.err_except()
            return Response(content, status_code)                       
              
@router.get("/control")
async def control_ip(request: Request, robot_ip:str, cmd:str):
    
    if robot_ip in robots:
        await robots[robot_ip].command(cmd)
        
        robot_rep = await robots[robot_ip].rep_queue.get()
    
        if robot_rep == 0:
            content, status_code = ResponseFormat.ok_command(robot_ip, cmd)
            return Response(content, status_code)
        
        elif robot_rep == 1:
            content, status_code = ResponseFormat.err_command(robot_ip)
            return Response(content, status_code)           
            
        else:
            content, status_code = ResponseFormat.err_except()
            return Response(content, status_code) 
    else:
        if not robot_initialize(robot_ip):
            
            content, status_code = ResponseFormat.err_found(robot_ip)
            return Response(content, status_code)             
        
        # 로봇 수신 가능 확인
        await robots[robot_ip].initialize()
                
        if await robots[robot_ip].rep_queue.get() == 1:
            robot_destroy(robot_ip)
            
            content, status_code = ResponseFormat.err_command(robot_ip)
            return Response(content, status_code)             
        
        await robots[robot_ip].command(cmd)
        
        robot_rep = await robots[robot_ip].rep_queue.get()
    
        if robot_rep == 0:
            content, status_code = ResponseFormat.ok_command(robot_ip, cmd)
            return Response(content, status_code)
        
        elif robot_rep == 1:
            content, status_code = ResponseFormat.err_command(robot_ip)
            return Response(content, status_code)           
            
        else:
            content, status_code = ResponseFormat.err_except()
            return Response(content, status_code) 
      
@router.get("/scan/")
async def scan(request: Request):
    robot_scan()
    if ip_dict:
        content, status_code = ResponseFormat.ok_scan(ip_dict)
        return Response(content, status_code)
    
    else:
        content, status_code = ResponseFormat.err_no_data(ip_dict)
        return Response(content, status_code)

# @router.get("/info")
# async def info(request: Request, robot_ip: str):
#     if robot_ip in robots:
#         if not robots[robot_ip].is_stream:
#             content, status_code = ResponseFormat.err_stream(robot_ip)
#             return Response(content, status_code)            
        
#         else:
#             try:
#                 # image_data = robots[robot_sn].video_queue.get()
#                 image_data = base64.b64encode(robots[robot_ip].video_queue.get())
#                 # decode_data = base64.b64encode(image_data)
#                 # print(image_data)
#             except:
#                 content, status_code = ResponseFormat.err_no_data(robot_ip)
#                 return Response(content, status_code)                 
            
#             content, status_code = ResponseFormat.ok_info(id= robot_ip, time= datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),\
#                 imageData= image_data, distance= robots[robot_ip].distance)
            
#             return Response(content, status_code)
            
#     else:
#         content, status_code = ResponseFormat.err_found(robot_ip)
#         return Response(content, status_code)

@router.get("/info")
async def info(request: Request, robot_ip: str):
    if robot_ip in robots:        
        content, status_code = ResponseFormat.ok_info(id= robot_ip,\
            hit= robots[robot_ip].hit, distance= robots[robot_ip].distance)
        
        return Response(content, status_code)
            
    else:
        if not robot_initialize(robot_ip):
            content, status_code = ResponseFormat.err_found(robot_ip)
            return Response(content, status_code)          
        
        
        await robots[robot_ip].initialize()
                
        if await robots[robot_ip].rep_queue.get() == 1:
            robot_destroy(robot_ip)
            content, status_code = ResponseFormat.err_command(robot_ip)
            return Response(content, status_code)        
        
        
        try:
            content, status_code = ResponseFormat.ok_info(id= robot_ip,\
            hit= robots[robot_ip].hit, distance= robots[robot_ip].distance)
            return Response(content, status_code)
            
        except:
            content, status_code = ResponseFormat.err_no_data(robot_ip)
            return Response(content, status_code)
     
@router.get("/video")
async def stream_video(request: Request, robot_ip: str):
    if robot_ip in robots:
        try:
            # frame = robots[robot_sn].video_queue.get_nowait()
            frame = robots[robot_ip].image
            # print(robots[robot_sn].image)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            
            if ret:
                video_frame = buffer.tobytes()  
                return StreamingResponse(io.BytesIO(video_frame), media_type="image/jpeg")
            else:
                content, status_code = ResponseFormat.err_convert()
                return Response(content, status_code)
        
        # except queue.Empty:
        except Exception:
            content, status_code = ResponseFormat.err_no_data(robot_ip)
            return Response(content, status_code)            
        
    else:     
        if not robot_initialize(robot_ip):
            content, status_code = ResponseFormat.err_found(robot_ip)
            return Response(content, status_code)
        
        await robots[robot_ip].initialize()
                
        if await robots[robot_ip].rep_queue.get() == 1:
            robot_destroy(robot_ip)
            content, status_code = ResponseFormat.err_command(robot_ip)
            return Response(content, status_code)            
        
        try:                    
            # frame = robots[robot_sn].video_queue.get_nowait()
            frame = robots[robot_ip].image
            ret, buffer = cv2.imencode('.jpg', frame)
            
            if ret:
                video_frame = buffer.tobytes()  
                return StreamingResponse(io.BytesIO(video_frame), media_type="image/jpeg")
            else:
                content, status_code = ResponseFormat.err_convert()
                return Response(content, status_code)                
            
        # except queue.Empty:
        except Exception:
            content, status_code = ResponseFormat.err_no_data(robot_ip)
            return Response(content, status_code)            
            
        # return Response(content= "임시 에러", status_code=500)
     
     
@router.delete("/{robot_ip}")
async def control(request: Request, robot_ip: str):
    
    if robot_ip in robots:
        
        robot_destroy(robot_ip)
        
        content, status_code = ResponseFormat.ok_delete(robot_ip)
        return Response(content, status_code)
    
    else:
        content, status_code = ResponseFormat.err_found(robot_ip)
        return Response(content, status_code)

def robot_initialize(_robot_ip) -> RoboEP:
    # try:
    #     robot_ip = robot_ip_table[_robot_sn]["ip_address"]
                
    # except Exception as e:
    #     return False
    
    # robot_sn = robot_ip_table[_robot_sn]["sn"]
    try:
        # robots[_robot_ip] = RoboEP(ip_dict[_robot_ip])     
        
        if _robot_ip == "192.168.50.39":
            sn = "3JKCK980030EKR"
        elif _robot_ip == "192.168.50.31":
            sn = "3JKCK2S00305WL"
           
        robots[_robot_ip] = RoboEP(sn)        
        # 3JKCK980030EKR
        return True
    
    except Exception as e:
        print(e)
        return False

def robot_destroy(_robot_ip) -> bool:
    try:
        robots[_robot_ip].destroy()
        del robots[_robot_ip]
    
        return True
    
    except:
        return False
        
        
        