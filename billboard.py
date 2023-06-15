# -*- coding: utf-8 -*-

import cocos
import json
from defines import *


class Billboard(cocos.layer.ColorLayer):
    def __init__(self, game):
        super(Billboard, self).__init__(0, 0, 0, 255, WIDTH, HEIGHT)
        self.game = game

        self.loading = cocos.text.Label(u'加载中...', font_name=FONTS, font_size=20)
        self.loading.position = 400, 360
        self.add(self.loading)

        self.schedule_interval(self.get_top, 0.5)

    def get_top(self, dt):
        # 从本地的JSON文件获取排行榜数据
        self.remove(self.loading)
        self.unschedule(self.get_top)

        # 读取本地的JSON文件
        with open('top_scores.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        top_a = data['all']
        # top_t = data['today']

        i = 0
        for d in top_a:
            i += 1
            rank = "No."+str(i)
            t = cocos.text.Label(
                '{:<10s} {:<10s} {:<10s} {}'.format(rank, str(d['name']), str(d['score']), d['date']),
                font_name=FONTS, font_size=18)

            t.position = 240, 420 - i * 26
            self.add(t)
            if i >= 6:
                break

        # i = 0
        # for d in top_t:
        #     i += 1
        #     t = cocos.text.Label(u'%-10s %-10s %s' % (d['name'], d['score'], d['date']),
        #                          font_name=FONTS, font_size=18)
        #     t.position = 120, 650 - i * 26
        #     self.add(t)
        #     if i == 1:
        #         self.game.top = d['name'], d['score']

        name = ''
        if self.game.name:
            name = self.game.name + u'，'
        rank = cocos.text.Label(name + u'你的成绩 %d 打败了银河系中 %s%% 的鼠鼠！' % (self.game.score, 99),
                                font_name=FONTS,
                                font_size=16)
        rank.position = 240, 520
        self.add(rank)

        top_all = cocos.text.Label(u'排行榜',
                                   font_name=FONTS,
                                   font_size=30)
        top_all.position = 400, 450
        self.add(top_all)

        # top_today = cocos.text.Label(u'今日排名',
        #                              font_name=FONTS,
        #                              font_size=20)
        # top_today.position = 300, 580
        # self.add(top_today)

        menu = cocos.menu.Menu()
        menu.font_item['font_name'] = FONTS
        menu.font_item_selected['font_name'] = FONTS
        replay = cocos.menu.MenuItem(u'再来一次', self.replay)
        replay.y = -200
        menu.create_menu([replay])
        self.add(menu)

    def replay(self):
        # 重新开始游戏
        self.game.reset()

    def show(self):
        # 显示排行榜
        self.visible = True
