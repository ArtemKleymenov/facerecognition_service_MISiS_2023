import numpy as np
import cv2
from deepface import DeepFace
import base64
import time

from fr_service.service import Service
from custom_cam.cam import Camera

class ServiceFR(Service):
    """
    Класс ServiceFR расширяет функциональность базового класса Service,
    предоставляя обработку видеопотока и распознавания лиц.
    """

    def _do_job(self):
        """
        Переопределенный метод, выполняющий основную работу сервиса.

        Включает в себя подключение к видеопотоку, обработку кадров и выполнение специализированных задач.
        В случае исключений, передает их в обработчик запросов.

        :rtype: None
        """
        try:
            self.__init_vars()

            # Подключение к RTSP потоку камеры
            url = 'rtsp://localhost:8554/mystream'  # rtsp-стрим
            url = 0  # webcam
            cap = Camera(url)
                
            while True:
                if self.need_job_break:
                    return
                if not self.need_job_pause:
                    continue

                # Получение кадров из потока
                self._frame = cap.getFrame()
                # Проверка, что кадр непустой
                if self._frame is None:
                    continue
                try:
                    # Обработка кадров
                    self.__specific_work()
                except Exception as e:
                    print('Exception:', e)
                    break
        finally:    
            # Когда работа окончена, следует остановить сервис
            cv2.destroyAllWindows()
            self.stop()


    def _request_handler(self, request):
        """
        Переопределенный метод для обработки входящих запросов.
        Полный список API-запросов доступен `здесь <https://github.com/ArtemKleymenov/facerecognition_service_MISiS_2023/tree/main#api-сервиса>`

        :param request: Входящий запрос.
        :type request: str
        :return: Ответ на запрос.
        :rtype: str
        """

        # https://docs.google.com/document/d/1wzAFfvVaIiOorsixK455Tr-vMfUOrCPk9_qPgOyx29U/edit
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        # GET FRAME
        if request == 'getFrame':
            rgb = cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB)
            img_buf = cv2.imencode('.jpg', rgb, encode_params)[1] # np.ndarray
            data = np.array(img_buf).tobytes()
            _str = base64.b64encode(data)
            return _str.decode()
        # GET DEPTH
        if request == 'getDepth':
            # gray = cv2.cvtColor(self._depth)
            img_buf = cv2.imencode('.jpg', self._depth, encode_params)[1] # np.ndarray
            data = np.array(img_buf).tobytes()
            _str = base64.b64encode(data)
            return _str.decode()
        # GET FACE
        if request == 'getFace':
            rgb = cv2.cvtColor(self._target_face, cv2.COLOR_BGR2RGB)
            img_buf = cv2.imencode('.jpg', rgb, encode_params)[1] # np.ndarray
            data = np.array(img_buf).tobytes()
            _str = base64.b64encode(data)
            return _str.decode()
        # GET RECT
        if request == 'getRect':
            if self._face_rect is None:
                _str = '0,0,0,0'
            else:    
                _str = ','.join(str(x) for x in self._face_rect)
            return _str
        # SET THRESHOLD
        if 'applyThreshold' in request:
            new_thresh = float(request.split('_')[1])
            if 0.0 < new_thresh <= 1.0:
                self._threshold = new_thresh
                _str = 'ok'
            else:
                _str = 'failed'
            return _str
        # BEGIN FACE TRACKING
        if request == 'startTracking':
            self._set_target = True
            time.sleep(2)
            if self._target_face is None:
                _str = 'failed'
            else:
                _str = 'ok'
            self._set_target = False
            return _str
        # GET TARGET
        if request == 'target':
            if self._face_rect is None:
                _str = 'empty'
            else:    
                _str = ','.join(str(x) for x in self._face_rect.items())
            return _str
        # STOP FACE TRACKING
        if request == 'stopTracking':
            self._set_target   = False
            self._target_face  = None
            self._target_in    = 0
            self._target_embed = None
            time.sleep(2)
            _str = 'ok'
            return _str
        # SET GRAYSCALE COLORMAP
        if request == 'applyGrayscale':
            self._colormap = 'gray'
            _str = 'ok'
            return _str.decode()
        # SET RGB COLORMAP
        if request == 'applyRgb':
            self._colormap = 'rgb'
            _str = 'ok'
            return _str.decode()
        # GET THRESHOLD VALUE
        if request == 'getThreshold':
            _str = str(self._threshold)
            return _str
        # GET COLORMAP
        if request == 'getColorMap':
            _str = self._colormap
            return _str
        return 'None'

    # Вспомогательная функция
    def __init_vars(self):
        """
        Приватный метод для установки параметров по умолчанию.

        :rtype: None
        """
        self._threshold = 0.667
        self._set_target = False
        self._frame = None
        self._depth = None
        self._target_embed = None

        # extras
        self._target_face = None
        self._target_in = 0  # no more than 5 and less than 0
        self._total_frames = 0
        self._face_rect = None
        self._colormap = 'rgb'
        pass

    # Вспомогательная функция
    def __specific_work(self):
        """
        Приватный метод для нахождения таргета.

        :rtype: None
        """

        extractor = DeepFace.extract_faces(
            self._frame, enforce_detection=False, 
            detector_backend='mediapipe', align=False, 
            target_size=[256, 256]
        )

        # Установка отслеживаемого/идентифицируемого лица
        if self._set_target:
            if extractor[0] is not None\
                and extractor[0]['confidence'] > self._threshold:
                print('Target')
                self._target_face = extractor[0]['face']
                self._target_embed = DeepFace.represent(
                    extractor[0]['face'].copy(), 
                    detector_backend='skip', 
                    model_name='ArcFace')

        color = (0, 0, 255)
        # Проверка: Лучшее* найденное на кадре лицо это наше таргетное лицо?
        # *имеющее наибольшее значение поля confidence
        for i, face_dict in enumerate(extractor):
            if face_dict['confidence'] < 0.01 or self._target_embed is None:
                break
            try:
                pred_embed = DeepFace.represent(face_dict['face'], detector_backend='skip', 
                                            model_name='ArcFace')
                self._face_rect = face_dict['facial_area']

                cos_sim_score = DeepFace.dst.findCosineDistance(
                    self._target_embed[0]["embedding"], pred_embed[0]["embedding"])
                
                print("Cosine Similarity:", cos_sim_score)

                if cos_sim_score < self._threshold:
                    if self._target_in < 5:
                        self._target_in += 1
                    color = (0, 255, 0)
                else:
                    if self._target_in > 0:
                        self._target_in -= 1
                cv2.imshow(f'Detected_{i}', face_dict['face'])
            except Exception as e:
                print('Search common face error!', e)
            finally:
                break
        # visualization
        if self._target_face is not None:
            pass
            _face = cv2.cvtColor(self._target_face, cv2.COLOR_BGR2RGB)
            cv2.imshow('Target', _face)

        if self._face_rect is not None:
            _value = "SAME"
            if color[2] == 255:
                _value = "NOT SAME"
            cv2.putText(self._frame, _value,
                        (self._face_rect['x'], self._face_rect['y']+10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,color,2)
            cv2.rectangle(self._frame, (self._face_rect['x'], self._face_rect['y']),
                          (self._face_rect['x']+self._face_rect['w'], self._face_rect['y']+self._face_rect['h']), 
                          color, thickness=2)
            
        cv2.imshow('Frame', self._frame)
        cv2.waitKey(10) 
        
        self._total_frames += 1
        # print(f'Frames (in/total): {self._target_in}/{self._total_frames}')
        pass

    def __resp_hand(self, response):
        """
        Приватный метод для обработки ответа (пуст).

        :rtype: None
        """
        pass
