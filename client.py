import os
import sys
import asyncio

import IPython
from tabulate import tabulate
import linecache
import websockets
import json
import aiohttp
async def every(__seconds: float, func, *args, **kwargs):
    while True:
        await func(*args, **kwargs)
        await asyncio.sleep(__seconds)
async def input_(prompt:str='')->str:
    global game
    res = await asyncio.get_event_loop().run_in_executor(None, input, prompt)
    if res == '114514':
        IPython.embed()
        return await input_(prompt)
    if res.startswith('/'):
        token = input("token:")
        await game.send({"type":"command","data":{"token":token,"cmd":res}})
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

async def clear() -> None:
    await asyncio.sleep(0.5)
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

class ColorOutput:
    """彩色输出工具类（简写方法名版）"""
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

    def __init__(self, server_addr:str, player_name:str):
        self.wsurl = f"ws://{server_addr}/ws/{player_name}"
        self.gmsturl = f"http://{server_addr}/game/state"
        self.plsturl = f"http://{server_addr}/playerinfo/{player_name}"
        self.sbmtinvurl = f"http://{server_addr}/submit/investment/{player_name}"
        self.sbmtbidurl = f"http://{server_addr}/submit/bidding/{player_name}"
        self.sbmtbidwurl = f"http://{server_addr}/submit/bidding_wants/{player_name}"
        self.server_addr = server_addr
        self.o = ColorOutput()
        self.player_name = player_name
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
        self.websocket = None

    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.wsurl)
            self.o.g(f"已连接到服务器: {self.wsurl}")
            return True
        except Exception as e:
            self.o.r(f"连接服务器失败: {e}")
            sys.exit(0)

    async def fetch_url(self,url:str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def sync_game_state(self):
        game_state = await self.fetch_url(self.gmsturl)
        all_player = game_state['players']
        all_player_state = [await self.fetch_url(f"http://{self.server_addr}/playerinfo/{name}") for name in all_player]
        self.resource_values = game_state['values']
        self.players = {name: {
                'resources': defaultdict(int),
                'action_points': state['action_points'],
                'buildings': state['buildings'],
                'money': state['bank_money'],
            } for name,state in zip(all_player,all_player_state)}
        for i in range(len(all_player)):
            for x in all_player_state[i]['resources']:
                self.players[all_player[i]]['resources'][x] = all_player_state[i]['resources'][x]
        self.market = game_state['market']
        self.started = game_state['started']

    async def send(self, message, is_inv:bool=False, url:str=None):
        """发送消息到服务器"""
        if not self.websocket:
            self.o.r("未连接到服务器")
            return False
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url if url else (self.sbmtinvurl if is_inv else self.sbmtbidurl),json=message) as resp:
                    return await resp.json()
        except Exception as e:
            self.o.r(f"发送消息失败: {e}")
            return False

    async def receive_message(self):
        """接收服务器消息"""
        if not self.websocket:
            self.o.r("未连接到服务器")
            return None
        try:
            message = await self.websocket.recv()
            print(f"received {message}")
            await asyncio.sleep(0.5)
            return json.loads(message)
        except Exception as e:
            self.o.r(f"接收消息失败: {e}")
            return None
    async def handle_messages(self):
        while True:
            message = await self.receive_message()
            if message['type'] == 'notify':
                self.o.b(f"收到服务器通知: {message}")
                target = message['target']
                if target['type'] == 'data_required':
                    if target['phase'] == 1:
                        await self._handle_investment(target['epoch'])
                    if target['phase'] == 2:
                        await self._handle_bidding(target['epoch'])
                    if target['phase'] == -2:
                        await self._parse_bidding(target['epoch'])
                if target['type'] == 'event_choiced':
                    await self._trigger_event_card(target['epoch'],target['event'])
            if target['type'] == 'bidding_sorted':
                self.o.b("竞标排序成功，顺序是")
                self.o.b(target['sorted'])
    
    async def send_investment(self,inv):
        return await self.send({
            'type': 'investment',
            'data': {
                'player': self.player_name,
                'investment':inv
            }
        },is_inv=True)
    
    async def initialize_game(self):
        await clear()
        await self.display_game_state()
        self.current_deck = []
        self.market = []
        self.resource_values = {
            '钻石': 8, '金币': 6, '木材': 2,
            '矿石': 3, '食物': 1, '铁': 2
        }
        self.tmp_cnt_take = defaultdict(int)
        await self.connect()
        await self.sync_game_state()
        asyncio.create_task(every(3,self.sync_game_state))
        while not self.started:
            await asyncio.sleep(0.5)
        self.o.g("游戏开始!")
        await self.handle_messages()

    async def _draw_cards(self, num:int):
        """从牌堆抽取指定数量的卡"""
        drawn = []
        for _ in range(num):
            if not self.current_deck:
                await self._shuffle_deck()
            if self.current_deck:
                drawn.append(self.current_deck.pop())
        return drawn

    async def _shuffle_deck(self):
        """将资源卡转换为可抽取的列表"""
        self.current_deck = []
        for card_type, count in self.resource_deck.items():
            self.current_deck.extend([card_type] * count)
        random.shuffle(self.current_deck)

    async def _trigger_event_card(self, epoch:int,event:str):
        await clear()
        await self.display_game_state()
        if epoch not in [3,6,9,13,15,18,21,23,25,27]:
            self.o.b("本轮无需事件卡阶段")
            return
        self.o.b(f"当前是第 {epoch} 轮的特殊阶段事件卡。")
        self.o.b(f"本轮事件：{event}")
        self.sync_game_state()
        if event == "火山爆发":
            self.o.w(">> 移除市场上一半资源")
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
            #         bid = int(await input_())
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
            self.o.w(">> 所有玩家行动点+2")
            for player,data in self.players.items():
                data['action_points'] += 2
        self.o.b("事件回合结束")
        return None

    async def _update_resource_values(self, epoch:int):
        await asyncio.sleep(1)
        await clear()
        await self.display_game_state()
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
    async def _handle_bidding_wants(self,epoch:int):
        await clear()
        await self.display_game_state()
        while True:
            await clear()
            await self.display_game_state()
            self.o.w(">> 请输入您想要的资源（编号），输入ok退出")
            want = await input_("：")
            if want == "ok":
                resp = await self.send({"type":"bidding_wants","data":{"player":self.player_name,"want":'ok'}})
                break
            want = int(want)
            if not (0 <= want < len(self.market)):
                self.o.y("输入错误，请重新输入")
                continue
            resp = await self.send({"type":"bidding_wants","data":{"player":self.player_name,"want":want}})
            if resp['type'] == 'notify':
                target = resp['target']
                if target['type'] == "bidding_success":
                    self.o.g(f"拿取成功")
            elif resp['type'] == 'error':
                target = resp['target']
                if target['type'] == "bidding_error":
                    self.o.y(f"拿取失败，原因：")
                    if target['reason'] == 1:
                        self.o.y("物品被他人拿取")
                    if target['reason'] == 2:
                        self.o.y("行动点不足")

    async def _handle_bidding(self, epoch:int):
        await clear()
        await self.display_game_state()
        self.o.b(f"现在是第 {epoch} 轮的竞标阶段")
        self.o.w(">> 竞标开始")
        bids = {"player":self.player_name,"bid":None}
        player = self.player_name
        data = self.players[player]
        if data['action_points'] == 0:
            self.o.y(f"玩家 {player} 没有行动点，自动放弃")
            bid = 0
        else:
            bid = int(await input_(f"玩家 {player}，你的竞标价是："))
            if bid == 0:
                self.o.w(f"玩家 {player} 放弃竞标")
            elif data['action_points'] < bid:
                self.o.y("你无法承受此价格，竞标失败，自动放弃")
                bid = 0
        bids['bid'] = bid
        resp = await self.send({"type":"bidding","data":bids},is_inv=False)
        self.o.w(">> 您的价格已上交")
        await clear()
        await self.display_game_state()

    async def _handle_investment(self, epoch:int):
        """处理投资阶段"""
        await clear()
        await self.display_game_state()
        self.o.b(f"当前是第 {epoch} 回合的投资阶段")
        already_exchanged = []
        already_mined = []
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
                    self.o.y("市场上没有木材，增加失败")
            if "高级伐木场" in self.players[player]['buildings']:
                self.o.w(f">> 玩家 {player} 有高级伐木场，增加2木材")
                if self.current_deck.count("木材") <2:
                    self.o.y("市场上没有木材，增加失败")
                    self.players[player]['resources']['木材'] +=2
                    self.current_deck.remove("木材")
                    self.current_deck.remove("木材")
                else:
                    self.o.y("市场上没有木材，增加失败")
        await asyncio.sleep(3)
        if True:
            player = self.player_name
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
                self.o.b(">> 请输入投资类型：")
                action = await input_()
                resp = None
                if action == '1':
                    self.o.w(f">> 玩家 {player} 探索市场")
                    if self.players[player]['action_points'] <1:
                        self.o.y(f"玩家 {player} 没有足够的行动点数")
                        continue
                    resp = await self.send_investment("1")
                elif action == '2':
                    self.o.w(f">> 玩家 {player} 使用1食物兑换行动点*3")
                    if self.players[player]['resources']['食物'] < 1:
                        self.o.y(f"玩家 {player} 食物不足，兑换失败")
                        continue
                    resp = await self.send_investment("2")
                elif action == '3':
                    self.o.w(f">> 玩家 {player} 建造建筑")
                    if self.players[player]['action_points'] < 3:
                        self.o.y("你没行动点，建造失败")
                        continue
                    building = await input_("你要建造什么建筑：")
                    if building not in self.all_buildings:
                        self.o.y("建筑不存在")
                        continue
                    resp = await self.send_investment({"3":building})
                elif action == '8':
                    resp = await self.send_investment('ok')
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
                    resp = await self.send_investment('4')
                elif action == '5':
                    if "银行" not in self.players[player]['buildings']:
                        self.o.y("你没有银行存个蛋")
                        continue
                    item = await input_("你要存什么物品：")
                    amount = int(await input_("存几个："))
                    if item not in self.all_resources:
                        self.o.y("物品不存在")
                        continue
                    if self.players[player]['resources'][item] < amount:
                        self.o.y("背包里这个物品不够")
                        continue
                    resp = await self.send_investment({"5":f"{item}x{amount}"})
                elif action == '6':
                    ores = []
                    if "矿机" in self.players[player]['buildings']:
                        wants = []
                        for i in range(3):
                            for x in self.market:
                                if  x in ['钻石','金币','铁','矿石']:
                                    ores.append(x)
                            self.o.b("当前市场上有以下矿物：" + str(ores))
                            x = int(await input_("你要拿哪个（输入名称）："))
                            if x >= len(ores):
                                self.o.y(f"市场没有索引为 {i} 的物品")
                            wants.append(x)
                        resp = await self.send_investment({"6":wants})
                        self.players[player]['buildings'].remove("矿机")
                    elif "高级矿机" in self.players[player]['buildings']:
                        if player in already_mined:
                            self.o.y("你都挖过了")
                            continue
                        already_mined.append(player)
                        ores_in_market = [item for item in self.market if item in ['钻石','金币','铁','矿石']]
                        for i in range(2):
                            self.o.b("当前市场上有以下矿物：" + str(ores_in_market))
                            if not ores_in_market:
                                self.o.b("市场上没有多余矿物，跳过")
                                continue
                            try:
                                choice_index = int(await input_("你要拿哪个（输入编号）："))
                                if not (0 <= choice_index < len(ores_in_market)):
                                    self.o.y(f"市场没有索引为 {choice_index} 的物品")
                                    continue
                                wants.append(ores_in_market[choice_index])
                            except ValueError:
                                self.o.y("请输入有效的数字索引。")
                                continue
                        resp = await self.send_investment({"6":wants})
                    else:
                        self.o.y("你没有矿机挖个蛋")
                        continue
                elif action == '7':
                    if "铁镐" not in self.players[player]['buildings']:
                        self.o.y("你没有铁镐采什么啊")
                        continue
                    resp = await self.send_investment('7')
                if resp == None:
                    return
                if resp['type'] == 'notify':
                    target = resp['target']
                    if target['type'] == 'investment_success':
                        self.o.g(f"投资 {target['action']} 成功")
                elif resp['type'] == 'error':
                    target = resp['target']
                    match target['reason']:
                        case 1:
                            self.o.y(f"投资 {target['action']} 失败：没有足够行动点或者耗材")
                        case 2:
                            self.o.y(f"投资 {target['action']} 失败：物品/建筑不在范围内")
                        case 3:
                            self.o.y(f"投资 {target['action']} 失败：下标错误")
                        case 4:
                            self.o.y(f"投资 {target['action']} 失败：行动不存在")
                        case 5:
                            self.o.y(f"投资 {target['action']} 失败：采集数量超限")
                await asyncio.sleep(0.5)
                await clear()
                await self.sync_game_state()
                await self.display_game_state()
            self.o.w(f">> 玩家 {player} 投资结束")
            await clear()
            await self.display_game_state()
        self.o.b("投资阶段结束")

    async def _check_can_build(self, player_name:str, building:str):
        calc = self.__class__.ResourceValueCalculator(self.resource_values)
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

    async def _pay_to_build(self, player_name:str, pay:Dict):
        for k,v in pay.items():
            self.players[player_name]['resources'][k] -= v
            self.current_deck.append(k)

    async def _process_build(self, player_name:str, building:str):
        m, x = await self._check_can_build(player_name, building)
        if m:
            await self._pay_to_build(player_name, x)
            self.players[player_name]['buildings'].append(building)
            return True
        return False

    async def get_player_values(self):
        players = defaultdict(int)
        for player, data in self.players.items():
            resources = data['resources']
            resources_value = sum(self.resource_values[res] * qty for res, qty in resources.items())
            building_value = len(data['buildings'])*4
            players[player] = resources_value + building_value + data['money']*1.3
        return players

    async def start(self, epochs:int):
        if epochs > 30:
            epochs = 30
        self.o.g("游戏开始")
        for epoch in range(1, epochs+1):
            await self._handle_investment(epoch)
            await self._handle_bidding(epoch)
            await self._update_resource_values(epoch)
            await self._trigger_event_card(epoch)
            await asyncio.sleep(3)
            await clear()
        self.o.g("游戏结束")
        print(await self.get_player_values())

    async def _send_bidding_wants(self, want:int):
        return await self.send({
            "type":"bidding_wants",
            "data":{
                "player":self.player_name,
                "want":want
            }
        },url=self.sbmtbidwurl,is_inv=False)

    async def _parse_bidding(self, epochs: int):
        await self.sync_game_state()
        await clear()
        await self.display_game_state()
        self.o.b(f"当前是第{epochs}轮的竞标拿取阶段，现在轮到你拿取了")
        while True:
            want = await input_("你要拿取第几个物品？（输入编号），完成请输入ok：")
            if want == 'ok':
                await self._send_bidding_wants(want)
                return
            want = int(want)
            if want < 0 or want >= len(self.market):
                self.o.y("请输入有效的物品编号。")
                continue
            res = await self._send_bidding_wants(want)
            if res['type'] == 'notify':
                if res['target']['type'] == 'bidding_success':
                    self.o.g("物品拿取成功")
                    await self.sync_game_state()
            elif res['type'] == 'error':
                target = res['target']
                match target['reason']:
                    case 1:
                        self.o.y("物品不存在")
                    case 2:
                        self.o.y("行动点不足，将自动退出")
                        return
            await clear()
            await self.sync_game_state()
            await self.display_game_state()

    async def display_game_state(self):
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
global game
if __name__ == '__main__':
    async def main():
        global game
        server_addr = input("请输入你的服务器地址：")
        if server_addr == '':
            server_addr = "localhost:8000"
        player_name = await input_("请输入你的玩家名称: ")
        game = ResourceIsland(server_addr, player_name)
        await game.initialize_game()
    
    asyncio.run(main())
