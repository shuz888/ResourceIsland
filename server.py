import asyncio
import dataclasses
from email.policy import default
from operator import truediv
import random
from collections import defaultdict
from threading import Thread
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

def process_command(command_string):
    """
    处理以'/'开头的指令，并返回指令名和参数列表
    参数:
        command_string (str): 要处理的指令字符串，例如 "/kick abc"
    返回:
        tuple: (指令名, 参数列表) 的元组，例如 ("kick", ["abc"])
        如果不是有效指令（不以'/'开头），则返回 (None, [])
    """
    # 检查是否是有效的指令（以'/'开头）
    if not command_string.startswith('/'):
        return None, []
    # 移除前缀'/'
    command_without_prefix = command_string[1:].strip()
    # 如果指令为空（例如只有'/'），则返回空指令
    if not command_without_prefix:
        return "", []
    # 分割指令名和参数
    parts = command_without_prefix.split()
    command_name = parts[0]
    arguments = parts[1:] if len(parts) > 1 else []
    return command_name, arguments

@dataclasses.dataclass
class Player:
    ws:WebSocket
    resources: Dict[str, int] = dataclasses.field(default_factory=dict)
    action_points: int = 3
    buildings: List[str] = dataclasses.field(default_factory=list)
    bank_money: int = 0

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
        available_res = {
            res: qty for res, qty in player_resources.items()
            if qty > 0 and not res.startswith('保留')
        }
        dp = defaultdict(list)
        dp[0] = [{}]
        for res, max_qty in available_res.items():
            res_value = self.resource_values[res]
            current_dp = list(dp.items())
            for value, combos in current_dp:
                for qty in range(1, max_qty + 1):
                    new_value = value + res_value * qty
                    new_combo = [{
                        **combo,
                        res: combo.get(res, 0) + qty
                    } for combo in combos]
                    if new_value not in dp or len(new_combo[0]) < len(dp[new_value][0]):
                        dp[new_value] = new_combo
        valid_combinations = []
        for value, combos in dp.items():
            if value >= target_value:
                for combo in combos:
                    valid_combinations.append({
                        'resources': combo,
                        'total_value': value,
                        'difference': value - target_value
                    })
        return sorted(valid_combinations, key=lambda x: (x['difference'], len(x['resources'])))
# 共享游戏状态（替换你原有的GameRoom）
class GameState:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.market: List[str] = []
        self.event_immunitie = [3, 6, 9, 13, 15]
        self.current_deck = []
        self.epoch = 1
        self.phase = 1
        self.resource_values = {
            '钻石': 8, '金币': 6, '木材': 2,
            '矿石': 3, '食物': 1, '铁': 2
        }
        self.tmp_cnt_take = defaultdict(int)
        self.started = False
