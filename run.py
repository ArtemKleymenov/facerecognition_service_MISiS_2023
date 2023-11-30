from df_service import ServiceDF


if __name__ == '__main__' :
    service_var = ServiceDF(ip_="localhost", port_=8888)
    service_var.start()
    
