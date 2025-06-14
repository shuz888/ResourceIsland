import asyncio
import dataclasses
import random
from collections import defaultdict
from threading import Thread
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

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
        self.tmp_cnt_take = {}
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
        self._game_task = None

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
        self.state.market.extend(await self._draw_cards(10))
        for player in game.state.players.keys():
            self.state.players[player].resources['食物'] += 5
        await self.broadcast({"type":"notify","target":{"type":"game_start"}})
        while self.state.epoch <= 30:
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
                await self._parse_bidding()
                self.state.phase = 3
            if self.state.phase == 3:
                await self._update_resource_values()
                self.state.phase = 4
            if self.state.phase == 4:
                await self._trigger_event_card()
            self.state.epoch += 1
    async def _handle_player_message(self,player:str,data:str):
        await self._player_resp.put((player,data))

    async def _collect_players_data(self,x:str):
        datas:List[Dict] = []
        while datas.__len__() < self.state.players.__len__():
            print(datas)
            data = await self._player_resp.get()
            if data[1]['type'] == x:
                datas.append(data[1])
        return datas

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
                'investment': [1,{'3':'xxx'},{'5':'0x5'},{'6':[1,2,3]}],
            }
        }
        :return:
        """
        data = await self._collect_players_data("investment")
        self.phase = 1
        for data in data:
            already_exchanged = False
            already_mined = False
            player = data['data']['player']
            if len(set(self.state.market)) == 1 and self.state.market:
                await self.broadcast({"type":"notify","target":{"type":"market_error"}})
                self.state.current_deck.extend(self.state.market)
                self.state.market = []
            if not self.state.market:
                await self.broadcast({"type":"notify","target":{"type":"market_empty"}})
                for k in self.state.players.keys():
                    if self.state.players[k].action_points:
                        self.state.players[k].action_points -= 1
                        self.state.market.extend(await self._draw_cards(2))
            if "农场" in self.state.players[player].buildings:
                await self.broadcast({"type":"notify","target":{"type":"building_worked","player":player,"building":"农场"}})
                self.state.players[player].action_points += 2
                already_exchanged = True
            if "无敌农场" in self.state.players[player].buildings:
                await self.broadcast({"type":"notify","target":{"type":"building_worked","player":player,"building":"无敌农场"}})
                self.state.players[player].action_points += 5
                already_exchanged = True
            if "伐木场" in self.state.players[player].buildings:
                await self.broadcast({"type":"notify","target":{"type":"building_worked","player":player,"building":"伐木场"}})
                if "木材" in self.state.market:
                    self.state.players[player].resources['木材'] +=1
                    self.state.market.remove("木材")
            if "高级伐木场" in self.state.players[player].buildings:
                await self.broadcast({"type":"notify","target":{"type":"building_worked","player":player,"building":"高级伐木场"}})
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
            for action in data["data"]["investment"]:
                if action == '1':
                    if self.state.players[player].action_points <1:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                        continue
                    self.state.players[player].action_points -= 1
                    self.state.market.extend(await self._draw_cards(2))
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                elif action == '2':
                    if self.state.players[player].resources['食物'] < 1:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                        continue
                    if already_exchanged:
                        continue
                    self.state.players[player].resources['食物'] -= 1
                    self.state.players[player].action_points += 2
                    self.state.current_deck.append('食物')
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                elif isinstance(action,dict) and action.__contains__("3"):
                    if self.state.players[player].action_points < 3:
                        await self.broadcast({"type": "error",
                                              "target": {"type": "investment_error", "player": player, "action": action,
                                                         "reason": 1}})
                        continue
                    self.state.players[player].action_points -= 3
                    building = action['3']
                    if building not in self.all_buildings:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":2}})
                        continue
                    else :
                        if not self._process_build(player,building):
                            await self.broadcast({"type": "error",
                                                  "target": {"type": "investment_error", "player": player, "action": action,
                                                             "reason": 1}})
                            self.state.players[player].action_points += 3
                elif action == '4':
                    if self.state.players[player].action_points < 1:
                        await self.broadcast({"type": "error",
                                              "target": {"type": "investment_error", "player": player, "action": action,
                                                         "reason": 1}})
                        continue
                    if self.state.players[player].resources['矿石'] < 1:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                        continue
                    self.state.players[player].action_points -= 1
                    self.state.players[player].resources['矿石'] -= 1
                    award = random.choice(self.ore_choices)
                    if award == '无':
                        await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                           "action": action}})
                        continue
                    self.state.players[player].resources[award] += 1
                    self.state.current_deck.remove(award)
                    self.state.current_deck.append("矿石")
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                elif isinstance(action,dict) and action.__contains__("5"):
                    if "银行" not in self.state.players[player].buildings:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                        continue
                    item = action['5'].split('x')[0]
                    amount = action['5'].split('x')[1]
                    if self.state.players[player].resources[item] < amount:
                        await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":1}})
                        continue
                    value = self.state.players[player].resources[item] * \
                        self.state.resource_values[item]
                    value *= amount
                    self.state.players[player].bank_money += value
                    self.state.players[player].resources[item] -= amount
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                elif isinstance(action,dict) and action.__contains__("6"):
                    if "矿机" in self.state.players[player].buildings:
                        if len(action['6']) >3:
                            await self.broadcast({"type": "error",
                                                  "target": {"type": "investment_error", "player": player, "action": action,
                                                             "reason": 5}})
                            continue
                        will_remove = []
                        for i in action['6']:
                            x = i
                            if x not in self.state.market:
                                await self.broadcast({"type": "error",
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
                            continue
                        if len(action['6']) >2:
                            await self.broadcast({"type": "error",
                                                  "target": {"type": "investment_error", "player": player, "action": action,
                                                             "reason": 5}})
                        will_remove = []
                        for i in action['6']:
                            x = i
                            if x >= len(self.state.market):
                                await self.broadcast({"type": "error",
                                                      "target": {"type": "investment_error", "player": player,
                                                                 "action": action, "reason": 3}})
                            self.state.players[player].resources[self.state.market[x]] += 1
                            will_remove.append(self.state.market[x])
                        for i in will_remove:
                            self.state.market.remove(i)
                        already_mined = True
                    else:
                        await self.broadcast({"type": "error",
                                              "target": {"type": "investment_error", "player": player, "action": action,
                                                         "reason": 1}})
                        continue
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                elif action == '7':
                    if "铁镐" not in self.state.players[player].buildings:
                        await self.broadcast({"type": "error",
                                              "target": {"type": "investment_error", "player": player, "action": action,
                                                         "reason": 1}})
                        continue
                    self.state.players[player].resources[self.state.current_deck[0]] += 1
                    self.state.current_deck.pop(0)
                    self.state.players[player].buildings.remove("铁镐")
                    await self.broadcast({"type": "notify", "target": {"type": "investment_success", "player": player,
                                                                       "action": action}})
                else:
                    await self.broadcast({"type": "error", "target": {"type":"investment_error","player": player,"action": action,"reason":4}})
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
        m , x=self._check_can_build(player_name,building)
        if m:
            await self._pay_to_build(player_name,x)
            self.state.players[player_name].buildings.append(building)
            return True
        return False
    async def _handle_bidding(self):
        """
        error:
        1=出价无法支付
        2=物品没有在市场中
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
        data = await self._collect_players_data("bidding")
        for data in data:
            player = data['data']['player']
            bid = data['data']['bid']
            wants = data['data']['wants']
            self.tmp = []
            if bid == 0:
                await self.broadcast({"type": "notify", "target": {"type": "bidding_success", "player": player}})
                return
            for x in wants:
                if x not in self.state.market:
                    await self.broadcast({"type": "error",
                                          "target": {"type": "bidding_error", "player": player, "reason": 2}})
                    return
            if self.state.players[player].action_points*wants.__len__() >= 0:
                await self.broadcast({"type": "notify", "target": {"type": "bidding_success", "player": player}})
                self.tmp.append({"player": player, "bid": bid, "wants": wants})
                return
            else:
                await self.broadcast({"type": "error",
                                      "target": {"type": "bidding_error", "player": player, "reason": 1}})
                return

    async def _parse_bidding(self):
        """
        error:
        1=物品被他人拿取
        :return:
        """
        self.tmp.sort(key=lambda y: y['bid'], reverse=True)
        await self.broadcast({"type": "notify", "target": {"type": "bidding_sorted", "sorted": [bid['player'] for bid in self.tmp]}})
        for x in self.tmp:
            for i in x['wants']:
                if i not in self.state.market:
                    await self.broadcast({"type": "error",
                                          "target": {"type": "bidding_error", "player": x['player'], "reason": 1}})
                    continue
                self.state.tmp_cnt_take[i] += 1
                self.state.players[x['player']].action_points -= x['bid']
                self.state.players[x['player']].resources[i] += 1
                self.state.market.remove(i)
    async def _update_resource_values(self):
        if self.state.epoch % 3 != 0:
            return
        await game.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                           "phase": self.state.phase}})
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
        if self.state.epoch not in [3,6,9,13,15,18,21,23,25,27]:
            return
        await game.broadcast({"type": "notify", "target": {"type": "phase_changed", "epoch": self.state.epoch,
                                                           "phase": self.state.phase}})
        event_deck = self.event_deck
        if self.state.epoch in self.state.event_immunitie:
            while "海盗掠夺" in event_deck:
                self.event_deck.remove("海盗掠夺")
            while "天降饥荒" in event_deck:
                self.event_deck.remove("天降饥荒")
        event = random.choice(event_deck)
        await game.broadcast({"type": "notify", "target": {"type": "event_choiced", "event":event}})
        if event == "火山爆发":
            self.market = self.state.market[:len(self.state.market)//2]
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
            data = await ws.receive_json()
            await game._handle_player_message(player, data)
    except WebSocketDisconnect:
        del game.state.players[player]
        await game.broadcast({"type":"notify","target":{"type":"player_left","player":player}})

async def game_starter():
    async def a():
        while len(game.state.players)!=2:          # 设置人数
            await asyncio.sleep(0.1)
        game.state.started = True
        return True
    await asyncio.wait_for(a(),timeout=300)
    await game.start_game()
if __name__ == "__main__":
    Thread(target=lambda: asyncio.run(game_starter()),name="game_starter",daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)