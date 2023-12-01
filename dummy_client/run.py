from dummy_client.dummy_service import ServiceDummy


if __name__ == '__main__' :
    service_dummy = ServiceDummy(ip_="localhost", port_=5050)
    service_dummy.start()
