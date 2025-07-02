import aiohttp,asyncio,os
from tabulate import tabulate
from threading import Thread
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

class GameStatusViewer:
    def __init__(self, server_addr :str):
        self.staturl = f"http://{server_addr}/game/state"
        self.server_addr = server_addr
        self.o = ColorOutput()
        self.players = {}
        self.resource_values = {}
        self.epoch = 0
        self.phase = ''
        self.market = []

    async def start(self):
        await self.every(1,self.display_game_state)

    async def every(self, __seconds: float, func, *args, **kwargs):
        while True:
            await func(*args, **kwargs)
            await asyncio.sleep(__seconds)

    async def fetch_url(self,url:str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def show_values(self):
        table = tabulate(
            [[res, value] for res, value in self.resource_values.items()],
            headers=["资源类型", "当前价值"],
        )
        print(table)

    async def show_rank(self):
        self.o.b("\n=== 玩家价值排名 ===")
        await self.sync_game_state()
        table = [[player,await self._calc_player_value(self.players[player])] for player in self.players.keys()]
        table.sort(key=lambda x:x[1],reverse=True)
        table = tabulate(
            [[i+1]+item for i,item in enumerate(table)],
            headers=["排名","玩家名称", "当前价值"],
        )
        print(table)

    async def _calc_player_value(self,data:dict):
        result = 0
        for k,v in data['resources'].items():
            result += self.resource_values[k]*v
        result += data['money']*1.5
        result += data['action_points']*0.5
        return result

    async def sync_game_state(self):
        game_state = await self.fetch_url(self.staturl)
        all_player = game_state['players']
        all_player_state = [await self.fetch_url(f"http://{self.server_addr}/playerinfo/{name}") for name in all_player]
        self.resource_values = game_state['values']
        self.players = {name: {
                'resources': state['resources'],
                'action_points': state['action_points'],
                'buildings': state['buildings'],
                'money': state['bank_money'],
            } for name,state in zip(all_player,all_player_state)}
        self.market = game_state['market']
        self.started = game_state['started']
        self.epoch = game_state['epoch']
        self.phase = game_state['phase']

    async def display_game_state(self):
        """优化后的游戏状态显示方法"""
        os.system("cls" if os.name == 'nt' else "clear")
        self.o.b("=== 游戏状态 ===")
        self.o.w(f"当前是第{self.epoch}轮的{self.phase}阶段。")
        # 显示玩家信息（精简版）
        self.o.b("=== 玩家状态 ===")
        for player, data in self.players.items():
            self.o.w(f"{player}: AP={data['action_points']} $={data['money']}", end='')
            self.o.w(f" 建筑:{data['buildings']}", end='')
            res = [f"{k[:2]}:{v}" for k, v in data['resources'].items() if v > 0]
            self.o.w(f" 资源:{','.join(res)}")

        # 显示资源价值
        self.o.b("=== 资源价值 ===")
        await self.show_values()

        # 显示市场
        self.o.b("=== 市场 ===")
        for i, item in enumerate(self.market):
            self.o.w(f"{i}: {item}",end=', ')
        
        await self.show_rank()
        # 添加分隔线
        self.o.b("\n" + "=" * 30 + "\n")

if __name__ == '__main__':
    async def main():
        server_addr: str = input("请输入你的服务器地址：")
        if server_addr == '':
            server_addr = "localhost:8000"
        viewer = GameStatusViewer(server_addr)
        await viewer.start()

    asyncio.run(main())