class Game:
    def __init__(self):
        self.ore_choices = [
            '钻石','金币',
            '铁','铁','铁','铁','铁',
            '无','无','无'
        ]
        self.state: GameState = GameState()
        self.all_buildings = [
            '矿机', '农场', '伐木场',
            '铁镐', '农田', '高级伐木场',
            '高级矿机', '无敌农场', '银行', '炮台'
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
        self.recipes: Dict[str, Dict] = {
            "矿机": {"铁": 5, "铁镐": 1},
            "炮台": {"金币": 2},
            "伐木场": {"铁镐": 1, "铁": 4},
            "铁镐": {"铁": 2},
            "高级矿机": {"矿机": 1, "金币": 2},
            "高级伐木场": {"伐木场": 1, "金币": 2},
            "农场": {"金币": 3},
            "无敌农场": {"农场": 1, "金币": 8},
            "银行": {"金币": 2}
        }
        self._player_resp = asyncio.Queue()
        self._gm_cmd = asyncio.Queue()
        self._game_task = None
        self._server_resp = asyncio.Queue()

    async def _shuffle_deck(self):
        self.state.current_deck = []
        for card_type, count in self.resource_deck.items():
            self.state.current_deck.extend([card_type] * count)
        random.shuffle(self.state.current_deck)

    async def _draw_cards(self, num:int):
        """从牌堆抽取指定数量的卡"""
        drawn = []
        for _ in range(num):
            if not self.state.current_deck:
                await self._shuffle_deck()
            if self.state.current_deck:
                drawn.append(self.state.current_deck.pop())
        return drawn

    async def broadcast(self, data):
        for player in self.state.players.values():
            await player.ws.send_json(data)

    async def _game_loop(self):
        await self._shuffle_deck()
        self.state.market.extend(await self._draw_cards(20))
        for player in game.state.players.keys():
            self.state.players[player].resources['食物'] += 10
        await self.broadcast({"type":"notify","target":{"type":"game_start"}})
        # while self.state.epoch <= 30: 
        while True:
            self.state.phase = 1
            if self.state.phase == 1:
                await self.broadcast({"type": "notify", "target": {"type": "phase_changed","epoch":self.state.epoch,"phase":self.state.phase}})
                await self.broadcast({"type": "notify", "target": {"type": "data_required", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self._handle_investment()
                self.state.phase = 2
            if self.state.phase == 2:
                await self.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self.broadcast({"type": "notify", "target": {"type": "data_required", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self._handle_bidding()
                self.state.phase = -2
                await self.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self._parse_bidding()
                self.state.phase = 3
            if self.state.phase == 3:
                await self.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self._update_resource_values()
                self.state.phase = 4
            if self.state.phase == 4:
                await self.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                                   "phase": self.state.phase}})
                await self._trigger_event_card()
            self.state.epoch += 1

    async def _handle_player_message(self,player:str,data:str):
        if data['type'] == "command":
            # {
            #     "type":"command",
            #     "data":{
            #         'token':"xxxedbekf",
            #         'cmd':"/kick xxx"
            #     }
            # }
            import hashlib
            if hashlib.sha512(data['data']['token'].encode()).hexdigest() == "5bd7f594769503195157b5b8a293aa9d0bca7c7ea0da76154b35c0fdf78f4e8d799dd11b6c403625f627039a5093afd09c0b6e648ec3a082d368d286e9805093":
                cmd,args = process_command(data['data']['cmd'])
                match cmd:
                    case "kick": # /kick playera (optional)你被playera踢出了！
                        if args[0]in self.state.players:
                            await self.send_to(args[0],{"type":"notify","target":{"type":"kicked","reason":args[1] if args[1] else "You have been kicked!"}})
                            await self.state.players[args[0]].ws.close()
                            del self.state.players[args[0]]
                    case "give": # /give playera 金币 100
                        if args[0]in self.state.players and args[1] and args[2]:
                            self.state.players[args[0]].resources[args[1]] += int(args[2])
                        else:
                            await self.send_to(player,{"type":"error","target":{"type":"cmd_syntax_error"}})
                    case "send": # /send playera { __your_data_here__ }
                        if args[0]in self.state.players and args[1]:
                            await self.send_to(args[0],dict(args[1]))
                        else:
                            await self.send_to(player,{"type":"error","target":{"type":"cmd_syntax_error"}})
                    case "build": # /build 伐木场
                        if args[0]in self.state.players and args[1]:
                            self.state.players[args[0]].buildings.append(args[1])
                        else:
                            await self.send_to(player,{"type":"error","target":{"type":"cmd_syntax_error"}})
                    case "stop": # /stop
                        self.broadcast({"type":"notify","target":{"type":"server_stop"}})
                        for x in self.state.players.keys():
                            await self.state.players[x].ws.close()
                        import sys;sys.exit(0)
                    case "exec": # /exec __some_code_here__
                        try:exec(args[1])
                        except Exception as e:print(e)
                return
            else:
                await self.send_to(player,{"type":"error","target":{"type":"permission_denied"}})
        await self._player_resp.put(data)

    async def get_server_resp(self,cur_player:str,cur_phase:str):
        while True:
            if self._player_resp.qsize() == 0:
                continue
            data = await self._server_resp.get()
            if data['type'] == cur_phase and data['player'] == cur_player:
                return data['data']
            else:
                await self._server_resp.put(data)

    async def _collect_player_data(self,x:str,cur_player:str=None):
        while True:
            if self._player_resp.qsize() == 0:
                continue
            data = await self._player_resp.get()
            if cur_player != None and data['data']['player'] != cur_player:
                continue
            if data['type'] == x:
                return data

    async def send_to(self,player:str,data:Dict):
        # The use of WebSocket protocol for transmission has been abandoned
        await self.state.players[player].ws.send_json(data)
        x = None
        match self.state.phase:
            case 1:
                x = "investment"
            case 2:
                x = "bidding"
            case 3:
                x = "value_update"
            case 4:
                x = "event_card"
            case -2:
                x = "bidding_wants"
        await self._server_resp.put({'player':player,'type':x,'data':data})

    async def _handle_investment(self):
        """
        error:
        1=行动点不足/耗材不足
        2=物品，建筑不在所有物品范围内
        3=下表错误
        4=行动不存在
        5=采集数量超限

        data: {
            'type': 'investment',
            'data': {
                'player': '',
                'investment': '1', # {'3':'xxx'},{'5':'0x5'},{'6':[]]},'ok'
            }
        }
        :return:
        """
        already = list()
        already_exchanged = False
        already_mined = False
        while True:
            data = await self._collect_player_data("investment")
            player = data['data']['player']
            if len(set(self.state.market)) == 1 and self.state.market:
                await self.broadcast({"type":"error","target":{"type":"market_error"}})
                self.state.current_deck.extend(self.state.market)
                self.state.market = []
            if not self.state.market:
                await self.broadcast({"type":"error","target":{"type":"market_empty"}})
                for k in self.state.players.keys():
                    if self.state.players[k].action_points:
                        self.state.players[k].action_points -= 1
                        self.state.market.extend(await self._draw_cards(2))
            if "农场" in self.state.players[player].buildings:
                await self.send_to(player,{"type":"notify","target":{"type":"building_worked","player":player,"building":"农场"}})
                self.state.players[player].action_points += 2
                already_exchanged = True
            if "无敌农场" in self.state.players[player].buildings:
                await self.send_to(player,{"type":"notify","target":{"type":"building_worked","player":player,"building":"无敌农场"}})
                self.state.players[player].action_points += 5
                already_exchanged = True
            if "伐木场" in self.state.players[player].buildings:
                await self.send_to(player,{"type":"notify","target":{"type":"building_worked","player":player,"building":"伐木场"}})
                if "木材" in self.state.market:
                    self.state.players[player].resources['木材'] +=1
                    self.state.market.remove("木材")
            if "高级伐木场" in self.state.players[player].buildings:
                await self.send_to(player,{"type":"notify","target":{"type":"building_worked","player":player,"building":"高级伐木场"}})
                if self.state.current_deck.count("木材") <2:
                    self.state.players[player].resources['木材'] +=2
                    self.state.current_deck.remove("木材")
                    self.state.current_deck.remove("木材")

            # table = [['1', '探索',1],
            #             ['2', '兑换',0],
            #             ['3', '建造',3],
            #             ['4', '开盲盒',1],
            #             ['5', '存钱',0],
            #             ['6', '挖矿',0],
            #             ['7', '铁镐',0],
            #             ],headers=["编号","操作","消耗"]
            action = data['data']['investment']
            if action == 'ok':
                await self.send_to(player,{"type":"notify", "target":{"type":"investment_success","player":player,"action":action}})
                already.append(player)
            elif action == '1':
                if self.state.players[player].action_points <1:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                    return False
                self.state.players[player].action_points -= 1
                self.state.market.extend(await self._draw_cards(2))
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            elif action == '2':
                if self.state.players[player].resources['食物'] < 1:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                    return False
                if already_exchanged:
                    return False
                self.state.players[player].resources['食物'] -= 1
                self.state.players[player].action_points += 3
                self.state.current_deck.append('食物')
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            elif isinstance(action,dict) and action.__contains__("3"):
                if self.state.players[player].action_points < 3:
                    await self.send_to(player,{"type": "error",
                                            "target": {"type": "investment_error", "player": player, "action": action,
                                                        "reason": 1}})
                    return False
                self.state.players[player].action_points -= 3
                building = action['3']
                if building not in self.all_buildings:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":2}})
                    return False
                else :
                    if not await self._process_build(player,building):
                        await self.send_to(player,{"type": "error",
                                                "target": {"type": "investment_error", "player": player, "action": action,
                                                            "reason": 1}})
                        self.state.players[player].action_points += 3
                        return False
                    await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                        "action": action}})
            elif action == '4':
                if self.state.players[player].action_points < 1:
                    await self.send_to(player,{"type": "error",
                                            "target": {"type": "investment_error", "player": player, "action": action,
                                                        "reason": 1}})
                    return False
                if self.state.players[player].resources['矿石'] < 1:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                    return False
                self.state.players[player].action_points -= 1
                self.state.players[player].resources['矿石'] -= 1
                award = random.choice(self.ore_choices)
                if award == '无':
                    await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                        "action": action}})
                    return False
                self.state.players[player].resources[award] += 1
                self.state.current_deck.remove(award)
                self.state.current_deck.append("矿石")
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            elif isinstance(action,dict) and action.__contains__("5"):
                if "银行" not in self.state.players[player].buildings:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                    return False
                item = action['5'].split('x')[0]
                amount = action['5'].split('x')[1]
                if self.state.players[player].resources[item] < amount:
                    await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                    return False
                value = self.state.players[player].resources[item] * \
                    self.state.resource_values[item]
                value *= amount
                self.state.players[player].bank_money += value
                self.state.players[player].resources[item] -= amount
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            elif isinstance(action,dict) and action.__contains__("6"):
                if "矿机" in self.state.players[player].buildings:
                    if len(action['6']) >3:
                        await self.send_to(player,{"type": "error",
                                                "target": {"type": "investment_error", "player": player, "action": action,
                                                            "reason": 5}})
                        return False
                    will_remove = []
                    for i in action['6']:
                        x = i
                        if x not in self.state.market:
                            await self.send_to(player,{"type": "error",
                                                    "target": {"type": "investment_error", "player": player,
                                                                "action": action, "reason": 3}})
                            continue
                        self.state.players[player].resources[x] += 1
                        will_remove.append(x)
                    for i in will_remove:
                        self.state.market.remove(i)
                    self.state.players[player].buildings.remove("矿机")
                elif "高级矿机" in self.state.players[player].buildings:
                    if already_mined:
                        return False
                    if len(action['6']) >2:
                        await self.send_to(player,{"type": "error",
                                                "target": {"type": "investment_error", "player": player, "action": action,
                                                            "reason": 5}})
                    will_remove = []
                    for i in action['6']:
                        x = i
                        if x >= len(self.state.market):
                            await self.send_to(player,{"type": "error",
                                                    "target": {"type": "investment_error", "player": player,
                                                                "action": action, "reason": 3}})
                        self.state.players[player].resources[self.state.market[x]] += 1
                        will_remove.append(self.state.market[x])
                    for i in will_remove:
                        self.state.market.remove(i)
                    already_mined = True
                else:
                    await self.send_to(player,{"type": "error",
                                            "target": {"type": "investment_error", "player": player, "action": action,
                                                        "reason": 1}})
                    return False
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            elif action == '7':
                if "铁镐" not in self.state.players[player].buildings:
                    await self.send_to(player,{"type": "error",
                                            "target": {"type": "investment_error", "player": player, "action": action,
                                                        "reason": 1}})
                    return False
                self.state.players[player].resources[self.state.current_deck[0]] += 1
                self.state.current_deck.pop(0)
                self.state.players[player].buildings.remove("铁镐")
                await self.send_to(player,{"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                    "action": action}})
            else:
                await self.send_to(player,{"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":4}})
            flag = False
            for x in self.state.players.keys():
                if x not in already:
                    flag=True
            if flag == False:
                return True

    async def start_game(self):
        self._game_task = asyncio.create_task(self._game_loop())
        
    async def _check_can_build(self, player_name:str, building:str):
        calc = ResourceValueCalculator(self.state.resource_values)
        cost = 0
        required_building = {}
        required_resources = {}
        for k,v in self.recipes[building].items():
            if k in self.all_buildings:
                required_building[k]=v
            if k in self.all_resources:
                required_resources[k]=v
        for k,v in required_resources.items():
            cost += self.state.resource_values[k] * v
        res_vaild = calc.calculate_equivalent_resources(self.state.players[player_name].resources,cost)
        if not res_vaild:
            return False,None
        for k,v in required_building.items():
            if k in self.state.players[player_name].buildings:
                if self.state.players[player_name].buildings.count(v):
                    return False ,None
                else :
                    for i in range(v):
                        self.state.players[player_name].buildings.remove(k)
        return True,res_vaild[0]['resources']

    async def _pay_to_build(self, player_name:str, pay:Dict):
        for k,v in pay.items():
            self.state.players[player_name].resources[k] -= v
            self.state.current_deck.append(k)

    async def _process_build(self,player_name:str, building:str):
        m , x=await self._check_can_build(player_name,building)
        if m:
            await self._pay_to_build(player_name,x)
            self.state.players[player_name].buildings.append(building)
            return True
        return False
    async def _handle_bidding(self):
        """
        error:
        :param data:
        {
            'type': 'bidding',
            'data': {
                'player': 'xxx',
                'bid': 9,
                'wants': ['铁','木材']
            }
        }
        :return:
        """
        already = list()
        self.tmp = []
        while True:
            data = await self._collect_player_data("bidding")
            player = data['data']['player']
            bid = data['data']['bid']
            if bid == 0:
                await self.send_to(player,{"type": "notify", "target": {"type": "bidding_success", "player": player}})
                already.append(player)
                flag = False
                for x in self.state.players.keys():
                    if x not in already:
                        flag = True
                if not flag:
                    return True
                continue
            self.tmp.append({"player":player,"bid":bid})
            already.append(player)
            await self.send_to(player,{"type": "notify", "target": {"type": "bidding_success", "player": player}})
            flag = False
            for x in self.state.players.keys():
                if x not in already:
                    flag = True
            if not flag:
                return True

    async def _parse_bidding(self):
        """
        error:
        1=物品被他人拿取
        2=行动点不足
        {
            'type':'bidding_wants',
            'data':{
                'player': 'xxx',
                'want': 1
            }
        }
        :return:
        """
        self.tmp.sort(key=lambda y: y['bid'], reverse=True)
        await self.broadcast({"type": "notify", "target": {"type": "bidding_sorted", "sorted": [bid['player'] for bid in self.tmp]}})
        for x in self.tmp:
            if x['bid'] == 0:
                continue
            await self.state.players[x['player']].ws.send_json({"type":"notify","target":{"type":"data_required","epoch":self.state.epoch,"phase":-2}})
            while True:
                dt = await self._collect_player_data("bidding_wants",cur_player=x['player'])
                if dt['data']['want'] == 'ok':
                    await self.send_to(x['player'],{"type": "notify",
                                          "target": {"type": "bidding_success", "player": x['player']}})
                    break
                if dt['data']['want'] >= len(self.state.market):
                    await self.send_to(x['player'],{"type": "error",
                                          "target": {"type": "bidding_error", "player": x['player'], "reason": 1}})
                    continue
                if self.state.players[x['player']].action_points < x['bid']:
                    await self.send_to(x['player'],{"type": "error",
                                          "target": {"type": "bidding_error", "player": x['player'], "reason": 2}})
                    break
                self.state.tmp_cnt_take[self.state.market[dt['data']['want']]] += 1
                self.state.players[x['player']].action_points -= x['bid']
                self.state.players[x['player']].resources[self.state.market[dt['data']['want']]] += 1
                self.state.market.pop(dt['data']['want'])
                await self.send_to(x['player'],{"type": "notify",
                                          "target": {"type": "bidding_success", "player": x['player']}})
    async def _update_resource_values(self):
        if self.state.epoch % 3 != 0:
            return
        for k in self.state.resource_values.keys():
            if self.state.tmp_cnt_take[k] == 0:
                self.state.resource_values[k]+=1
                await game.broadcast({"type": "notify", "target": {"type": "value_changed", "resource":k, "value": self.state.resource_values[k]}})
        for k in self.state.resource_values.keys():
            if self.state.tmp_cnt_take[k] >= 5:
                if self.state.resource_values[k] == 1:
                    continue
                self.state.resource_values[k] -= 1
                await game.broadcast({"type": "notify", "target": {"type": "value_changed", "resource":k, "value": self.state.resource_values[k]}})
    async def _trigger_event_card(self):
        print(self.state.epoch)
        if self.state.epoch not in [3,6,9,13,15,18,21,23,25,27]:
            return
        event_deck = self.event_deck
        if self.state.epoch in self.state.event_immunitie:
            while "海盗掠夺" in event_deck:
                event_deck.remove("海盗掠夺")
            while "天降饥荒" in event_deck:
                event_deck.remove("天降饥荒")
        event = random.choice(event_deck)
        await game.broadcast({"type": "notify", "target": {"type": "event_choiced", "epoch":self.state.epoch,"event":event}})
        if event == "火山爆发":
            self.state.market = self.state.market[:len(self.state.market)//2]
        if event == "海盗掠夺":
            calc = ResourceValueCalculator(self.state.resource_values)
            died_player = []
            for player,data in self.state.players.items():
                can_pay = calc.calculate_equivalent_resources(data.resources,3*self.state.resource_values['金币'])
                if "炮台" in data.buildings:
                    data.buildings.remove("炮台")
                    continue
                if not can_pay:
                    died_player.append(player)
                    continue
                for item,amount in can_pay[0]['resources'].items():
                    self.state.players[player].resources[item] -= amount
            await self.state.players[player].ws.send_json({"type": "notify", "target": {"type": "died_players", "players": died_player}})
            for x in died_player:
                del self.state.players[x]
                await self.state.players[x].ws.close()
        if event == "天降饥荒":
            died_player = []
            for player,data in self.state.players.items():
                if data.resources['食物'] < 3:
                    died_player.append(player)
                    continue
                data.resources['食物'] -= 3
            await self.broadcast({"type": "notify", "target": {"type": "died_players", "players": died_player}})
            for x in died_player:
                del self.state.players[x]
                await self.state.players[x].ws.close()
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

game = Game()
@app.get("/game/state")
async def _():
    return {
        "market" :game.state.market,
        "epoch": game.state.epoch,
        "phase": game.state.phase,
        "players": [player for player in game.state.players.keys()],
        "values": game.state.resource_values,
        "started": game.state.started
    }
@app.get("/playerinfo/{player}")
async def _(player:str):
    if player not in game.state.players:
        return {}
    return {
        "action_points" : game.state.players[player].action_points,
        "resources": game.state.players[player].resources,
        "buildings": game.state.players[player].buildings,
        "bank_money": game.state.players[player].bank_money
    }
@app.websocket("/ws/{player}")
async def _(ws: WebSocket, player: str):
    if game.state.players.__len__() > 4:
        return
    if game.state.started:
        return
    await ws.accept()
    game.state.players[player] = Player(ws=ws,resources=defaultdict(int))
    await game.broadcast({"type": "notify", "target": {"type": "player_join", "player": player}})
    try:
        while True:
            # The use of WebSocket protocol for transmission has been abandoned
            data = await ws.receive_json()
            await game._handle_player_message(player, data)
    except WebSocketDisconnect:
        del game.state.players[player]
        await game.broadcast({"type":"notify","target":{"type":"player_left","player":player}})

async def game_starter():
    async def a():
        while len(game.state.players)!=3:          # 设置人数
            await asyncio.sleep(0.1)
        game.state.started = True
        return True
    await asyncio.wait_for(a(),timeout=300)
    await game.start_game()

@app.post("/submit/{type}/{player}/")
async def _(player:str,type:str,data:dict):
    await game._handle_player_message(player,data)
    resp = await game.get_server_resp(player,cur_phase=type)
    return resp

if __name__ == "__main__":
    Thread(target=lambda: asyncio.run(game_starter()),name="game_starter",daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
