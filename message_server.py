import socket 
import select 
import threading
import time

import message

class MessageServer(object):
    def __init__(self, host, port, timeout=1):
        self.host = host 
        self.port = port
        self.timeout = timeout
        self.epoll = select.epoll()
        self.fd_to_socket = {}
        self.client_buffer = {}

        self.mssocket = self.init_server()

    def init_server(self):
        mssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mssocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        address = (self.host, self.port)
        mssocket.bind(address)
        mssocket.listen(100)

        self.epoll.register(mssocket.fileno(), select.EPOLLIN)
        
        self.fd_to_socket[mssocket.fileno()] = mssocket

        return mssocket

    def close_server(self):
        self.mssocket.close()
        print "Server closed!"

    def server_cron(self):
        print "Run server cron"

    def process(self, fd, type, data):
        #print "Process message here"
        # for test
        if type == message.message_echo_type:
            self.add_reply(fd, type, data)
        else:
            print "error message type", type

    def close_client(self, fd):
        self.epoll.unregister(fd)
        socket = self.fd_to_socket[fd]
        socket.close()
        del self.fd_to_socket[fd]
        del self.client_buffer[fd]

    def add_reply(self, fd, type, data):
        print "reply:", fd, type, data
        if data is None or len(data) == 0:
            return
        write_buffer = self.client_buffer[fd][1]
        message.extend_message(write_buffer, type, data)
        self.epoll.modify(fd, select.EPOLLOUT)

    def run(self):

        epoll_wait_time = self.timeout

        last_server_cron_run = time.time()

        print "Start to wait epoll event"
        while True:
            events = self.epoll.poll(epoll_wait_time)

            # Run server cron
            server_cron_check = time.time()

            # some time the result will small then 0 
            # Do not know the reason now
            server_cron_gap_time = max(server_cron_check - last_server_cron_run, 0)

            if server_cron_gap_time > epoll_wait_time:
                self.server_cron()
                epoll_wait_time = self.timeout
                last_server_cron_run = time.time()
            else:
                epoll_wait_time -= server_cron_gap_time 
            
            for fd, event in events:
                socket = self.fd_to_socket[fd]
                if socket == self.mssocket:
                    if not event & select.EPOLLIN:
                        print "Server error!"
                        exit(-1)
                    # new connection
                    connect_socket, address = self.mssocket.accept()
                    connect_socket.setblocking(False)
                    self.epoll.register(connect_socket.fileno(), 
                            select.EPOLLIN)
                    self.fd_to_socket[connect_socket.fileno()] = connect_socket
                    # 1 for read; 2 for write
                    self.client_buffer[connect_socket.fileno()] = [ [], []] 

                elif event & select.EPOLLHUP:
                    print "Client close!"
                    self.close_client(fd)


                elif event & select.EPOLLIN:
                    try:
                        data = socket.recv(1024)
                    except socket.error as e:
                        print e

                    if data: 
                        read_buffer = self.client_buffer[fd][0]
                        read_buffer.extend(data) 

                        while True:
                            status, m, read_buffer = message.remove_message(read_buffer)
                            self.client_buffer[fd][0] = read_buffer

                            if status == message.parse_ok:

                                type, data = m
                                # process
                                self.process(fd, type, data)  
                            elif status == message.buffer_not_enough:
                                break 
                            else:
                                print "Parse message error, close Client"
                                self.close_client(fd)
                                break

                elif event & select.EPOLLOUT:
                    write_buffer = ''.join(self.client_buffer[fd][1])
                    nwrite = socket.send(write_buffer)
                    self.client_buffer[fd][1] = list(write_buffer[nwrite:])
                    if len(self.client_buffer[fd][1]) == 0:
                        self.epoll.modify(fd, select.EPOLLIN)

        self.close_server()




lock = threading.Lock()

def run_test_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 12346))

    for i in range(8):
        id = threading.currentThread().ident
        data = "this id no is " + str(id) + " %d send time!" % i 

        buf = message.extend_message([], message.message_echo_type, data)
        #print "send_totlan", len(buf)
        s.sendall(''.join(buf))

        read_buffer = []
        target_read_size = len(buf)
        total_read_size = 0
        while total_read_size < target_read_size:
            chunk = s.recv(min(target_read_size - total_read_size, 
                1024))
            if len(chunk) == 0:
                raise RuntimeError("connection broker")
            read_buffer.extend(chunk)
            total_read_size += len(chunk)
        status, m, read_buffer = message.remove_message(read_buffer)
        lock.acquire()
        print "receive reply", status, m
        lock.release()



if __name__ == '__main__':
    server = MessageServer("127.0.0.1", 12346)

    for i in range(100):
        t = threading.Thread(target=run_test_client)
        t.start()

    server.run()





