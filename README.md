# MessageBasedTcpServer
自己用python的epoll写一个简单tcp服务器。代码整体原理上参考了redis的处理流程，实现了多客户端处理基本功能。

## 使用

使用一个新的server类继承message_server.py中的MessageServer，并且重新实现process和server_cron函数。process中处理各种message的情况并返回，server_cron可以执行一些服务器定期指令。具体实现可以参考task_server.py。

## 实现

项目分为3个文件，`message.py`，`message_server.py`, `task_server.py`，他们的功能如下：

- `message.py` 定义了服务器在传输中的数据包格式，以及实现对数据包打包和解包的函数

```
    Message struct is this
    {
    unsigned int sig,       for len 0:4
    unsigned int totlen,    for len 4:8
    unsigned int type,      for len 8:12
    char[]       data       for len 12:totlen
    }
```

- `message_server.py` 是tcp服务器的主要代码，功能上使用epoll支持多个客户端同时连接，对每个客户端传来的数据使用message数据包格式解包，符合格式的调用process函数进行处理。在process函数中，根据解析出的message的type可以进行不同的处理。这里实现了一个简单的echo服务。另外支持服务端的一个定时事件，可以定时执行server_cron函数。

- `task_server.py` 实现了一个更进一步的多线程处理服务端，继承了MessageServer并且重载了process和server_cron函数，可以支持将长时间操作的任务放入task线程中处理，等task处理完成后再通过server_cron将结果返回给客户端，使长时间操作不会阻塞主线程。
