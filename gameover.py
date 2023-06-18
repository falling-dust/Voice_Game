# -*- coding: utf-8 -*-
import threading

import cocos
from defines import *
import json
import datetime


# from iat_ws_python3 import WsParam, RecognitionWebsocket


def run_websocket(ws_instance):
    ws_instance.connect()
    ws_instance.run_forever()


class Gameover(cocos.layer.ColorLayer):
    def __init__(self, game):
        super(Gameover, self).__init__(0, 0, 0, 255, WIDTH, HEIGHT)
        self.game = game
        self.billboard = None
        self.score = cocos.text.Label(u'分数：%d' % self.game.score,
                                      font_name=FONTS,
                                      font_size=36)
        self.score.position = 365, 480
        self.add(self.score)

        menu = cocos.menu.Menu(u'济又输！')
        menu.font_title['font_name'] = FONTS
        menu.font_item['font_name'] = FONTS
        menu.font_item_selected['font_name'] = FONTS
        self.name = cocos.menu.EntryMenuItem(u'你是?', self.input_name, self.game.name)
        self.name.y = 0
        submit = cocos.menu.MenuItem(u'提交成绩', self.submit)
        submit.y = -33
        top = cocos.menu.MenuItem(u'排行榜', self.game.show_top)
        top.y = -67
        replay = cocos.menu.MenuItem(u'再来一次', self.replay)
        replay.y = -100
        menu.create_menu([self.name, submit, top, replay])
        self.add(menu)

        logo = cocos.sprite.Sprite('photo/crossin-logo.png')
        logo.position = 790, 150
        self.add(logo, 99999)

        self.schedule(self.update)  # 调度器，将update方法添加到场景中定期更新

        # ws_param = WsParam(APPId='69027c09', APIKey='bc189e61e8d3a5dffd0329a5f6b9ddc9',
        #                    APISecret='YmVmODkzZGMxNTI4ZjAwMGMzNWY1NjVi', AudioFile=r'')
        # ws_url = ws_param.create_url()
        # ws = RecognitionWebsocket(ws_url, ws_param)
        #
        # def run_voice_again():
        #     ws.connect()
        #     ws.run_forever()
        #
        # # 语音识别启动
        # websocket_thread = threading.Thread(target=run_voice_again)
        # websocket_thread.start()

    def input_name(self, txt):
        self.game.name = txt
        if len(txt) > 16:
            self.game.name = txt[:16]

    def update(self, dt):
        if self.game.ws.instruct_id == 2:
            self.game.ws.instruct_id = -1
            self.game.play_background_music()
        elif self.game.ws.instruct_id == 3:
            self.game.ws.instruct_id = -1
            self.game.stop_background_music()
        elif self.game.ws.instruct_id == 1:
            self.game.ws.instruct_id = -1
            self.replay()

        # elif self.game.ws.instruct_id == 4:
        #     self.game.ws.instruct_id = -1
        #     self.game.show_top()

    def submit(self):
        import datetime
        import json

        # 获取当前日期
        current_date = datetime.date.today().isoformat()

        # 将成绩写入本地的 JSON 文件
        data = {
            'name': self.game.name,
            'score': self.game.score,
            'date': current_date
        }

        # 读取本地的 JSON 文件
        with open('top_scores.json', 'r', encoding='utf-8') as file:
            top_scores = json.load(file)

        # 更新排行榜数据
        all_scores = top_scores['all']
        today_scores = top_scores['today']
        inserted = False

        # 遍历 all_scores 列表，根据 score 的大小找到合适的位置插入数据
        for i, score in enumerate(all_scores):
            if data['score'] > score['score']:
                all_scores.insert(i, data)
                inserted = True
                break

        # 如果 data 的 score 比 all_scores 中的任何一个都小，将其添加到最后
        if not inserted:
            all_scores.append(data)

        # 遍历 today_scores 列表，根据 score 的大小找到合适的位置插入数据
        for i, score in enumerate(today_scores):
            if data['score'] > score['score']:
                today_scores.insert(i, data)
                break

        # 将更新后的数据写入本地的 JSON 文件
        with open('top_scores.json', 'w') as file:
            json.dump(top_scores, file)

        self.game.show_top()

    def replay(self):
        # 重新开始游戏
        self.pause_scheduler()
        self.game.reset()

    def recognize_instruction(self, ws_instance):
        if ws_instance.instruct_id == 1:
            ws_instance.instruct_id = -1
            self.replay()
