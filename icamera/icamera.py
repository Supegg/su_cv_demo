
from enum import Enum
from threading import Thread
from queue import Queue, Empty


class TriggerMode(Enum):
    '''
    Free, 连续拉流\n
    Line1, 触发模式，下同\n
    Line2,\n
    Software,
    '''
    Free = 0
    Line1 = 1
    Line2 = 2
    Software = 3

class icamera(Thread):
    '''
    各类型摄像头基类\n
    继承Thread类\n
    Queue交换数据，也可以考虑用事件驱动\n
    如有必要，使用multiprocessing实现，以利用多核心处理器\n
    '''
    
    #设备枚举功能，各类型自定义
    # cameras = dict()
    # def enumCameras()

    def __init__(self, name, mode: TriggerMode = TriggerMode.Free) -> None:
        Thread.__init__(self)
        '''
        name, Camera's Name\n
        mode, TriggerMode
        '''
        self.name = name
        self.mode = mode
        
        self.imgFactory = Queue() # 图像缓存队列
        self.running = False

    def run(self): # start thread...
        '''
        main capture loop
        '''
        pass

    def close(self):
        '''
        dispose the camera & resources
        '''
        pass