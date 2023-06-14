# -*- coding: utf-8 -*-

import cocos
from defines import *
import json
import datetime


class Gameover(cocos.layer.ColorLayer):
    def __init__(self, game):
        super(Gameover, self).__init__(0, 0, 0, 255, WIDTH, HEIGHT)
        self.game = game
        self.billboard = None
        self.score = cocos.text.Label(u'分数：%d' % self.game.score,
                                      font_name=FONTS,
                                      font_size=36)
        self.score.position = 200, 340
        self.add(self.score)

        menu = cocos.menu.Menu(u'你挂了……')
        menu.font_title['font_name'] = FONTS
        menu.font_item['font_name'] = FONTS
        menu.font_item_selected['font_name'] = FONTS
        self.name = cocos.menu.EntryMenuItem(u'大虾请留名：', self.input_name, self.game.name)
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
        logo.position = 550, 100
        self.add(logo, 99999)

    def input_name(self, txt):
        self.game.name = txt
        if len(txt) > 16:
            self.game.name = txt[:16]

    def submit(self):
        # 获取当前日期
        current_date = datetime.date.today().isoformat()

        # 将成绩写入本地的JSON文件
        data = {
            'name': self.game.name,
            'score': self.game.score,
            'date': current_date
        }

        # 读取本地的JSON文件
        with open('top_scores.json', 'r') as file:
            top_scores = json.load(file)

        # 更新排行榜数据
        top_scores['all'].append(data)
        top_scores['today'].append(data)

        # 将更新后的数据写入本地的JSON文件
        with open('top_scores.json', 'w') as file:
            json.dump(top_scores, file)

        self.game.show_top()

    def replay(self):
        # 重新开始游戏
        self.game.reset()
