# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#
#  语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#  webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#  语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#  设置热词
#  注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#  语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#  可添加语种或方言，添加后会显示该方言的参数值
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import hashlib
import base64
import hmac
import json
import threading
from urllib.parse import urlencode
import logging

from wsgiref.handlers import format_date_time
import datetime
from datetime import datetime
import time
from time import mktime
import _thread as thread
import pyaudio

from ws4py.client.threadedclient import WebSocketClient

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

I_START_GAME = 0  # 启动游戏
I_RESTART_GAME = 1   # 重开游戏
I_PLAY_MUSIC = 2  # 播放音乐
I_STOP_MUSIC = 3  # 停止音乐


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


class WsParam(object):
    # 初始化
    def __init__(self, APPId, APIKey, APISecret, AudioFile):
        self.APPId = APPId
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {
            'app_id': self.APPId
        }
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {
            'domain': 'iat',
            'language': 'zh_cn',
            'accent': 'mandarin',
            'vinfo': 1,
            'vad_eos': 10000,
            'dwa': 'wpgs',
            'ptt': 0
        }

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = 'host: ' + 'ws-api.xfyun.cn' + '\n'
        signature_origin += 'date: ' + date + '\n'
        signature_origin += 'GET ' + '/v2/iat ' + 'HTTP/1.1'
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self.APIKey, 'hmac-sha256', 'host date request-line', signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            'authorization': authorization,
            'date': date,
            'host': 'ws-api.xfyun.cn'
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print('date: ',date)
        # print('v: ',v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


class RecognitionWebsocket(WebSocketClient):

    def __init__(self, url, ws_param):
        super().__init__(url)
        self.ws_param = ws_param
        self.rec_text = {}  # 识别结果信息
        self.status = STATUS_FIRST_FRAME
        self.instruct_id = -1

        # 收到websocket消息的处理

    def received_message(self, message):
        message = message.__str__()

        try:
            code = json.loads(message)['code']
            sid = json.loads(message)['sid']
            self.status = json.loads(message)['data']['status']
            if code != 0:
                err_msg = json.loads(message)['message']
                logging.error('sid:%s call error:%s code is:%s' % (sid, err_msg, code))
            else:
                data = json.loads(message)['data']['result']
                ws = data['ws']

                result = ''
                for i in ws:
                    for w in i['cw']:
                        result += w['w']
                self.rec_text = result
                logging.info('识别结果为: {}'.format(self.rec_text) + " 当前状态：" + str(self.status))

                if "开始" in result:
                    self.instruct_id = 0
                    self.status = STATUS_LAST_FRAME
                elif "再来" in result:
                    self.instruct_id = 1
                    self.status = STATUS_LAST_FRAME

        except Exception as e:
            logging.info(message)
            logging.error('receive msg,but parse exception: {}'.format(e))

    # 收到websocket错误的处理
    def on_error(self, error):
        logging.error(error)

    # 收到websocket关闭的处理
    def closed(self, code, reason=None):
        logging.info('语音识别通道关闭' + str(code) + str(reason))

    # 收到websocket连接建立的处理
    def opened(self):
        def run(*args):
            interval = 0.04  # 发送音频间隔(单位:s)
            self.status = STATUS_FIRST_FRAME
            audio = pyaudio.PyAudio()
            stream = audio.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True)

            while True:
                buf = stream.read(CHUNK)
                # print(buf)
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if self.status == STATUS_FIRST_FRAME:
                    d = {'common': self.ws_param.CommonArgs,
                         'business': self.ws_param.BusinessArgs,
                         'data': {'status': 0, 'format': 'audio/L16;rate=16000',
                                  'audio': str(base64.b64encode(buf), 'utf-8'),
                                  'encoding': 'raw'}}
                    d = json.dumps(d)
                    self.send(d)
                    self.status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif self.status == STATUS_CONTINUE_FRAME:
                    d = {'data': {'status': 1, 'format': 'audio/L16;rate=16000',
                                  'audio': str(base64.b64encode(buf), 'utf-8'),
                                  'encoding': 'raw'}}
                    self.send(json.dumps(d))
                # 最后一帧处理
                elif self.status == STATUS_LAST_FRAME:
                    d = {'data': {'status': 2, 'format': 'audio/L16;rate=16000',
                                  'audio': str(base64.b64encode(buf), 'utf-8'),
                                  'encoding': 'raw'}}
                    self.send(json.dumps(d))
                    logging.info('录音结束')
                    time.sleep(1)

                    stream.stop_stream()
                    stream.close()
                    audio.terminate()

                    break
                # 模拟音频采样间隔
                time.sleep(interval)
            self.closed(1000, '')

        thread.start_new_thread(run, ())


if __name__ == "__main__":
    # AudioFile参数为空时表示不在本地生成音频文件，是否设置为空可以根据开发需求确定
    ws_param = WsParam(APPId='69027c09', APIKey='bc189e61e8d3a5dffd0329a5f6b9ddc9',
                       APISecret='YmVmODkzZGMxNTI4ZjAwMGMzNWY1NjVi', AudioFile=r'')
    ws_url = ws_param.create_url()
    ws = RecognitionWebsocket(ws_url, ws_param)


    def run_websocket():
        ws.connect()
        ws.run_forever()

    def recognize_instruction():
        while True:
            if ws.instruct_id == 0:
                break


    # 创建并启动后台线程
    websocket_thread = threading.Thread(target=run_websocket)
    websocket_thread.start()

    recognize_thread = threading.Thread(target=recognize_instruction)
    recognize_thread.start()

    while True:
        print(ws.status)
        time.sleep(1)
        if ws.status == 2:
            break

    time.sleep(5)
    print("重启线程")
    # ws = RecognitionWebsocket(ws_url, ws_param)

    print(ws)
    print(ws.status)
    # websocket_thread = threading.Thread(target=run_websocket)
    # websocket_thread.start()
    #
    # recognize_thread = threading.Thread(target=recognize_instruction)
    # recognize_thread.start()
    #
    # while True:
    #     print(ws.status)
    #     time.sleep(1)
    #     if ws.status == 2:
    #         break
