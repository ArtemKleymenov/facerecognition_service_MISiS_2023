from fr_service.fr_service import ServiceFR


if __name__ == '__main__' :
    service_var = ServiceFR(ip_="localhost", port_=8888)
    service_var.start()
    