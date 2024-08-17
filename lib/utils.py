import socket

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    return local_ip_address


def create_db_backend(driver,**params):
    if driver == 'mysql':
        from db.mysql import MySqlBackend as dbbackend
    elif driver == 'postgres':
        from db.postgres import PostgresBackend  as dbbackend
    else:
        raise Exception('Unknown db driver %s',db_driver)
    return dbbackend(**params)
