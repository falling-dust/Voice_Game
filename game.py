# coding: utf8
import threading
import time

import cocos
from cocos.sprite import Sprite
from pyaudio import PyAudio, paInt16
import pygame
import struct

from sympy.core import singleton

# from iat_ws_python3 import WsParam, RecognitionWebsocket
from ppx import PPX
from block import Block
from gameover import Gameover, run_websocket
from billboard import Billboard
from defines import *


# 创建一个继承自cocos.layer.ColorLayer的VoiceGame类
class VoiceGame(cocos.layer.ColorLayer):
    is_event_handler = True

    def __init__(self):  # ,ws_instance***
        # 初始化 VoiceGame 类
        # self.ws = ws_instance   ***
        super(VoiceGame, self).__init__(255, 255, 255, 255, WIDTH, HEIGHT)  # 设置场景的背景颜色和大小
        pygame.mixer.init()

        self.gameover = None  # 游戏结束标志
        self.billboard = None  # 计分板

        # 分数标签
        self.score = 0
        self.txt_score = cocos.text.Label(u'分数：0', font_name=FONTS, font_size=24, color=BLACK)
        self.txt_score.position = 800, 600
        self.add(self.txt_score, 99999)

        # 顶部通知信息
        self.top = '', 0
        self.top_notice = cocos.text.Label(u'', font_name=FONTS, font_size=18, color=BLACK)
        self.top_notice.position = 700, 510
        self.add(self.top_notice, 99999)

        self.name = ''  # 玩家姓名

        # 初始化声音
        self.NUM_SAMPLES = 2048  # pyAudio 内部缓存的块的大小
        self.LEVEL = 1500  # 声音保存的阈值

        # 顶部声音条
        self.voiceBar = Sprite('photo/black.png', color=(100, 200, 255))
        self.voiceBar.position = 20, 550
        self.voiceBar.scale_y = 0.1
        self.voiceBar.image_anchor = 0, 0
        self.add(self.voiceBar)

        self.ppx = PPX(self)  # 创建角色对象
        self.add(self.ppx)  # 将角色添加到场景中

        self.floor = cocos.cocosnode.CocosNode()  # 地板节点
        self.add(self.floor)  # 将地板节点添加到场景中
        self.last_block = 0, 100  # 上一个方块的位置
        for i in range(5):
            b = Block(self)
            self.floor.add(b)
            pos = b.x + b.width, b.height

        # 开启声音输入
        pa = PyAudio()
        SAMPLING_RATE = int(pa.get_device_info_by_index(0)['defaultSampleRate'])  # 获取默认采样率
        self.stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True,
                              frames_per_buffer=self.NUM_SAMPLES)  # 打开音频流
        self.stream.stop_stream()  # 停止音频流

        self.background_music = None  # 背景音乐对象
        self.load_background_music('music/bgm.wav')
        self.play_background_music()

        self.schedule(self.update)  # 调度器，将update方法添加到场景中定期更新

    # 音乐控制
    def load_background_music(self, file_path):
        self.background_music = pygame.mixer.Sound(file_path)

    def play_background_music(self, loop=-1):
        if self.background_music:
            self.background_music.play(loop)

    def stop_background_music(self):
        if self.background_music:
            self.background_music.stop()

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def collide(self):
        px = self.ppx.x - self.floor.x
        for b in self.floor.get_children():
            if b.x <= px + self.ppx.width * 0.8 and px + self.ppx.width * 0.2 <= b.x + b.width:
                if self.ppx.y < b.height:
                    self.ppx.land(b.height)
                    break

    def update(self, dt):
        # 读入 NUM_SAMPLES 个取样
        if self.stream.is_stopped():
            self.stream.start_stream()
        string_audio_data = self.stream.read(self.NUM_SAMPLES)  # 从音频流中读取数据
        k = max(struct.unpack('2048h', string_audio_data))  # 解析取样数据，找到最大值
        self.voiceBar.scale_x = k / 10000.0  # 根据取样值设置声音条长度

        if k > 2000:
            if not self.ppx.dead:
                # 根据取样值更新地板的位置，最大偏移量为 (k / 20.0) 或 150
                self.floor.x -= min((k / 20.0), 150) * dt
        if k > 6000:
            # 如果取样值大于 6000，调用角色的跳跃方法，参数为 (k - 6000) / 25.0
            self.ppx.jump((k - 6000) / 25.0)

        self.floor.x -= self.ppx.velocity * dt  # 根据角色的速度更新地板的位置
        self.collide()  # 执行碰撞检测
        self.top_notice.x -= 80 * dt  # 移动顶部通知的位置

        if self.top_notice.x < -700:
            self.top_notice.x = 700  # 重置顶部通知的位置，使其移出屏幕

    def reset(self):
        # 重置游戏状态
        self.floor.x = 0
        self.last_block = 0, 100
        for b in self.floor.get_children():
            b.reset()
        self.score = 0
        self.txt_score.element.text = u'分数：0'
        self.ppx.reset()

        # 移除游戏结束和计分板（如果存在）
        if self.gameover:
            self.remove(self.gameover)
            self.gameover = None
        if self.billboard:
            self.remove(self.billboard)
            self.billboard = None

        self.stream.start_stream()  # 开启声音输入
        self.resume_scheduler()  # 恢复调度器的运行

        # 如果存在最佳记录，则显示最佳记录提示
        if self.top[0] and self.top[1]:
            notice = u'%s 刚刚以 %d 分刷新了今日最佳！' % self.top
            self.top_notice.element.text = notice
            self.top_notice.x = 800

    def end_game(self):
        # 跳跃失败，游戏结束
        self.stream.stop_stream()
        self.pause_scheduler()
        self.gameover = Gameover(self)
        self.add(self.gameover, 100000)

    def show_top(self):
        # 显示最高分榜单
        self.remove(self.gameover)
        self.gameover = None
        self.billboard = Billboard(self)
        self.add(self.billboard, 100001)

    def add_score(self):
        # 增加分数
        self.score += 1
        self.txt_score.element.text = u'分数：%d' % self.score


if __name__ == "__main__":
    # AudioFile参数为空时表示不在本地生成音频文件，是否设置为空可以根据开发需求确定

    # 语音识别启动
    # ws_param = WsParam(APPId='69027c09', APIKey='bc189e61e8d3a5dffd0329a5f6b9ddc9',
    #                    APISecret='YmVmODkzZGMxNTI4ZjAwMGMzNWY1NjVi', AudioFile=r'')
    # ws_url = ws_param.create_url()
    # ws = RecognitionWebsocket(ws_url, ws_param)

    # websocket_thread = threading.Thread(target=run_websocket, args=(ws,))
    # websocket_thread.start()

    # while True:
    #     if ws.instruct_id == 0:
    #         ws.instruct_id = -1
            # 初始化Cocos2d导演
            cocos.director.director.init(width=WIDTH, height=HEIGHT, caption="Let's Go! JieZi!")
            # 运行场景
            cocos.director.director.run(cocos.scene.Scene(VoiceGame())) # ws
