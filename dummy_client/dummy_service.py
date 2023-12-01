import numpy as np
import cv2
import base64
import time

from fr_service.service import Service


class ServiceDummy(Service):
    """
    Класс ServiceDummy расширяет функциональность базового класса Service,
    предоставляя запросы и обработку ответ от распознавания лиц class:`fr_service.fr_service.ServiceFR`.
    """

    def _do_job(self):
        """
        Переопределенный метод, выполняющий основную работу сервиса.
        """
        try:
            # while True:
            time.sleep(2)
            self.stopTracking(ip="localhost", port=8888)
        finally:    
            # Когда работа окончена, следует остановить сервис
            self.stop()


    def _request_handler(self, request):
        return 'None'

    # Методы для работы с ServiceFR
    # getFrame
    def __resp_hand_get_frame(self, response):
        b64_res = base64.b64decode(response)
        from_b = np.frombuffer(b64_res, dtype=np.uint8)
        img = cv2.imdecode(from_b, cv2.IMREAD_COLOR)
        cv2.imshow('BGR_Frame', img)
        cv2.waitKey(1000)

    def getFrame(self, ip, port):
        self.run_client(ip=ip, port=port, request='getFrame', 
                        response_handler=self.__resp_hand_get_frame)                  

    # getDepth
    def __resp_hand_get_depth(self, response):
        b64_res = base64.b64decode(response)
        from_b = np.frombuffer(b64_res, dtype=np.uint8)
        img = cv2.imdecode(from_b, cv2.IMREAD_GRAYSCALE)
        cv2.imshow('Depth_Frame', img)
        cv2.waitKey(1000)

    def getDepth(self, ip, port):
        self.run_client(ip=ip, port=port, request='getDepth',
                        response_handler=self.__resp_hand_get_depth)
        
    # getFace
    def __resp_hand_get_face(self, response):
        b64_res = base64.b64decode(response)
        from_b = np.frombuffer(b64_res, dtype=np.uint8)
        img = cv2.imdecode(from_b, cv2.IMREAD_COLOR)
        cv2.imshow('Face_Frame', img)
        cv2.waitKey(1000)

    def getFace(self, ip, port):
        self.run_client(ip=ip, port=port, request='getFace',
                        response_handler=self.__resp_hand_get_face)

    # getRect
    def __resp_hand_get_rect(self, response):
        print(f"Received: {response}")

    def getRect(self, ip, port):
        self.run_client(ip=ip, port=port, request='getRect',
                        response_handler=self.__resp_hand_get_rect)

    # applyThreshold
    def __resp_hand_apply_threshold(self, response):
        print(f"Received: {response}")

    def applyThreshold(self, ip, port, thresh):
        _threshold = 'applyThreshold_' + str(thresh)
        self.run_client(ip=ip, port=port, request=_threshold,
                        response_handler=self.__resp_hand_apply_threshold)

    # startTracking
    def __resp_hand_start_tracking(self, response):
        print(f"Received: {response}")

    def startTracking(self, ip, port):
        self.run_client(ip=ip, port=port, request='startTracking',
                        response_handler=self.__resp_hand_start_tracking)

    # target
    def __resp_hand_target(self, response):
        print(f"Received: {response}")

    def target(self, ip, port):
        self.run_client(ip=ip, port=port, request='target',
                        response_handler=self.__resp_hand_target)
    
    # stopTracking
    def __resp_hand_stop_tracking(self, response):
        print(f"Received: {response}")

    def stopTracking(self, ip, port):
        self.run_client(ip=ip, port=port, request='stopTracking',
                        response_handler=self.__resp_hand_stop_tracking)

    # applyGrayscale
    def __resp_hand_apply_grayscale(self, response):
        print(f"Received: {response}")

    def applyGrayscale(self, ip, port):
        self.run_client(ip=ip, port=port, request='applyGrayscale',
                        response_handler=self.__resp_hand_apply_grayscale)

    # applyRgb
    def __resp_hand_apply_rgb(self, response):
        print(f"Received: {response}")

    def applyRgb(self, ip, port):
        self.run_client(ip=ip, port=port, request='applyRgb',
                        response_handler=self.__resp_hand_apply_rgb)

    # getThreshold
    def __resp_hand_get_thresh(self, response):
        print(f"Received: {response}")

    def getThreshold(self, ip, port):
        self.run_client(ip=ip, port=port, request='getThreshold',
                        response_handler=self.__resp_hand_get_thresh)

    # getColorMap
    def __resp_hand_get_cm(self, response):
        print(f"Received: {response}")

    def getColorMap(self, ip, port):
        self.run_client(ip=ip, port=port, request='getColorMap',
                        response_handler=self.__resp_hand_get_cm)
