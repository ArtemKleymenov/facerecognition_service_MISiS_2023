from abc import ABC, abstractmethod
import threading
import socket
import struct
from typing import Optional, Callable


class Service(ABC):
    """
    Базовый класс для создания сервисов с сетевым функционалом.

    :ip (str): IP-адрес сервиса.
    :port (int): Порт сервиса.
    :n_conn (int): Количество подключений, которые может обрабатывать сервер.
    :timeout (int): Таймаут для сокета.
    :need_job_break (bool): Флаг для остановки задачи сервиса.
    :need_job_pause (bool): Флаг для приостановки задачи сервиса.
    :server_is_open (bool): Флаг, показывающий, открыт ли сервер.
    :need_restart (bool): Флаг для перезапуска сервиса.
    :server (socket): Сокет сервера.
    :connected_clients (list): Список подключенных клиентов.
    """
    def __init__(self, ip_: str, port_: int, n_conn_=10):
        """
        Инициализация сервиса.

        :param ip_ (str): IP-адрес для привязки сервера.
        :param port_ (int): Порт для привязки сервера.
        :param n_conn_ (int): Максимальное количество подключений. По умолчанию 10.
        """
        self.ip = ip_
        self.port = port_
        self.n_conn = n_conn_
        self.timeout = 3

        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_clients = []

    def __recvall(self, sock: socket, n: int) -> bytearray:
        """Приватный метод для получения сообщения из сокета.

        :param sock: Сокет для чтения сообщения.
        :type sock: socket
        :return: Принятое сообщение.
        :rtype: bytearray
        """
        data = bytearray()
        while len(data) < n:
            print(n, len(data), n - len(data))
            packet = sock.recv(n - len(data))
            if not packet:
                break
            data.extend(packet)
        return data

    def __recv_msg(self, sock: socket) -> bytearray:
        """
        Приватный метод для получения сообщения из сокета.

        :param sock: Сокет для чтения сообщения.
        :type sock: socket
        :return: Прочитанное сообщение.
        :rtype: bytearray
        """
        raw_msglen = self.__recvall(sock, 4)
        if not raw_msglen:
            return bytearray()
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.__recvall(sock, msglen)

    def __send_msg(self, sock: socket, msg: bytes) -> None:
        """
        Приватный метод для отправки сообщения через сокет.

        :param sock: Сокет для отправки сообщения.
        :type sock: socket
        :param msg: Сообщение, которое необходимо отправить.
        :type msg: bytes
        """
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)

    def __manage_clients(self) -> None:
        """
        Приватный метод для обработки входящих запросов.

        Управляет запросами клиентов, обрабатывает команды управления сервисом (включить, выключить, закрыть,
        перезапустить) и делегирует обработку остальных запросов `_request_handler`.
        """
        service_closing_commands = []
        while True:
            if len(self.connected_clients) == 0 and not self.server_is_open:
                break
            if len(self.connected_clients) == 0:
                continue
            while len(self.connected_clients) > 0:
                client_socket = self.connected_clients[0]
                self.connected_clients.pop(0)

                try:
                    request = self.__recv_msg(client_socket)
                    request = request.decode("utf-8")
                    print(f"Received: {request}")

                    if request.lower() == "disable":
                        self.pause()
                        self.__send_msg(client_socket, "disable success".encode("utf-8"))
                    elif request.lower() == "enable":
                        self.unpause()
                        self.__send_msg(client_socket, "enable success".encode("utf-8"))
                    elif request.lower() == "close" or request.lower() == "restart":
                        self.stop()
                        service_closing_commands.append(request.lower())
                        self.__send_msg(client_socket, ("beginning " + request.lower()).encode("utf-8"))
                    else:
                        result = self._request_handler(request)
                        self.__send_msg(client_socket, result.encode("utf-8"))
                except Exception as e:
                    print(f"Server error when handling client: {e}")
                finally:
                    client_socket.close()
        if len(service_closing_commands) > 0:
            if service_closing_commands[0] == "restart":
                self.need_restart = True

    @abstractmethod
    def _do_job(self):
        """
        Защищенный метод основной работы для переопределения.

        Предполагается постоянная обработка входящей информации,
        требуется реализовать возможность для паузы и полной остановки сервиса.
        """
        pass

    @abstractmethod
    def _request_handler(self, request):
        """
        Защищенный метод обработки входящих запросов для переопределения.

        Предполагается обработка запросов, специфичных для конкретного сервиса,
        так как общие для всех сервисов запросы уже обрабатываются.
        """
        pass

    def _run_client(self, ip: str, port: int, request: str,
                    response_handler: Optional[Callable[[str], None]] = None) -> None:
        """
        Вспомогательный защищенный метод для отправления запроса другому сервису. Устанавливает соединение, отправляет
        запрос, получает ответ, решает, что делать с ответом.

        :param ip: IP-адрес сервера для подключения.
        :type ip: str
        :param port: Порт сервера для подключения.
        :type port: int
        :param request: Запрос для отправки на сервер.
        :type request: str
        :param response_handler: Функция обратного вызова для обработки ответа сервера, опциональный параметр.
        :type response_handler: Callable[[str], None], optional
        """
        global client
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))

            self.__send_msg(client, request.encode("utf-8"))
            response = self.__recv_msg(client)
            response = response.decode("utf-8")
            print(f"Received: {response}")

            if response_handler is not None:
                response_handler(response)
        except Exception as e:
            print(f"Client error when handling client: {e}")
        finally:
            client.close()
            print("Connection to server closed")

    # public:
    def run_client(self, ip: str, port: int, request: str, response_handler: Optional[Callable] = None) -> None:
        """
        Публичный метод для выполнения клиентского подключения и отправки запроса в отдельном потоке.

        :param ip: IP-адрес сервера для подключения.
        :type ip: str
        :param port: Порт сервера для подключения.
        :type port: int
        :param request: Запрос для отправки на сервер.
        :type request: str
        :param response_handler: Функция обратного вызова для обработки ответа сервера, опциональный параметр.
        :type response_handler: Callable[[str], None], optional
        """
        client_thread = threading.Thread(target=self._run_client, args=(ip, port, request, response_handler,))
        client_thread.start()

    def start(self) -> None:
        """
        Метод для запуска сервиса.

        Инициализирует сервер, начинает прослушивание на заданном IP и порту, и запускает потоки для управления задачами и клиентами.
        """
        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False
        self.connected_clients = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(self.timeout)
        self.server.bind((self.ip, self.port))
        self.server.listen(self.n_conn)
        print(f"Listening on {self.ip}:{self.port}")

        job_thread = threading.Thread(target=self._do_job, args=())
        job_thread.start()

        client_managing_thread = threading.Thread(target=self.__manage_clients, args=())
        client_managing_thread.start()

        while self.server_is_open:
            try:
                client_socket, client_address = self.server.accept()
                print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
                self.connected_clients.append(client_socket)
            except socket.timeout:
                pass
        client_managing_thread.join()
        self.server.close()

        if self.need_restart:
            self.restart()

    def stop(self) -> None:
        """
        Метод для остановки сервиса.

        Закрывает сервер и устанавливает флаги для остановки обработки задач и клиентских запросов.
        """
        self.server_is_open = False
        self.need_job_break = True

    def pause(self) -> None:
        """
        Метод для приостановки выполнения задач сервиса.

        Устанавливает флаг, приостанавливающий обработку задач, но не оставляет сервис полностью.
        """
        self.need_job_pause = False

    def unpause(self) -> None:
        """
        Метод для возобновления выполнения задач сервиса.

        Снимает флаг приостановки, позволяя возобновить обработку задач.
        """
        self.need_job_pause = True

    def restart(self) -> None:
        """
        Метод для перезапуска сервиса.

        Останавливает текущий экземпляр сервиса и инициирует его заново.
        """
        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart = False
        self.connected_clients = []
        self.start()