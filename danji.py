import os
import sys
import time

import IPython
from tabulate import tabulate
import sys
import linecache
def input_(prompt:str='')->str:
    res = input(prompt)
    if res == '114514':
        IPython.embed()
        return input_(prompt)
    return res
class Tracer:
    def __init__(self):
        self._indent = 0
        self._last_line = None
        self._current_file = None
    def trace(self, frame, event, arg):
        # 处理函数调用事件
        if event == 'call':
            return self.handle_call(frame)
        # 处理行执行事件
        elif event == 'line':
            return self.handle_line(frame)
        # 处理函数返回事件
        elif event == 'return':
            return self.handle_return(frame, arg)
        return self.trace
    def handle_call(self, frame):
        # 获取调用信息
        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name
        # 跳过不需要跟踪的文件
        if self.should_skip(filename):
            return None
        # 打印调用信息
        print(f"{'  ' * self._indent}→ {func_name}() [调用 @ {filename}:{frame.f_lineno}]")
        self._indent += 1
        self._current_file = filename
        return self.trace
    def handle_line(self, frame):
        # 获取当前行信息
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        # 跳过不需要跟踪的文件
        if self.should_skip(filename):
            return self.trace
        # 获取源代码行
        line = linecache.getline(filename, lineno).strip()
        # 避免重复打印同一行(可能由于循环)
        if (filename, lineno) != self._last_line:
            print(f"{'  ' * self._indent}• {filename}:{lineno} {line}")
            self._last_line = (filename, lineno)
        return self.trace
    def handle_return(self, frame, arg):
        # 获取返回信息
        code = frame.f_code
        filename = code.co_filename
        # 跳过不需要跟踪的文件
        if self.should_skip(filename):
            return
        self._indent = max(self._indent - 1, 0)
        print(f"{'  ' * self._indent}← 返回: {arg}")
    def should_skip(self, filename):
        # 跳过标准库和Python内置文件
        return (filename.startswith('<') or
                'site-packages' in filename or
                'lib/python' in filename or
                filename.endswith('.pyc'))

def start_tracing():
    """启用跟踪"""
    tracer = Tracer()
    sys.settrace(tracer.trace)
    return tracer
def stop_tracing():
    """禁用跟踪"""
    sys.settrace(None)

if os.getenv("RSIDEBUG") == '1':
    start_tracing()
def show_values(resource_values):
    table = tabulate(
        [[res, value] for res, value in resource_values.items()],
        headers=["资源类型", "当前价值"],
    )
    print(table)
def delete_last_lines(n=1):
    """使用ANSI转义码删除最后n行"""
    for _ in range(n):
        sys.stdout.write('\x1b[1A')  # 光标上移一行
        sys.stdout.write('\x1b[2K')  # 清除整行
def clear() -> None :time.sleep(0.5);import os;os.system('cls' if os.name == 'nt' else 'clear')
class ColorOutput:
    """
    彩色输出工具类（简写方法名版）
    使用示例：
    co = ColorOutput()
    co.r("红色文字")
    co.g("绿色文字")
    """
    # ANSI 颜色代码（保持原样）
    COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'reset': '\033[0m'
    }
    def _color_wrap(self, text: str, color_code: str) -> str:
        return f"{color_code}{text}{self.COLORS['reset']}"
    def k(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['black']))  # 黑 (black)
    def r(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['red']))  # 红 (red)
    def g(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['green']))  # 绿 (green)
    def y(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['yellow']))  # 黄 (yellow)
    def b(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['blue']))  # 蓝 (blue)
    def m(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['magenta']))  # 品红 (magenta)
    def c(self, text: str) -> None: print(self._color_wrap(text, self.COLORS['cyan']))  # 青 (cyan)
    def w(self, text: str, end: str=None) -> None: print(self._color_wrap(text, self.COLORS['white']), end=end)  # 白 (white)

import random
from collections import defaultdict
from typing import Dict

