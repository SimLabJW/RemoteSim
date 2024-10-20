from pydantic import BaseModel
from typing import Optional
from abc import ABC, abstractmethod
import asyncio
import queue

class Control(BaseModel):
    """ Robot Control : For Post

    Required Value: 
        id: str
        cmd: str
    
    Optional Value:
        description: str
    """
    
    ip: str
    cmd: str
    description: Optional[str]
    
class StateRequest(BaseModel):
    """ Request State From Unity

    Required Value: 
        id: str
        home: int
        store: int
        state: str 
    """
    
    id: str
    home: int
    store: int
    state: str
    
class BaseRobot(ABC):
    def __init__(self) -> None:
        super().__init__()
        
        self.cmd_queue = asyncio.Queue()
        # self.video_queue = asyncio.Queue(maxsize=1)
        # self.video_queue = queue.Queue(maxsize=1)
        self.rep_queue = asyncio.Queue()
        self.async_event = asyncio.Event()
        self.async_tasks = []

    # def __del__(self):
    #     print("Mother")
    
    def __del__(self):
        super().__del__()
        print("Mother")
    
    @abstractmethod
    async def initialize(self):
        pass
        
    @abstractmethod
    def command(self, cmd):
        pass
    
    @abstractmethod
    async def sender(self):
        pass
    
    @abstractmethod
    async def receiver(self):
        pass
    
    @abstractmethod
    async def update_state(self):
        pass
    
    @abstractmethod
    def video_stream(self):
        pass
    
    @abstractmethod
    def coroutine_start(self):
        pass
    
    @abstractmethod
    def destroy(self):
        pass
    
