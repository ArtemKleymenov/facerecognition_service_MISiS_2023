import threading
from threading import Lock
import cv2


class Camera:
    """
    Класс Camera для работы с потоком кадров.
    """
    last_frame = None
    last_ready = None
    lock = Lock()

    def __init__(self, rtsp_link):
        """
        Инициализация.

        :param rtsp_link (str): ссылка для подключения к физической камере.
        :rtype: None
        """
        capture = cv2.VideoCapture(rtsp_link)
        thread = threading.Thread(target=self.rtsp_cam_buffer, args=(capture,), name = "rtsp_read_thread")
        thread.daemon = True
        thread.start()

    def rtsp_cam_buffer(self, capture):
        """
        Зачитывание кадра.

        :param capture: открытый поток.
        :rtype: None
        """
        while True:
            with self.lock:
                self.last_ready, self.last_frame = capture.read()


    def getFrame(self):
        """
        Получение кадра.

        :rtype: ndarary | None
        """
        if (self.last_ready is not None) and (self.last_frame is not None):
            return self.last_frame.copy()
        else:
            return None
        