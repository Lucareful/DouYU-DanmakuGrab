# asyncore模块



## 介绍

>这个模块为异步socket的服务器客户端通信提供简单的接口。
>
>该模块提供了异步socket服务客户端和服务器的基础架构。
>
>相比python原生的socket api，asyncore具备有很大的优势，asyncore对原生的socket进行封装，提供非常简洁优秀的接口，利用asyncore覆写相关需要处理的接口方法，就可以完成一个socket的网络编程，从而需要处理复杂的socket网络状况以及多线程处理等等。



## 实现流程



![image-asynocre](https://i.postimg.cc/VvCFY8Qg/image-20191029171333100.png)



# 客户端 Socket 开发基本使用

1.定义类继承自`asyncore.dispatcher`

2.实现类中的回调代码

  - 实现构造函数

      - 调用父类方法
      - 创建 `Socket`对象
      - 连接服务器

- 实现`handle_connect`回调函数

  > 当`socket`连接服务器成功时回调该函数

- 实现`writable`回调函数

  > 描述是否有数据需要被发送到服务器。返回值为`True`表示可写，`False`表示不可写，如果不实现默认返回为`True`，当返回`True`时，回调函数`handle_write`将被触发

- 实现`handle_write` 回调函数

  > 当有数据需要发送时（`writable`回调函数返回`True`时），该函数被触发，通常情况下在该函数中编写`send`方法发送数据
  
- 实现`readable`回调函数

     > 描述是否有数据从服务端读取。返回`True` 表示有数据需要读取，`False`表示没有数据需要被读取，当不实现默认返回为`True`，当返回`True` 时，回调函数`handle_read`将被触发

- 实现`handle_read `回调函数

     > 当有数据需要读取时触发（`readable`回调函数返回`True`
     > 时），该函数被触发，通常情况下在该函数中编写`recv`方法接收数据

- 实现`handle_error`回调函数

     > 当程序运行过程发生异常时回调

- 实现`handle_close`回调函数

     > 当连接被关闭时触发

- 3.创建对象并且执行`asyncore.loop`进入运行循环

     - `timeout`表示一次循环所需要的时长

```python
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
        pass

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
```



# 斗鱼弹幕实战

- 文档资料

  - 斗鱼弹幕服务器第三方接入协议V1.6.2.pdf 官方提供协议文档弹幕

全部代码：

## 客户端开发流程

- 连接初始化

  - 使用TCP连接服务器
    - IP地址：openbarrage.douyutv.com 
    - 端口：8601
  - 客户端向弹幕服务器发送登录请弧，登录弹幕服务器
  - 弹幕服务器收到客户端登录请求并完成登录后，返回登录成功消息给客户端
  - 客户端收到登录成功消息后发送进入弹幕分组请求给弹幕服务器
  - 弹幕服务器接受到客户端弹幕分组请求后将客户端添加到请求指定的弹幕分组中

- 服务过程

  - 客户端每隔45秒发送心跳给弹幕服务器，弹幕服务器回复心跳信息给客户端
  - 弹幕服务器如有广播信息，则推送给客户端，服务器消息协议

- 断开连接

  - 客户端发送登出消息
  - 客户端关闭TCP连接

## 数据发送和接收流程



![image-数据发送和接收流程](https://i.postimg.cc/qMp1Qkm8/image-20191030102511977.png)



### 数据包讲解



![image-20191030103731258](https://i.postimg.cc/4dShcQFL/image-20191030103731258.png)



- 消息长度：4 字节小端整数，表示整条消息（包括自身）长度（字节数）消息长度出现两遍，二者相同
- 消息类型：2 字节小端整数，表示消息类型。
- 取值如下：
  - 689 客户端发送给弹幕服务器的文本格式数据
  - 690 弹幕服务器发送给客户端的文本格式数据。
- 加密字段：暂时未用，默认为 0。
- 保留字段：暂时未用，默认为 0。
- 数据部分：斗鱼独创序列化文本数据，结尾必须为‘\0’。
- 详细序列化、反序列化算法见下节。（所有协议内容均为 UTF-8 编码）

### 数据包的封装

>对数据包进行对象化封装，对数据的封装方便以后使用，实现对象和二进制数据之间的转换

- 通过参数构建数据包对象
- 实现获取数据包长度的方法
- 实现获取二进制数据的方法



## 实现发送数据包

![image-20191030165625836](https://i.postimg.cc/NGH0BBG3/image-20191030165625836.png)



- 构建发送数据包的容器
- 实现回调函数，判断容器中有数据就发送没有数据不发送
- 实现登录函数
  - 构建登录数据包
  - 把数据包添加到发送数据包容器中

## 实现接收数据

![image-20191030174404676](https://i.postimg.cc/mkDvTKnp/image-20191030174404676.png)



- 构建接收数据包队列
- 读取回调函数中读取数据
  - 读取长度
  - 读取内容
  - 构建数据包对象
  - 把数据包放入接收数据包容器中
- 构建处理数据包线程
  - 构建线程
  - 实现回调函数处理数据



## 实现外部传入回调函散

> 通过外部指定回调函数实现自定义数据处理

- 添加参数`callback`
  - 构造函数中添加参数
  - 外部传入自定义回调函数
- 在处理接收数据包的线程中调用回调函数



## 数据内容序列话与反序列化

- 1 键 key 和值 value 直接采用‘@=’分割
- 2 数组采用‘/’分割
- 3 如果 key 或者 value 中含有字符‘/’，则使用‘@S’转义
- 4 如果 key 或者 value 中含有字符‘@’ ，使用‘@A’转义
  举例：
  - 多个键值对数据：key1@=value1/key2@=value2/key3@=value3/
  -  数组数据：value1/value2/value3/
-  不同消息有相同的协议头、序列化方式

## 加入弹幕分组

>​        第三方平台建议选择-9999（即海量弹幕模式  )



## 心跳机制

> 作用是让服务器解决假死连接问题，客户端必须每隔45秒发送一次请求，否则就会被主动断开。

- 实现发送心跳函数
  - 构建心跳数据包
  - 把数据包添加到发送数据包容器队列中
- 构建心跳线程
  - 构建心跳线程
  - 添加触发机制
  - 添加暂停机制