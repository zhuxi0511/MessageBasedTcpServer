import os

import threading
import time

from message_server import MessageServer

class ResultThread(threading.Thread):
    def __init__(self, func, args=()):
        super(ResultThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

class TaskStatus:
    thread = None
    is_run = False
    run_percent = 0

class MessageType: 
    task_start = 0x1e01
    task_reply = 0xe101
    task_query = 0x1e02

message_type = MessageType()

file_path = os.path.dirname(os.path.abspath(__file__))

class TaskServers(MessageServer):
    def __init__(self, host, port):
        super(TaskServers, self).__init__(host, port)
        self.task_status = TaskStatus()
        self.lock = threading.Lock()

    def task_start(self):
        for i in range(11):
            time.sleep(1)

            self.lock.acquire()
            self.task_status.run_percent = i 
            self.lock.release()

        # end export
        return "Finish"

    def process(self, fd, type, data):
        print "fd, type, data", fd, type, data
        if type == message_type.task_start:
            if self.task_status.is_run:
                self.add_reply(fd, message_type.task_reply, 'already run')
                return


            self.task_status.is_run = True
            self.task_status.thread = ResultThread(self.task_start)
            self.task_status.thread.start()
            self.add_reply(fd, message_type.task_reply, 'start')
            return

        elif type == message_type.task_query:
            pass
            return

    def server_cron(self):
        finish = self.task_status.thread.get_result() if self.task_status.thread is not None else None
        if finish:
            self.task_status.thread.join()
            self.task_status = TaskStatus()
            for fd in self.client_buffer.keys():
                self.add_reply(fd, message_type.task_reply, str(finish))
                #TODO just for client test
                self.close_client(fd)

        if self.task_status.is_run:
            self.lock.acquire()
            run_percent = self.task_status.run_percent
            self.lock.release()
            for fd in self.client_buffer.keys():
                self.add_reply(fd, message_type.task_reply, str(run_percent))



def main():
    server_host = "0.0.0.0"
    server_port = 9002
    nfs_ip = "192.168.1.36"
    server = TaskServers(server_host, server_port)
    server.run()


lock = threading.Lock()

def run_test_client():
    import socket 
    import message
    time.sleep(1)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9002))


    data = ""
    id = threading.currentThread().ident
    buf = message.extend_message([], message_type.task_start, data)
    #print "send_totlan", len(buf)
    s.sendall(''.join(buf))

    s.setblocking(False)
    read_buffer = []
    while True:
        chunk = str()
        try:
            chunk = s.recv(1024)
        except socket.error as e:
            #print e, e.errno
            if e.errno == 11:
                continue
            else:
                lock.acquire()
                print str(id), "connection error:", e;
                lock.release()
                break;
        if len(chunk) == 0:
            lock.acquire()
            print str(id), "connection broken:";
            lock.release()
            break
        #print "len:", len(chunk)

        #raise RuntimeError("connection broker")
        read_buffer.extend(chunk)
        status, m, read_buffer = message.remove_message(read_buffer)
        lock.acquire()
        if status != 1:
            print "receive reply", status, m
        lock.release()

if __name__ == '__main__':
    for i in range(2):
        t = threading.Thread(target=run_test_client)
        t.start()
    main()
