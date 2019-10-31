import asyncore
import sys
import threading
import time
from queue import Queue

DATA_PACKET_TYPE_SEND = 689
DATA_PACKET_TYPE_RECV = 690


def encode_content(content):
    """
    序列化内容
    :param content:需要序列化的内容
    :return:
    """
    if isinstance(content, str):
        return content.replace(r'@', r'@A').replace(r'/', r'@S')
    elif isinstance(content, dict):
        return r'/'.join(["{}@={}".format(encode_content(k), encode_content(v)) for k, v in content.items()]) + r'/'
    elif isinstance(content, list):
        return r'/'.join([encode_content(data) for data in content]) + r'/'

    return ""


def decode_to_str(content):
    """
    反序列化字符串
    :param content:字符串数据
    :return:
    """
    if isinstance(content, str):
        return content.replace(r'@S', r'/').replace('@A', r'@')
    return ""


def decode_to_dict(content):
    """
    反序列化字典数据
    :param content:被序列化的字符串
    :return:
    """
    ret_dict = dict()
    if isinstance(content, str):
        item_string = content.split(r'/')
        for item_string in item_string:
            k_v_list = item_string.split(r'@=')
            if k_v_list is not None and len(k_v_list) > 1:
                k = k_v_list[0]
                v = k_v_list[1]
                ret_dict[decode_to_str(k)] = decode_to_str(v)
    return ret_dict


def decode_to_list(content):
    """
    对列表进行反序列化
    :param content:被序列化的字符串
    :return:
    """
    ret_list = []

    if isinstance(content, str):
        items = content.split(r'/')
        for idx, item in enumerate(items):
            if idx < len(items) - 1:
                ret_list.append(decode_to_str(item))
    return ret_list


class DataPacket():
    def __init__(self, type=DATA_PACKET_TYPE_SEND, content='', data_bytes=None):
        if data_bytes is None:
            # 数据包类型
            self.type = type
            # 数据部分内容
            self.content = content
            self.encorypt_flag = 0
            self.preserve_flag = 0
        else:
            self.type = int.from_bytes(data_bytes[4:6], byteorder='little', signed=False)
            self.encorypt_flag = int.from_bytes(data_bytes[6:7], byteorder='little', signed=False)
            self.preserve_flag = int.from_bytes(data_bytes[7:8], byteorder='little', signed=False)
            # 构建数据部分
            self.content = str(data_bytes[8:-1], encoding='utf-8')

    def get_length(self):
        """
        获取当前数据包长度，为以后需要发送数据包做准备
        :return:
        """
        return 4 + 2 + 1 + 1 + len(self.content.encode('utf-8', "ignore")) + 1

    def get_bytes(self):
        """
        通过数据包转换成 二进制数据
        :return:
        """
        data = bytes()
        # 构建四个字节的消息长度数据
        data_packet_length = self.get_length()
        # to_bytes把一个整型数据转化成二进制数据
        # 第一个参数，表示需要转 换的二进制数据占几个字节
        # byteorder第二个参数，描述字节数
        # signed第三个参数，设置是否有符号

        # 处理消息长度
        data += data_packet_length.to_bytes(4, byteorder='little', signed=False)
        # 处理消息类型
        data += self.type.to_bytes(2, byteorder='little', signed=False)
        # 处理加密字段
        data += self.encorypt_flag.to_bytes(1, byteorder='little', signed=False)
        # 处理保留字段
        data += self.preserve_flag.to_bytes(1, byteorder='little', signed=False)

        # 处理数据内容
        data += self.content.encode("utf-8","ignore")

        # 添加 \0 数据
        data += b'\0'

        return data


