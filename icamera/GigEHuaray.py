if __name__ == '__main__': # this isn't the Way
    from ImageConvert import *
    from MVSDK import *
    from icamera import *
else:
    from .ImageConvert import *
    from .MVSDK import *    
    from .icamera import *
import time
import numpy
import cv2 as cv
import gc
import os
from queue import Queue, Empty


class GigEHuaray(icamera):
    '''
    open/start
    自由拉流/软/硬触发
    拉流
        while检测是否停止
    close
    '''
    cameras = dict()  # key=name

    # 枚举相机
    # enumerate camera
    def enumCameras():
        # 获取系统单例
        # get system instance
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if (nRet != 0):
            print("getSystemInstance fail!")
            return None

        # 发现相机
        # discover camera
        cameraList = pointer(GENICAM_Camera())
        cameraCnt = c_uint()
        nRet = system.contents.discovery(system, byref(cameraList), byref(
            cameraCnt), c_int(GENICAM_EProtocolType.typeAll))
        if (nRet != 0):
            print("discovery fail!")
            return None
        elif cameraCnt.value < 1:
            print("discovery no camera!")
            return None
        else:
            print("cameraCnt: " + str(cameraCnt.value))
            for i in range(cameraCnt.value):
                camera = cameraList[i]
                GigEHuaray.cameras[camera.getName(camera).decode()] = camera
            return cameraCnt.value

    def __init__(self, name, mode: TriggerMode = TriggerMode.Free) -> None:
        super().__init__(name, mode)
        self.camera = GigEHuaray.cameras.get(name)  # None if not found

        self.g_cameraStatusUserInfo = b"statusInfo"
        self.connectCallBackFuncEx = connectCallBackEx(self.deviceLinkNotify)
        
    # 取流回调函数Ex
    # grabbing callback function with userInfo parameter
    def onGetFrameEx(self, frame, userInfo):
        if not self.running:
            return

        nRet = frame.contents.valid(frame)
        if ( nRet != 0):
            print("frame is invalid!")
            # 释放驱动图像缓存资源
            # release frame resource before return
            frame.contents.release(frame)
            return         
    
        # print("BlockId = %d userInfo = %s"  %(frame.contents.getBlockId(frame), c_char_p(userInfo).value))

        # 给转码所需的参数赋值
        # fill conversion parameter
        imageParams = IMGCNV_SOpenParam()
        imageParams.dataSize    = frame.contents.getImageSize(frame)
        imageParams.height      = frame.contents.getImageHeight(frame)
        imageParams.width       = frame.contents.getImageWidth(frame)
        imageParams.paddingX    = frame.contents.getImagePaddingX(frame)
        imageParams.paddingY    = frame.contents.getImagePaddingY(frame)
        imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

        # 将裸数据图像拷出
        # copy image data out from frame
        imageBuff = frame.contents.getImage(frame)
        userBuff = c_buffer(b'\0', imageParams.dataSize)
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

        # 释放驱动图像缓存资源
        # release frame resource at the end of use
        frame.contents.release(frame)

        # 如果图像格式是 Mono8 直接使用
        # no format conversion required for Mono8
        if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
            grayByteArray = bytearray(userBuff)
            cvImage = numpy.array(grayByteArray).reshape(imageParams.height, imageParams.width)
        else:
            # 转码 => BGR24
            # convert to BGR24
            rgbSize = c_int()
            rgbBuff = c_buffer(b'\0', imageParams.height * imageParams.width * 3)

            nRet = IMGCNV_ConvertToBGR24(cast(userBuff, c_void_p), \
                                        byref(imageParams), \
                                        cast(rgbBuff, c_void_p), \
                                        byref(rgbSize))

            colorByteArray = bytearray(rgbBuff)
            cvImage = numpy.array(colorByteArray).reshape(imageParams.height, imageParams.width, 3)
    # --- end if ---

        # 加入队列
        self.imgFactory.put(cvImage)
        # cv.imshow('myWindow', cvImage)
        # cv.waitKey(1)
        gc.collect()


    # 相机连接状态回调函数
    # camera connection status change callback
    def deviceLinkNotify(self, connectArg, linkInfo):
        if ( EVType.offLine == connectArg.contents.m_event ):
            print("camera has off line, userInfo [%s]" %(c_char_p(linkInfo).value))
        elif ( EVType.onLine == connectArg.contents.m_event ):
            print("camera has on line, userInfo [%s]" %(c_char_p(linkInfo).value))
                

    # 注册相机连接状态回调
    # subscribe camera connection status change
    def subscribeCameraStatus(self, camera):
        # 注册上下线通知
        # subscribe connection status notify
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(camera)
        nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
        if ( nRet != 0):
            print("create eventSubscribe fail!")
            return -1
        
        nRet = eventSubscribe.contents.subscribeConnectArgsEx(eventSubscribe, self.connectCallBackFuncEx, self.g_cameraStatusUserInfo)
        if ( nRet != 0 ):
            print("subscribeConnectArgsEx fail!")
            # 释放相关资源
            # release subscribe resource before return
            eventSubscribe.contents.release(eventSubscribe)
            return -1  
        
        # 不再使用时，需释放相关资源
        # release subscribe resource at the end of use
        eventSubscribe.contents.release(eventSubscribe) 
        return 0

    # 反注册相机连接状态回调
    # unsubscribe camera connection status change
    def unsubscribeCameraStatus(self, camera):
        # 反注册上下线通知
        # unsubscribe connection status notify
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(camera)
        nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
        if ( nRet != 0):
            print("create eventSubscribe fail!")
            return -1
            
        nRet = eventSubscribe.contents.unsubscribeConnectArgsEx(eventSubscribe, self.connectCallBackFuncEx, self.g_cameraStatusUserInfo)
        if ( nRet != 0 ):
            print("unsubscribeConnectArgsEx fail!")
            # 释放相关资源
            # release subscribe resource before return
            eventSubscribe.contents.release(eventSubscribe)
            return -1
        
        # 不再使用时，需释放相关资源
        # release subscribe resource at the end of use
        eventSubscribe.contents.release(eventSubscribe)
        return 0   


    # 打开相机
    # open camera
    def openCamera(self, camera):
        # 连接相机
        # connect camera
        nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
        if ( nRet != 0 ):
            print("camera connect fail!")
            return -1
        else:
            print("camera connect success.")
    
        # 注册相机连接状态回调
        # subscribe camera connection status change
        nRet = self.subscribeCameraStatus(camera)
        if ( nRet != 0 ):
            print("subscribeCameraStatus fail!")
            return -1

        return 0


    # 关闭相机
    # close camera
    def closeCamera(self, camera):
        # 反注册相机连接状态回调
        # unsubscribe camera connection status change
        nRet = self.unsubscribeCameraStatus(camera)
        if ( nRet != 0 ):
            print("unsubscribeCameraStatus fail!")
            return -1
    
        # 断开相机
        # disconnect camera
        nRet = camera.disConnect(byref(camera))
        if ( nRet != 0 ):
            print("disConnect camera fail!")
            return -1
        
        return 0    

    def run(self):
        # 先实现自由拉流    
        # 显示相机信息
        camera = self.camera
        print("Key           = " + camera.getKey(camera).decode())
        print("Name          = " + camera.getName(camera).decode())
        print("vendor name   = " + camera.getVendorName(camera).decode())
        print("Model  name   = " + camera.getModelName(camera).decode())
        print("Serial number = " + camera.getSerialNumber(camera).decode())

        # 打开相机
        # open camera
        nRet = self.openCamera(camera)
        if ( nRet != 0 ):
            print("openCamera fail.")
            return -1
            
        # 创建流对象
        # create stream source object
        streamSourceInfo = GENICAM_StreamSourceInfo()
        streamSourceInfo.channelId = 0
        streamSourceInfo.pCamera = pointer(camera)
        
        streamSource = pointer(GENICAM_StreamSource())
        nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
        if ( nRet != 0 ):
            print("create StreamSource fail!")
            return -1
        
        # 通用属性设置:设置触发模式为off --根据属性类型，直接构造属性节点。如触发模式是 enumNode，构造enumNode节点
        # create corresponding property node according to the value type of property, here is enumNode
        # 自由拉流：TriggerMode 需为 off
        # set trigger mode to Off for continuously grabbing
        trigModeEnumNode = pointer(GENICAM_EnumNode())
        trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
        trigModeEnumNodeInfo.pCamera = pointer(camera)
        trigModeEnumNodeInfo.attrName = b"TriggerMode"
        nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
        if ( nRet != 0 ):
            print("create TriggerMode Node fail!")
            # 释放相关资源
            # release node resource before return
            streamSource.contents.release(streamSource) 
            return -1
        
        nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
        if ( nRet != 0 ):
            print("set TriggerMode value [Off] fail!")
            # 释放相关资源
            # release node resource before return
            trigModeEnumNode.contents.release(trigModeEnumNode)
            streamSource.contents.release(streamSource) 
            return -1
        
        # 需要释放Node资源
        # release node resource at the end of use  
        trigModeEnumNode.contents.release(trigModeEnumNode) 
            
        # 注册拉流回调函数
        # subscribe grabbing callback
        userInfo = b"test"
        frameCallbackFuncEx = callbackFuncEx(self.onGetFrameEx)
        nRet = streamSource.contents.attachGrabbingEx(streamSource, frameCallbackFuncEx, userInfo)    
        if ( nRet != 0 ):
            print("attachGrabbingEx fail!")
            # 释放相关资源
            # release stream source object before return
            streamSource.contents.release(streamSource)  
            return -1
            
        # 开始拉流
        # start grabbing
        nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
                                                c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
        if( nRet != 0):
            print("startGrabbing fail!")
            # 释放相关资源
            # release stream source object before return
            streamSource.contents.release(streamSource)   
            return -1

        # run the camera
        self.running = True
        while(self.running):
            time.sleep(0.01)

        # 释放资源
        # 反注册回调函数
        # unsubscribe grabbing callback
        nRet = streamSource.contents.detachGrabbingEx(streamSource, frameCallbackFuncEx, userInfo) 
        if ( nRet != 0 ):
            print("detachGrabbingEx fail!")
            # 释放相关资源
            # release stream source object before return
            streamSource.contents.release(streamSource)  
            return -1

        # 停止拉流
        # stop grabbing
        nRet = streamSource.contents.stopGrabbing(streamSource)
        if ( nRet != 0 ):
            print("stopGrabbing fail!")
            # 释放相关资源
            # release stream source object before return
            streamSource.contents.release(streamSource)  
            return -1

        # cv.destroyAllWindows()

        # 关闭相机
        # close camera
        nRet = self.closeCamera(camera)
        if ( nRet != 0 ):
            print("closeCamera fail")
            # 释放相关资源
            # release stream source object before return
            streamSource.contents.release(streamSource)   
            return -1
        
        # 释放相关资源
        # release stream source object at the end of use
        streamSource.contents.release(streamSource)    
        
        return 0


    def snap(self):
        '''
        执行一次软触发
        '''
        pass

    def close(self):
        self.running = False
        if self.is_alive():
            self.join()
        print(f"close the camera({self.name})")            


if __name__ == '__main__':
    # print(os.path.realpath(__file__))
    # print(os.path.join(os.path.split(os.path.realpath(__file__))[0], 'dll/x64/ImageConvert.dll'))
    print(TriggerMode.Free.name)
    GigEHuaray.enumCameras()
    print(GigEHuaray.cameras)
    camera = GigEHuaray('camera01')
    camera.start() # thread runs... 

    while(1):
        try:
            frame = camera.imgFactory.get(block=False) # Width=1024, Height=920, OffsetX=320,OffsetY=168
            frame = cv.resize(frame, (900, 800))
            cv.imshow(camera.name, frame)
        except Empty:
            pass

        if cv.waitKey(1) & 0xFF == ord('q'):
            camera.close()
            cv.destroyAllWindows()
            break
    
