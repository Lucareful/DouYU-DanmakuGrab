import asyncore
import sys


# 定义类继承自 asyncore.dispather
class scoket_client(asyncore.dispatcher):

    # 实现类中的回调代码
    def __init__(self, host, port):
        # 调用父类的方法
        asyncore.dispatcher.__init__(self)

        # 创建 Scoket 服务器
        self.create_socket()

        # 连接地址
        address = (host, port)
        self.connect(address)

    # 实现handle_connect回调函数
    def handle_connect(self):
        print("连接成功")

    # 实现writable函数
    def writable(self):
        return False

    # 实现handle_write回调函数
    def handle_write(self):
        # 内部实现对服务器发送数据代码
        # 调用 send 方法发送数据，参数是字节数据
        self.send("hello world".encode('utf-8'))
        # self.send("hello world")

    # 实现readable回调函数
    def readable(self):
        return True

    # 实现handle_read回调函数
    def handle_read(self):
        # 主动接收数据
        result = self.recv(1024)
        print(result)

    # 实现handle_error回调函数
    def handle_error(self):
        # 编写处理错误方法
        t, e, trace = sys.exc_info()

    # 实现handle_close回调函数
    def handle_close(self):
        print("连接关闭")
        self.close()


# 创建对象并且执行asyncore.loop 进入循环


if __name__ == '__main__':
    client = scoket_client('127.0.0.1', 9000)

    # 开始启动运行循环
    asyncore.loop(timeout=5)