class DouYu(asyncore.dispatcher):

    def __init__(self, host, port, callback=None):
        # 构建发送数据包的队列
        self.send_queue = Queue()

        # 构建接收数据包的队列
        self.recv_queue = Queue()

        # 定义外部传入的自定义回调函数
        self.callback = callback

        # 调用父类的方法
        asyncore.dispatcher.__init__(self)

        # 创建 Scoket 服务器
        self.create_socket()

        # 连接地址
        address = (host, port)
        self.connect(address)

        # 构建一个专门处理接收数据包容器中的数据包的线程
        self.callback_thread = threading.Thread(target=self.do_callback)
        self.callback_thread.setDaemon(True)
        self.callback_thread.start()

        # 构建心跳线程
        self.heart_thread = threading.Thread(target=self.do_ping)
        self.heart_thread.setDaemon(True)
        self.ping_running = False

    def handle_connect(self):
        print("连接成功")
        self.stsrt_ping()

    def writable(self):
        return self.send_queue.qsize() > 0

    def handle_write(self):
        # 从发送数据包队列中获取数据包对象
        dp = self.send_queue.get()

        # 获取数据包的长度
        dp_length = dp.get_length()
        dp_length_data = dp_length.to_bytes(4, byteorder='little', signed=False)
        self.send(dp_length_data)

        # 发送数据包二进制数据
        self.send(dp.get_bytes())
        self.send_queue.task_done()

    def readable(self):
        return True

    def handle_read(self):

        # 读取长度，二进制数据
        length_data = self.recv(4)
        # 通过二进制获取length具体数据
        data_length = int.from_bytes(length_data, byteorder='little', signed=False)

        # 通过数据包的长度，获取数据
        data = self.recv(data_length)
        # 通过二进制数据，构建数据包对象
        dp = DataPacket(data_bytes=data)
        # 把数据包放入接收数据的容器中
        self.recv_queue.put(dp)

    def handle_error(self):
        t, e, trace = sys.exc_info()
        print(e)
        self.close()

    def handle_close(self):
        self.stop_ping()
        print("连接关闭")
        self.close()

    def login_room_id(self, room_id):

        self.room_id = room_id

        send_data = {
            "type":"loginreq",
            "roomid":str(room_id)
        }

        # 构建登录数据包
        content = encode_content(send_data)
        login_dp = DataPacket(DATA_PACKET_TYPE_SEND, content=content)

        # 把数据包添加到发送数据包容器中
        self.send_queue.put(login_dp)

    def join_room_group(self):
        """
        加入弹幕分组
        """
        send_data = {
            "type":"joingroup",
            "rid":str(self.room_id),
            "gid":'-9999'
        }

        content = encode_content(send_data)

        dp = DataPacket(type=DATA_PACKET_TYPE_SEND, content=content)
        self.send_queue.put(dp)

    def send_heart_data_packet(self):
        send_data = {
            "type":"mrkl"
        }
        content = encode_content(send_data)
        dp = DataPacket(type=DATA_PACKET_TYPE_SEND, content=content)
        self.send_queue.put(dp)

    def stsrt_ping(self):
        """开始心跳"""
        self.ping_running = True

    def stop_ping(self):
        """结束心跳"""
        self.ping_running = False

    def do_ping(self):
        """执行心跳"""
        while True:
            if self.ping_running:
                self.send_heart_data_packet()
                time.sleep(40)

    def do_callback(self):
        """
        专门负责处理接收数据包容器中的数据
        :return:
        """
        while True:
            # 从接收数据包容器中获取数据
            dp = self.recv_queue.get()
            # 对数据进行处理
            if self.callback is not None:
                self.callback(dp)
            self.recv_queue.task_done()


def data_callback(dp):
    """
    :param dp:数据包对象
    :return:
    """
    resp_data = decode_to_dict(dp.content)
    if resp_data["type"] == "loginres":
        # 调入加入分组请求
        print("登录成功", resp_data)
        client.join_room_group()
    elif resp_data["type"] == "chatmsg":
        print("{}:{}".format(resp_data['nn'], resp_data['txt']))


if __name__ == '__main__':
    client = DouYu("openbarrage.douyutv.com", 8601, callback=data_callback)

    client.login_room_id(101)

    asyncore.loop(timeout=10)

#     序列化和反序列化测试
#     data = {
#         "a":"x@b",
#         "b":"y"
#     }
#     data = ["a","b", "/", "c"]
#     edata = encode_content(data)
#
#     print(decode_to_list(edata))