class ResourceIsland:
    class ResourceValueCalculator:
        def __init__(self, resource_values):
            self.resource_values = resource_values

        def calculate_equivalent_resources(self, player_resources, target_value):
            """
            计算等值物资组合（动态规划优化版）
            :param player_resources: 玩家当前资源 {'钻石':1, '铁':3}
            :param target_value: 需要匹配的目标价值
            :return: 所有可行的资源组合列表，按最接近目标值排序
            """
            # 过滤掉零值资源和保留卡
            available_res = {
                res: qty for res, qty in player_resources.items()
                if qty > 0 and not res.startswith('保留')
            }

            # 初始化动态规划表：dp[value] = 最小资源组合
            dp = defaultdict(list)
            dp[0] = [{}]  # 初始状态：价值为0时，资源组合为空

            # 遍历每种资源
            for res, max_qty in available_res.items():
                res_value = self.resource_values[res]
                current_dp = list(dp.items())  # 复制当前状态，避免遍历时修改

                # 遍历当前所有可能的价值
                for value, combos in current_dp:
                    # 尝试添加1到max_qty个当前资源
                    for qty in range(1, max_qty + 1):
                        new_value = value + res_value * qty
                        new_combo = [{
                            **combo,
                            res: combo.get(res, 0) + qty
                        } for combo in combos]

                        # 如果新价值未记录，或找到更小的组合
                        if new_value not in dp or len(new_combo[0]) < len(dp[new_value][0]):
                            dp[new_value] = new_combo

            # 收集所有≥目标价值的组合
            valid_combinations = []
            for value, combos in dp.items():
                if value >= target_value:
                    for combo in combos:
                        valid_combinations.append({
                            'resources': combo,
                            'total_value': value,
                            'difference': value - target_value
                        })

            # 按最接近目标值排序
            return sorted(valid_combinations, key=lambda x: (x['difference'], len(x['resources'])))

        def validate_payment(self, payment, target_value):
            """
            验证支付是否满足等值要求
            :param payment: 玩家选择的支付组合 {'钻石':1, '铁':2}
            :param target_value: 目标价值
            :return: Tuple (是否有效, 差额)
            """
            total = sum(self.resource_values[res] * qty for res, qty in payment.items())
            return (total >= target_value, total - target_value)

    def __init__(self):
        self.o = ColorOutput()
        self.all_buildings = [
            '矿机', '农场', '伐木场',
            '铁镐', '农田', '高级伐木场',
            '高级矿机', '无敌农场', '银行','炮台'
        ]
        self.resource_deck = {
            '金币': 10, '木材': 100,
            '矿石': 200, '食物': 200,
            '钻石': 10, '铁': 300,
        }
        self.all_resources = [
            '金币', '木材', '矿石', '食物',
            '钻石', '铁'
        ]
        self.event_deck = [
            '火山爆发', '海盗掠夺', '海盗掠夺', '天降饥荒',
            '天降饥荒', '出现宝藏', '祝福事件', '祝福事件'
        ]
        self.players = {}
        self.recipes:Dict[str,Dict] = {
            "矿机": {"铁":5,"铁镐":1},
            "炮台": {"金币":2},
            "伐木场": {"铁镐":1,"铁":4},
            "铁镐":{"铁":2},
            "高级矿机":{"矿机":1,"金币":2},
            "高级伐木场":{"伐木场":1,"金币":2},
            "农场":{"金币":3},
            "无敌农场":{"农场":1,"金币":8},
            "银行":{"金币":2}
        }
        self.event_immunitie = [3,6,9,13,15]
        self.current_deck = []
        self.market = []
        self.resource_values = {
            '钻石': 8, '金币': 6, '木材': 2,
            '矿石': 3, '食物': 1, '铁': 2
        }
        self.ore_choices = [
            '钻石','金币',
            '铁','铁','铁','铁','铁',
            '无','无','无'
        ]
        self.tmp_cnt_take = {}

    def reset_game(self):
        self.current_deck = []
        self.market = []
        self.resource_values = {
            '钻石': 8, '金币': 6, '木材': 2,
            '矿石': 3, '食物': 1, '铁': 2
        }
        self.tmp_cnt_take = defaultdict(int)

    def initialize_game(self):
        clear()
        self.display_game_state()
        self.reset_game()
        player_names = []
        for i in range(4):
            name = input_(f"请输入玩家{i+1}的名字：")
            if not name or name == ' ' or name in player_names:
                continue
            player_names.append(name)
        if not isinstance(player_names, list) or len(player_names) < 2:
            raise ValueError("需要2-4名玩家")
        self.o.b("游戏进行初始化")
        self.o.w(">> 每个玩家获得3行动点、5食物")
        self.resource_deck["食物"] -= len(player_names) * 5
        self.players = {
            name: {
                'resources': defaultdict(int),
                'action_points': 3,
                'buildings': [],
                'money': 0,
            } for name in player_names
        }
        for data in self.players.values():
            data['resources']['食物']+=5
        self.o.w(">> 洗牌")
        self._shuffle_deck()
        self.o.w(">> 抽取10牌到市场")
        self.market = self._draw_cards(10)
        self.o.b("初始化完成")
        clear()

    def _draw_cards(self, num:int):
        """从牌堆抽取指定数量的卡"""
        drawn = []
        for _ in range(num):
            if not self.current_deck:
                self._shuffle_deck()
            if self.current_deck:
                drawn.append(self.current_deck.pop())
        return drawn

    def _shuffle_deck(self):
        """将资源卡转换为可抽取的列表"""
        self.current_deck = []
        for card_type, count in self.resource_deck.items():
            self.current_deck.extend([card_type] * count)
        random.shuffle(self.current_deck)

    def _trigger_event_card(self, epoch:int):
        clear()
        self.display_game_state()
        if epoch not in [3,6,9,13,15,18,21,23,25,27]:
            self.o.b("本轮无需事件卡阶段")
            return
        self.o.b(f"当前是第 {epoch} 轮的特殊阶段事件卡。")
        event_deck = self.event_deck
        if epoch in self.event_immunitie:
            self.o.b(f"当前海岛掠夺、天降饥荒可豁免")
            self.o.w(f">> 删除海盗掠夺、天降饥荒")
            while "海盗掠夺" in event_deck:
                self.event_deck.remove("海盗掠夺")
            while "天降饥荒" in event_deck:
                self.event_deck.remove("天降饥荒")
        self.o.w(f">> 正在挑选事件卡")
        event = random.choice(event_deck)
        self.o.b(f"本轮事件：{event}")
        if event == "火山爆发":
            self.o.w(f">> 移除市场上一半资源")
            self.market = self.market[:len(self.market)//2]
        if event == "海盗掠夺":
            calc = ResourceIsland.ResourceValueCalculator(self.resource_values)
            died_player = []
            for player,data in self.players.items():
                can_pay = calc.calculate_equivalent_resources(data['resources'],3*self.resource_values['金币'])
                if "炮台" in data['buildings']:
                    data['buildings'].remove("炮台")
                    self.o.w(f">> 玩家 {player} 使用炮台防御海盗袭击")
                    continue
                if not can_pay:
                    died_player.append(player)
                    continue
                for item,amount in can_pay[0]['resources'].items():
                    self.players[player]['resources'][item] -= amount
                    self.o.w(f">> 玩家 {player} 支付 {amount} 个 {item}")
            for x in died_player:
                self.o.r(f">> 玩家 {x} 无法支付，死亡")
                self.players.pop(x)
        if event == "天降饥荒":
            died_player = []
            for player,data in self.players.items():
                if data['resources']['食物'] < 3:
                    died_player.append(player)
                    continue
                self.o.w(f">> 玩家 {player} 支付 3个食物")
                data['resources']['食物'] -= 3
            for x in died_player:
                self.o.r(f">> 玩家 {x} 没有食物，死亡")
                self.players.pop(x)
        if event == "出现宝藏":
            return
            # calc = ResourceIsland.ResourceValueCalculator(self.resource_values)
            # self.o.w(f">> 请各位玩家出价")
            # bids = []
            # for x in self.players.keys():
            #     while True:
            #         self.o.w(f">> 玩家 {x} 你的价格是：")
            #         bid = int(input_())
            #         vaild = calc.calculate_equivalent_resources(self.players[x]['resources'], bid)
            #         if not vaild:
            #             self.o.y(f">> 玩家 {x} 你无法承受这个价值，请重新输入")
            #             continue
            #         if bid == 0:
            #             self.o.w(f">> 玩家 {x} 放弃")
            #             break
            #         bids.append({"player":x,"bid":bid,"will_pay":vaild[0]})
            #         break
            # bids.sort(key=lambda x:x['bid'],reverse=True)

        if event == "祝福事件":
            self.o.w(f">> 所有玩家行动点+2")
            for player,data in self.players.items():
                data['action_points'] += 2
        self.o.b("事件回合结束")
        return None

    def _update_resource_values(self,epoch:int):
        time.sleep(1)
        clear()
        self.display_game_state()
        print(self.market)
        if epoch % 3 != 0:
            self.o.b("本轮无需价格波动")
            return
        self.o.b(f"现在是第 {epoch} 轮的价值波动阶段")
        for k in self.resource_values.keys():
            if self.tmp_cnt_take[k] == 0:
                self.o.w(f">> 资源 {k} 未被拿取，价格+1")
                self.resource_values[k]+=1
        for k in self.resource_values.keys():
            if self.tmp_cnt_take[k] >= 7:
                if self.resource_values[k] == 1:
                    continue
                self.o.w(f">> 资源 {k} 被拿去许多，价格-1")
                self.resource_values[k] -= 1

    def _handle_bidding(self, epoch:int):
        clear()
        self.display_game_state()
        self.o.b(f"现在是第 {epoch} 轮的竞标阶段")
        self.o.w(f">> 竞标开始")
        bids = []
        for player,data in self.players.items():
            if data['action_points'] == 0:
                self.o.y(f"玩家 {player} 没有行动点，自动放弃")
            bid = int(input_(f"玩家 {player}，你的竞标价是："))
            if bid == 0:
                self.o.w(f"玩家 {player} 放弃竞标")
                continue
            if data['action_points'] < bid:
                self.o.y("你无法承受此价格，请重新输入")
                bid = int(input_(f"玩家 {player}，你的竞标价是："))
                if bid == 0:
                    self.o.w(f"玩家 {player} 放弃竞标")
                    continue
            bids.append({"player":player, "bid":bid} )
        self.o.w(f">> 价格统计完毕，排序中")
        bids.sort(key=lambda x:x['bid'],reverse=True)
        for x in bids:
            self.o.w(f">> 计算出玩家 {x['player']} 现在开始拿取")
            can = self.players[x['player']]['action_points'] // x['bid']
            self.o.b(f"玩家 {x['player']} 你可以拿取 {can} 个物品")
            for n in range(self.players[x['player']]['action_points'] // x['bid']):
                if not len(self.market):
                    for k in self.players.keys():
                        if self.players[k]['action_points']:
                            self.players[k]['action_points'] -= 1
                            self.market.extend(self._draw_cards(2))
                if self.players[x['player']]['action_points'] < x['bid']:
                    break
                self.o.b(f"玩家 {x['player']} 你还可以拿取 {can-n*x['bid']} 个物品")
                self.o.w(f">> 请选择你要拿取的物品下标或者输入ok推出")
                take = input_()
                if take == 'ok':
                    break
                take = int(take)
                self.tmp_cnt_take[self.market[take]] +=1
                self.players[x['player']]['action_points'] -= x['bid']
                self.players[x['player']]['resources'][self.market[take]] +=1
                self.market.pop(take)
                clear()
                self.display_game_state()
        self.o.b(f"竞标阶段结束")

    def _handle_investment(self, epoch:int):
        """处理投资阶段"""
        clear()
        self.display_game_state()
        self.o.b(f"当前是第 {epoch} 回合的投资阶段")
        already_exchanged = []
        already_mined = []
        if not self.market:
            self.o.y(f"当前市场上没有物品，正在强制补充")
            for k in self.players.keys():
                if self.players[k]['action_points']:
                    self.players[k]['action_points'] -= 1
                    self.market.extend(self._draw_cards(2))
            if self.market:
                self._handle_investment(epoch)
            return
        if len(set(self.market)) == 1 and self.market:
            self.o.y(f"市场上只剩下1种资源，正在放入资源堆")
            self.current_deck.extend(self.market)
            self.market = []
            self._handle_investment(epoch)
            return
        for player in self.players.keys():
            if "农场" in self.players[player]['buildings']:
                self.o.w(f">> 玩家 {player} 有农场，免费增加2行动点")
                self.players[player]['action_points'] += 2
                already_exchanged.append(player)
            if "无敌农场" in self.players[player]['buildings']:
                self.o.w(f">> 玩家 {player} 有无敌农场，增加5行动点")
                self.players[player]['action_points'] += 5
                already_exchanged.append(player)
            if "伐木场" in self.players[player]['buildings']:
                self.o.w(f">> 玩家 {player} 有伐木场，增加1木材")
                if "木材" in self.market:
                    self.players[player]['resources']['木材'] +=1
                    self.market.remove("木材")
                else:
                    self.o.y(f"市场上没有木材，增加失败")
            if "高级伐木场" in self.players[player]['buildings']:
                self.o.w(f">> 玩家 {player} 有高级伐木场，增加2木材")
                if self.current_deck.count("木材") <2:
                    self.o.y(f"市场上没有木材，增加失败")
                    self.players[player]['resources']['木材'] +=2
                    self.current_deck.remove("木材")
                    self.current_deck.remove("木材")
                else:
                    self.o.y(f"市场上没有木材，增加失败")
        time.sleep(3)
        for player,data in self.players.items():
            while True:
                self.o.w(f">> 请玩家 {player} 进行投资")
                table = tabulate([['1', '探索',1],
                                    ['2', '兑换',0],
                                   ['3', '建造',3],
                                   ['4', '开盲盒',1],
                                    ['5', '存钱',0],
                                    ['6', '挖矿',0],
                                    ['7', '铁镐',0],
                                    ['8', '结束回合',0]
                                  ],headers=["编号","操作","消耗"])
                print(table)
                self.o.b(f">> 请输入投资类型：")
                action = input_()
                if action == '1':
                    self.o.w(f">> 玩家 {player} 探索市场")
                    if self.players[player]['action_points'] <1:
                        self.o.y(f"玩家 {player} 没有足够的行动点数")
                        continue
                    self.players[player]['action_points'] -= 1
                    self.market.extend(self._draw_cards(2))
                elif action == '2':
                    self.o.w(f">> 玩家 {player} 使用1食物兑换行动点*2")
                    if self.players[player]['resources']['食物'] < 1:
                        self.o.y(f"玩家 {player} 食物不足，兑换失败")
                        continue
                    if player in already_exchanged:
                        self.o.y(f"你已经兑换过了")
                    self.players[player]['resources']['食物'] -= 1
                    self.players[player]['action_points'] += 2
                    self.current_deck.append('食物')
                elif action == '3':
                    self.o.w(f">> 玩家 {player} 建造建筑")
                    if self.players[player]['action_points'] < 3:
                        self.o.y(f"你没行动点，建造失败")
                        continue
                    self.players[player]['action_points'] -= 3
                    building = input_("你要建造什么建筑：")
                    if building not in self.all_buildings:
                        self.o.y(f"建筑不存在")
                        continue
                    else :
                        if not self._process_build(player,building):
                            self.players[player]['action_points'] += 3
                elif action == '8':
                    break
                elif action == '4':
                    if self.players[player]['action_points'] < 1:
                        self.o.y(f"玩家 {player} 没有足够的行动点数")
                        continue
                    if self.players[player]['resources']['矿石'] < 1:
                        self.o.y(f"玩家 {player} 没有足够的矿石")
                        continue
                    self.players[player]['action_points'] -= 1
                    self.players[player]['resources']['矿石'] -= 1
                    award = random.choice(self.ore_choices)
                    if award == '无':
                        continue
                    self.players[player]['resources'][award] += 1
                    self.current_deck.remove(award)
                    self.current_deck.append("矿石")
                elif action == '5':
                    if "银行" not in self.players[player]['buildings']:
                        self.o.y("你没有银行存个蛋")
                        continue
                    item = input_("你要存什么物品：")
                    amount = int(input_("存几个："))
                    if item not in self.all_resources:
                        self.o.y(f"物品不存在")
                        continue
                    if self.players[player]['resources'][item] < amount:
                        self.o.y("背包里这个物品不够")
                        continue
                    value = self.players[player]['resources'][item] * \
                        self.resource_values[item]
                    value *= amount
                    self.players[player]['money'] += value
                    self.players[player]['resources'][item] -= amount
                elif action == '6':
                    ores = []
                    for i in self.market:
                        if  i in ['钻石','金币','铁','矿石']:
                            ores.append(i)
                    if "矿机" in self.players[player]['buildings']:
                        for i in range(3):
                            self.o.b(f"当前市场上有以下矿物：" + str(ores))
                            x = int(input_("你要拿哪个："))
                            if x >= len(ores):
                                self.o.y(f"市场没有索引为 {i} 的物品")
                            self.players[player]['resources'][ores[x]] += 1
                            self.market.remove(ores[x])
                            ores.pop(x)
                        self.players[player]['buildings'].remove("矿机")
                    elif "高级矿机" in self.players[player]['buildings']:
                        if player in already_mined:
                            self.o.y("你都挖过了")
                            continue
                        already_mined.append(player)
                        for i in range(2):
                            self.o.b(f"当前市场上有以下矿物：" + str(ores))
                            x = int(input_("你要拿哪个："))
                            if not ores:
                                self.o.b(f"市场上没有多余矿物，跳过")
                                continue
                            if x >= len(ores):
                                self.o.y(f"市场没有索引为 {x} 的物品")
                            self.players[player]['resources'][ores[x]] += 1
                            self.market.remove(ores[x])
                            ores.pop(x)
                    else:
                        self.o.y("你没有矿机挖个蛋")
                        continue
                elif action == '7':
                    if "铁镐" not in self.players[player]['buildings']:
                        self.o.y(f"你没有铁镐采什么啊")
                        continue
                    self.players[player]['resources'][self.current_deck[0]] += 1
                    self.current_deck.pop(0)
                    self.players[player]['buildings'].remove("铁镐")
                elif action == '114514':
                    self.o.r(f"开始调试")
                    from IPython import embed
                    embed()
                clear()
                self.display_game_state()
            self.o.w(f">> 玩家 {player} 投资结束")
            clear()
            self.display_game_state()
        self.o.b("投资阶段结束")

    def _check_can_build(self, player_name:str, building:str):
        calc = ResourceIsland.ResourceValueCalculator(self.resource_values)
        cost = 0
        required_building = {}
        required_resources = {}
        for k,v in self.recipes[building].items():
            if k in self.all_buildings:
                required_building[k]=v
            if k in self.all_resources:
                required_resources[k]=v
        for k,v in required_resources.items():
            cost += self.resource_values[k] * v
        res_vaild = calc.calculate_equivalent_resources(self.players[player_name]['resources'],cost)
        if not res_vaild:
            return False,None
        for k,v in required_building.items():
            if k in self.players[player_name]['buildings']:
                if self.players[player_name]['buildings'].count(v):
                    return False ,None
                else :
                    for i in range(v):
                        self.players[player_name]['buildings'].remove(k)
        return True,res_vaild[0]['resources']

    def _pay_to_build(self, player_name:str, pay:Dict):
        for k,v in pay.items():
            self.players[player_name]['resources'][k] -= v
            self.current_deck.append(k)

    def _process_build(self,player_name:str, building:str):
        m , x=self._check_can_build(player_name,building)
        if m:
            self._pay_to_build(player_name,x)
            self.players[player_name]['buildings'].append(building)
            return True
        return False

    def get_player_values(self):
        players = defaultdict(int)
        for player, data in self.players.items():
            resources = data['resources']
            resources_value = sum(self.resource_values[res] * qty for res, qty in resources.items())
            building_value = len(data['buildings'])*4
            players[player] = resources_value + building_value + data['money']*1.3
        return players

    def start(self,epochs:int):
        if epochs > 30:
            epochs = 30
        self.o.g("游戏开始")
        for epoch in range(1,epochs+1):
            self._handle_investment(epoch)
            self._handle_bidding(epoch)
            self._update_resource_values(epoch)
            self._trigger_event_card(epoch)
            time.sleep(3)
            clear()
        self.o.g("游戏结束")
        print(self.get_player_values())

    def display_game_state(self):
        """优化后的游戏状态显示方法"""
        # 显示玩家信息（精简版）
        self.o.b("=== 玩家状态 ===")
        for player, data in self.players.items():
            self.o.w(f"{player}: AP={data['action_points']} $={data['money']}", end='')
            self.o.w(f" 建筑:{data['buildings']}", end='')
            res = [f"{k[:2]}:{v}" for k, v in data['resources'].items() if v > 0]
            self.o.w(f" 资源:{','.join(res)}")

        # 显示资源价值
        self.o.b("=== 资源价值 ===")
        show_values(self.resource_values)

        # 显示市场
        self.o.b("=== 市场 ===")
        for i, item in enumerate(self.market):
            self.o.w(f"{i}: {item}",end=', ')

        # 添加分隔线
        self.o.b("\n" + "=" * 30 + "\n")

if __name__ == '__main__':
    game = ResourceIsland()
    game.initialize_game()
    game.start(30)
