import json
import os
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from astrbot.api import logger


def _strip_emoji(text: str) -> str:
    """去掉开头的emoji，只留文字部分用于匹配"""
    import re
    # 去掉开头的emoji字符（包括变体选择符和ZWJ序列）
    cleaned = re.sub(r'^[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F\u200D\u20E3\u2000-\u3300]+\s*', '', text)
    return cleaned.strip() if cleaned.strip() else text.strip()


# ========== 季节/节日判断 ==========

def get_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5): return "spring"
    if month in (6, 7, 8): return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"

def get_holiday() -> str:
    """仅当天命中才返回节日名"""
    m, d = datetime.now().month, datetime.now().day
    holidays = {
        (1, 1): "元旦", (2, 14): "情人节", (3, 8): "妇女节",
        (4, 1): "愚人节", (5, 1): "劳动节", (5, 4): "青年节",
        (6, 1): "儿童节", (10, 1): "国庆节", (10, 31): "万圣节",
        (12, 24): "平安夜", (12, 25): "圣诞节",
    }
    return holidays.get((m, d), "")


# ========== 收藏品已占用的 emoji（AI生成时排除） ==========

_COLLECTIBLE_EMOJIS = {
    "🦆", "🐱", "🤡", "🐟", "🪲", "🥬", "🕊️", "🍳", "⌨️", "🍋",
    "🍗", "💇", "🏀", "🐠", "🔪", "🔌", "🖥️", "📺", "☁️", "🎓",
    "🍅", "🔘", "🧊",
}

_HOLIDAY_EMOJIS = {
    "🎄", "🎅", "🎃", "👻", "🎆", "🧨", "💘", "🌹", "🎁", "🎊",
}

_FORBIDDEN_EMOJIS = _COLLECTIBLE_EMOJIS | _HOLIDAY_EMOJIS


# ========== 节日专属商品（手写固定池） ==========

HOLIDAY_ITEMS = {
    "元旦": [
        {"name": "🎆 新年烟花糖", "category": "food", "price": 3, "desc": "噼里啪啦的跳跳糖", "shelf_life_days": 30},
    ],
    "情人节": [
        {"name": "💘 心形巧克力", "category": "food", "price": 5, "desc": "粉色包装的心形巧克力", "shelf_life_days": 30},
        {"name": "🌹 红玫瑰", "category": "flower", "price": 8, "desc": "一枝鲜红的玫瑰", "shelf_life_days": 5},
    ],
    "妇女节": [
        {"name": "💐 康乃馨花束", "category": "flower", "price": 6, "desc": "温馨的粉色康乃馨", "shelf_life_days": 5},
    ],
    "愚人节": [
        {"name": "🎁 神秘盒子", "category": "item", "price": 1, "desc": "打开可能是惊喜也可能是惊吓"},
    ],
    "劳动节": [
        {"name": "🧨 劳动勋章饼干", "category": "food", "price": 3, "desc": "勋章形状的黄油饼干", "shelf_life_days": 15},
    ],
    "青年节": [
        {"name": "📖 热血笔记本", "category": "item", "price": 4, "desc": "封面写着「奋斗」的笔记本"},
    ],
    "儿童节": [
        {"name": "🍭 超大棒棒糖", "category": "food", "price": 2, "desc": "彩虹色的大棒棒糖", "shelf_life_days": 60},
        {"name": "🎈 气球", "category": "decoration", "price": 1, "desc": "圆圆的红气球"},
    ],
    "国庆节": [
        {"name": "🎊 国庆小旗", "category": "decoration", "price": 2, "desc": "迎风飘扬的小国旗"},
    ],
    "万圣节": [
        {"name": "🎃 南瓜灯", "category": "decoration", "price": 5, "desc": "笑嘻嘻的南瓜灯"},
        {"name": "👻 幽灵糖果", "category": "food", "price": 3, "desc": "白色幽灵形状的软糖", "shelf_life_days": 30},
    ],
    "平安夜": [
        {"name": "🍎 平安果", "category": "food", "price": 4, "desc": "包装精美的红苹果", "shelf_life_days": 7},
    ],
    "圣诞节": [
        {"name": "🎄 迷你圣诞树", "category": "decoration", "price": 6, "desc": "桌上摆的小圣诞树"},
        {"name": "🎅 圣诞袜糖果", "category": "food", "price": 3, "desc": "红袜子里装满了糖", "shelf_life_days": 30},
    ],
}


# ========== 默认商品池 ==========

DEFAULT_POOL = {
    "all_season": [
        {"name": "🍇 葡萄", "category": "food", "price": 3, "desc": "一串紫葡萄", "shelf_life_days": 5},
        {"name": "🍎 苹果", "category": "food", "price": 2, "desc": "红红的苹果", "shelf_life_days": 7},
        {"name": "🥛 牛奶", "category": "food", "price": 2, "desc": "一盒纯牛奶", "shelf_life_days": 7},
        {"name": "🍞 面包", "category": "food", "price": 2, "desc": "普通的切片面包", "shelf_life_days": 3},
        {"name": "🧃 果汁", "category": "food", "price": 2, "desc": "盒装橙汁", "shelf_life_days": 14},
        {"name": "🍪 饼干", "category": "food", "price": 2, "desc": "一包原味饼干", "shelf_life_days": 60},
        {"name": "🥚 鸡蛋", "category": "food", "price": 1, "desc": "一颗鸡蛋", "shelf_life_days": 14},
        {"name": "🧻 纸巾", "category": "item", "price": 1, "desc": "一包抽纸"},
        {"name": "🖊️ 圆珠笔", "category": "item", "price": 1, "desc": "普通蓝色圆珠笔"},
        {"name": "📎 回形针", "category": "item", "price": 1, "desc": "一盒回形针"},
        {"name": "⭐ 小星星", "category": "decoration", "price": 1, "desc": "亮晶晶的小星星"},
    ],
    "spring": [
        {"name": "🫖 茉莉花茶", "category": "food", "price": 3, "desc": "清香的茉莉花茶包", "shelf_life_days": 90},
        {"name": "🌷 郁金香", "category": "flower", "price": 5, "desc": "一枝粉色郁金香", "shelf_life_days": 5},
        {"name": "🥒 黄瓜", "category": "food", "price": 2, "desc": "新鲜的黄瓜", "shelf_life_days": 5},
        {"name": "🎋 竹扇", "category": "item", "price": 3, "desc": "手工竹扇"},
    ],
    "summer": [
        {"name": "🍉 西瓜", "category": "food", "price": 4, "desc": "冰镇大西瓜", "shelf_life_days": 2},
        {"name": "🍦 冰淇淋", "category": "food", "price": 3, "desc": "香草冰淇淋", "shelf_life_days": 1},
        {"name": "🥤 柠檬水", "category": "food", "price": 2, "desc": "冰柠檬水", "shelf_life_days": 1},
        {"name": "🌻 向日葵", "category": "flower", "price": 4, "desc": "一枝向日葵", "shelf_life_days": 5},
    ],
    "autumn": [
        {"name": "🌰 板栗", "category": "food", "price": 3, "desc": "糖炒板栗", "shelf_life_days": 7},
        {"name": "🍠 烤红薯", "category": "food", "price": 3, "desc": "热乎乎的烤红薯", "shelf_life_days": 1},
        {"name": "🍊 橘子", "category": "food", "price": 2, "desc": "甜甜的橘子", "shelf_life_days": 14},
        {"name": "🍁 枫叶书签", "category": "decoration", "price": 2, "desc": "红色枫叶压成的书签"},
    ],
    "winter": [
        {"name": "🥟 饺子", "category": "food", "price": 4, "desc": "猪肉白菜馅饺子", "shelf_life_days": 1},
        {"name": "🫕 关东煮", "category": "food", "price": 3, "desc": "热乎乎的关东煮", "shelf_life_days": 1},
        {"name": "☕ 热可可", "category": "food", "price": 3, "desc": "暖暖的热巧克力", "shelf_life_days": 1},
        {"name": "🧣 围巾", "category": "item", "price": 6, "desc": "毛线围巾"},
    ],
    "collectible": [
        {"name": "🦆 柯尔鸭", "category": "collectible", "price": 30, "desc": "致敬鸭鸭老师的限定收藏，头上带着一朵小花，眼神坚定。"},
        {"name": "🐱 薛定谔的猫罐头", "category": "collectible", "price": 25, "desc": "打开之前不知道里面有没有猫。建议永远别打开。"},
        {"name": "🤡 打工人的面具", "category": "collectible", "price": 20, "desc": "戴上它，今天也是元气满满的一天呢！（防御力+0，心酸度+100）"},
        {"name": "🐟 失去梦想的咸鱼", "category": "collectible", "price": 18, "desc": "翻个身，发现依然是咸鱼。质地坚硬，适合物理超度。"},
        {"name": "🪲 祖传代码Bug", "category": "collectible", "price": 35, "desc": "千万不要删！删了整个世界就会崩溃！据说它是这个游戏运行的基石。"},
        {"name": "🥬 一捆新鲜的韭菜", "category": "collectible", "price": 15, "desc": "绿油油长势喜人，你仿佛听到了半空中镰刀挥舞的破风声。"},
        {"name": "🕊️ 鸽子精的绒毛", "category": "collectible", "price": 22, "desc": "作者掉落的稀有物品。收集齐100根可兑换一个'下次一定更新'的承诺。"},
        {"name": "🍳 黑漆漆的平底锅", "category": "collectible", "price": 20, "desc": "进可挡子弹，退可炒冷饭。还能一巴掌拍醒做白日梦的玩家。"},
        {"name": "⌨️ 键仙的遗物", "category": "collectible", "price": 28, "desc": "在特定场合输入'懂得都懂'，可造成真实伤害。"},
        {"name": "🍋 发光的柠檬", "category": "collectible", "price": 15, "desc": "好酸啊！为什么别人都能抽到SSR，而我只有这个？"},
        {"name": "🍗 V我50的神秘炸鸡", "category": "collectible", "price": 25, "desc": "一到星期四就会散发耀眼光芒的圣物。"},
        {"name": "🐟 全自动电子木鱼", "category": "collectible", "price": 30, "desc": "赛博菩萨的法宝。放背包里自动积累赛博功德，专门抵消你在互联网上造的口业。"},
        {"name": "💇 强者的最后遗物", "category": "collectible", "price": 35, "desc": "某位全栈大佬跑通最后一个Bug时掉落的一撮头发，见证了技术巅峰与发际线衰退。"},
        {"name": "🏀 神秘的背带裤", "category": "collectible", "price": 20, "desc": "穿上它耳边会自动响起动感旋律。唱跳RAP篮球熟练度+2.5。"},
        {"name": "🐠 尊嘟假嘟测谎仪", "category": "collectible", "price": 22, "desc": "长得像条鱼，捏一下会发出'O.o'的声音，是敷衍一切画大饼行为的终极防具。"},
        {"name": "🔪 四十米长的大刀", "category": "collectible", "price": 28, "desc": "允许敌人先跑三十九米。携带时经常卡在新手村门框上。"},
        {"name": "🔌 被拔掉的网线", "category": "collectible", "price": 18, "desc": "终极物理防御。只要网线拔得够快，API被盗刷的速度就永远赶不上你。"},
        {"name": "🖥️ 禁忌符咒rm -r*/", "category": "collectible", "price": 40, "desc": "威力过于强大的毁灭魔法。某管理员在服务器里敲下它之后连夜买站票跑路了。"},
        {"name": "📺 下次一定硬币", "category": "collectible", "price": 15, "desc": "正面写着'白嫖'，反面写着'下次'。投给UP主时触发绝对防御。"},
        {"name": "☁️ 502护身符", "category": "collectible", "price": 20, "desc": "亮出这个符咒，就能把所有访问请求拒之门外，获得内心的片刻宁静。"},
        {"name": "🎓 赛博无敌学生证", "category": "collectible", "price": 25, "desc": "学信网可查，白嫖各路大厂云服务和开发者赠金的无价之宝！"},
        {"name": "🍅 西红柿炒钢丝球", "category": "collectible", "price": 18, "desc": "食堂大妈的巅峰之作。吃完不仅回血，还能给肠胃做深度抛光。"},
        {"name": "🔘 XX启动按钮", "category": "collectible", "price": 22, "desc": "按下去会发出无法静音的声响。在公共场合触发会立刻施放社会性死亡。"},
        {"name": "🧊 融化的雪糕刺客", "category": "collectible", "price": 30, "desc": "平平无奇的外表下隐藏着击穿钱包的杀伤力。结账时才发动致命一击。"},
    ],
}


class ShopManager:
    """
    线上超市系统
    - 每日10个商品（普通9-10 + 2%概率出收藏品替换其中一个）
    - 节日当天自动加入手写节日商品（替换普通商品）
    - 收藏品唯一：每人只能买一个，买过的不再出现
    - 主题食品店：每日随机开一家（蛋糕店/烤肉店/快餐店等）
    """

    def __init__(self, data_dir: str, daily_item_count: int = 10, item_pool: Dict = None):
        self.data_dir = data_dir
        self.daily_item_count = daily_item_count
        self.item_pool = item_pool or DEFAULT_POOL
        os.makedirs(self.data_dir, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, "shop.json")
        if not os.path.exists(path):
            return {"date": "", "items": [], "purchase_log": []}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("date", "")
                data.setdefault("items", [])
                data.setdefault("purchase_log", [])
                return data
        except (json.JSONDecodeError, TypeError):
            return {"date": "", "items": [], "purchase_log": []}

    def _save_data(self):
        path = os.path.join(self.data_dir, "shop.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ========== 收藏品唯一性 ==========

    def get_owned_collectibles(self, user_id: str) -> List[str]:
        """获取用户已拥有的收藏品名称列表"""
        return self.data.get("owned_collectibles", {}).get(user_id, [])

    def _record_collectible(self, user_id: str, item_name: str):
        """记录用户购买收藏品"""
        owned = self.data.setdefault("owned_collectibles", {})
        user_list = owned.setdefault(user_id, [])
        if item_name not in user_list:
            user_list.append(item_name)
            self._save_data()

    def has_collectible(self, user_id: str, item_name: str) -> bool:
        """检查用户是否已拥有某收藏品"""
        return item_name in self.get_owned_collectibles(user_id)

    # ========== 主题食品店 ==========

    FOOD_SHOPS = {
        "cake": {
            "name": "🎂 甜心蛋糕店",
            "items": [
                {"name": "🍰 草莓蛋糕", "category": "food", "price": 6, "desc": "铺满草莓的奶油蛋糕", "shelf_life_days": 2},
                {"name": "🧁 杯子蛋糕", "category": "food", "price": 3, "desc": "巧克力霜淇淋杯子蛋糕", "shelf_life_days": 3},
                {"name": "🍩 甜甜圈", "category": "food", "price": 2, "desc": "糖霜甜甜圈", "shelf_life_days": 2},
                {"name": "🥐 可颂", "category": "food", "price": 3, "desc": "黄油可颂，外酥里嫩", "shelf_life_days": 1},
                {"name": "🍮 焦糖布丁", "category": "food", "price": 4, "desc": "表面焦脆的经典布丁", "shelf_life_days": 2},
                {"name": "🧇 华夫饼", "category": "food", "price": 3, "desc": "淋蜂蜜的格子华夫", "shelf_life_days": 1},
            ],
        },
        "bbq": {
            "name": "🥩 炭火烤肉店",
            "items": [
                {"name": "🥩 和牛五花", "category": "food", "price": 8, "desc": "A5和牛雪花五花肉", "shelf_life_days": 1},
                {"name": "🍖 猪排", "category": "food", "price": 4, "desc": "秘制酱烤猪排", "shelf_life_days": 1},
                {"name": "🍗 烤鸡翅", "category": "food", "price": 3, "desc": "蜜汁烤鸡翅", "shelf_life_days": 1},
                {"name": "🌽 烤玉米", "category": "food", "price": 2, "desc": "刷酱烤玉米", "shelf_life_days": 1},
                {"name": "🫑 烤青椒", "category": "food", "price": 1, "desc": "微辣的烤青椒", "shelf_life_days": 1},
                {"name": "🍢 烤串拼盘", "category": "food", "price": 5, "desc": "羊肉串+牛肉串+鸡心", "shelf_life_days": 1},
            ],
        },
        "fastfood": {
            "name": "🍔 快乐快餐店",
            "items": [
                {"name": "🍔 经典汉堡", "category": "food", "price": 4, "desc": "双层牛肉芝士汉堡", "shelf_life_days": 1},
                {"name": "🍟 薯条", "category": "food", "price": 2, "desc": "大份脆薯条", "shelf_life_days": 1},
                {"name": "🌮 墨西哥卷", "category": "food", "price": 3, "desc": "鸡肉牛油果卷", "shelf_life_days": 1},
                {"name": "🌭 热狗", "category": "food", "price": 2, "desc": "美式芥末热狗", "shelf_life_days": 1},
                {"name": "🥤 可乐", "category": "food", "price": 2, "desc": "冰可乐", "shelf_life_days": 30},
                {"name": "🍕 芝士披萨", "category": "food", "price": 5, "desc": "拉丝芝士薄底披萨", "shelf_life_days": 1},
            ],
        },
        "chinese": {
            "name": "🥢 家常菜馆",
            "items": [
                {"name": "🥘 红烧肉", "category": "food", "price": 6, "desc": "肥而不腻的红烧肉", "shelf_life_days": 1},
                {"name": "🍜 兰州拉面", "category": "food", "price": 4, "desc": "一清二白三红四绿五黄", "shelf_life_days": 1},
                {"name": "🥟 小笼包", "category": "food", "price": 3, "desc": "鲜肉小笼包一屉", "shelf_life_days": 1},
                {"name": "🍚 蛋炒饭", "category": "food", "price": 3, "desc": "粒粒分明的蛋炒饭", "shelf_life_days": 1},
                {"name": "🫕 麻辣烫", "category": "food", "price": 5, "desc": "自选配菜麻辣烫", "shelf_life_days": 1},
                {"name": "🥡 宫保鸡丁", "category": "food", "price": 4, "desc": "花生米嘎嘣脆", "shelf_life_days": 1},
            ],
        },
        "dessert": {
            "name": "🍨 甜品站",
            "items": [
                {"name": "🍨 芒果冰沙", "category": "food", "price": 4, "desc": "新鲜芒果打的冰沙", "shelf_life_days": 1},
                {"name": "🧋 珍珠奶茶", "category": "food", "price": 4, "desc": "波霸珍珠奶茶", "shelf_life_days": 1},
                {"name": "🍡 团子", "category": "food", "price": 2, "desc": "三色糯米团子", "shelf_life_days": 2},
                {"name": "🥧 苹果派", "category": "food", "price": 3, "desc": "肉桂苹果派", "shelf_life_days": 2},
                {"name": "🍧 刨冰", "category": "food", "price": 3, "desc": "红豆抹茶刨冰", "shelf_life_days": 1},
                {"name": "🫘 红豆汤", "category": "food", "price": 2, "desc": "温热的红豆汤", "shelf_life_days": 1},
            ],
        },
        "snack": {
            "name": "🍿 零食小铺",
            "items": [
                {"name": "🍿 爆米花", "category": "food", "price": 2, "desc": "焦糖味爆米花", "shelf_life_days": 7},
                {"name": "🥜 坚果拼盘", "category": "food", "price": 4, "desc": "腰果杏仁核桃夏威夷果", "shelf_life_days": 30},
                {"name": "🍫 巧克力棒", "category": "food", "price": 3, "desc": "夹心巧克力棒", "shelf_life_days": 90},
                {"name": "🍘 仙贝", "category": "food", "price": 2, "desc": "旺旺大礼包同款", "shelf_life_days": 60},
                {"name": "🥨 椒盐脆饼", "category": "food", "price": 2, "desc": "嘎嘣脆的椒盐饼", "shelf_life_days": 30},
                {"name": "🧀 芝士条", "category": "food", "price": 3, "desc": "拉丝芝士条", "shelf_life_days": 14},
            ],
        },
    }

    def _get_today_food_shop(self) -> Optional[Dict]:
        """获取今日主题食品店（每天随机一家）"""
        today = datetime.now().strftime("%Y-%m-%d")
        # 用日期做种子，保证同一天同一家店
        seed = int(today.replace("-", ""))
        rng = random.Random(seed)
        shop_key = rng.choice(list(self.FOOD_SHOPS.keys()))
        return self.FOOD_SHOPS[shop_key]

    def needs_refresh(self) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data.get("date") != today

    def _inject_special_items(self, items: List[Dict]) -> List[Dict]:
        """在普通商品列表上注入节日商品和收藏品（替换，不追加）"""
        result = list(items)

        # 1. 节日商品：当天替换
        holiday = get_holiday()
        if holiday and holiday in HOLIDAY_ITEMS:
            holiday_items = HOLIDAY_ITEMS[holiday]
            for hi in holiday_items:
                if len(result) > 0:
                    # 替换一个随机普通商品
                    idx = random.randint(0, len(result) - 1)
                    result[idx] = hi

        # 2. 收藏品：2%概率替换一个普通商品
        collectibles = self.item_pool.get("collectible", [])
        if collectibles and random.random() < 0.02:
            idx = random.randint(0, len(result) - 1)
            result[idx] = random.choice(collectibles)

        return result

    def refresh_with_defaults(self):
        """使用默认商品池刷新"""
        today = datetime.now().strftime("%Y-%m-%d")
        season = get_season()

        pool = list(self.item_pool.get("all_season", []))
        pool += self.item_pool.get(season, [])

        count = min(self.daily_item_count, len(pool))
        selected = random.sample(pool, count)
        selected = self._inject_special_items(selected)
        self._build_shop(today, selected)

    def refresh_with_ai_items(self, ai_items: List[Dict]):
        """使用AI生成的普通商品，再注入节日/收藏品"""
        today = datetime.now().strftime("%Y-%m-%d")
        items = self._inject_special_items(ai_items)
        self._build_shop(today, items)

    def _build_shop(self, today: str, items: List[Dict]):
        shop_items = []
        for i, item in enumerate(items, 1):
            shop_item = {
                "id": i,
                "name": item.get("name", "未知商品"),
                "category": item.get("category", "item"),
                "price": item.get("price", 1),
                "desc": item.get("desc", ""),
                "stock": random.randint(1, 5),
            }
            if item.get("shelf_life_days"):
                shop_item["shelf_life_days"] = item["shelf_life_days"]
            shop_items.append(shop_item)

        self.data["date"] = today
        self.data["items"] = shop_items
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.data["purchase_log"] = [
            log for log in self.data.get("purchase_log", [])
            if log.get("time", "") >= cutoff
        ]
        self._save_data()

        holiday = get_holiday()
        holiday_str = f"（{holiday}）" if holiday else ""
        logger.info(f"[Shop] 货架已刷新{holiday_str}，上架 {len(shop_items)} 种商品")

    def get_today_items(self) -> List[Dict]:
        if self.needs_refresh():
            self.refresh_with_defaults()
        return [item for item in self.data["items"] if item.get("stock", 0) > 0]

    def buy_item(self, item_id: int, buyer_id: str) -> Optional[Dict]:
        if self.needs_refresh():
            self.refresh_with_defaults()
        for item in self.data["items"]:
            if item["id"] == item_id and item.get("stock", 0) > 0:
                # 收藏品唯一性检查
                if item.get("category") == "collectible":
                    if self.has_collectible(buyer_id, item["name"]):
                        return {"error": "already_owned", "name": item["name"]}
                item["stock"] -= 1
                purchased = {
                    "name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                    "desc": item["desc"],
                }
                if item.get("shelf_life_days"):
                    purchased["expires_at"] = (
                        datetime.now() + timedelta(days=item["shelf_life_days"])
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    purchased["shelf_life_days"] = item["shelf_life_days"]
                # 记录收藏品
                if item["category"] == "collectible":
                    self._record_collectible(buyer_id, item["name"])
                self.data["purchase_log"].append({
                    "buyer": buyer_id, "item": item["name"],
                    "price": item["price"],
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                self._save_data()
                return purchased
        return None

    def find_item_by_name(self, name: str) -> Optional[Dict]:
        if self.needs_refresh():
            self.refresh_with_defaults()
        query = name.strip().lower().replace(" ", "")
        query_no_emoji = _strip_emoji(name).lower().replace(" ", "")
        # 先找超市
        for item in self.data["items"]:
            if item.get("stock", 0) > 0:
                item_full = item["name"].strip().lower().replace(" ", "")
                item_no_emoji = _strip_emoji(item["name"]).lower().replace(" ", "")
                if query in (item_full, item_no_emoji) or query_no_emoji in (item_full, item_no_emoji):
                    return item
        # 再找今日食品店
        food_shop = self._get_today_food_shop()
        if food_shop:
            for fs_item in food_shop["items"]:
                item_full = fs_item["name"].strip().lower().replace(" ", "")
                item_no_emoji = _strip_emoji(fs_item["name"]).lower().replace(" ", "")
                if query in (item_full, item_no_emoji) or query_no_emoji in (item_full, item_no_emoji):
                    return {"_food_shop": True, **fs_item}
        return None

    def buy_food_shop_item(self, item_name: str, buyer_id: str) -> Optional[Dict]:
        """从今日食品店购买"""
        food_shop = self._get_today_food_shop()
        if not food_shop:
            return None
        for fs_item in food_shop["items"]:
            if _strip_emoji(fs_item["name"]).lower().replace(" ", "") == _strip_emoji(item_name).lower().replace(" ", "") \
               or fs_item["name"].strip().lower().replace(" ", "") == item_name.strip().lower().replace(" ", ""):
                purchased = {
                    "name": fs_item["name"],
                    "category": fs_item["category"],
                    "price": fs_item["price"],
                    "desc": fs_item["desc"],
                }
                if fs_item.get("shelf_life_days"):
                    purchased["expires_at"] = (
                        datetime.now() + timedelta(days=fs_item["shelf_life_days"])
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    purchased["shelf_life_days"] = fs_item["shelf_life_days"]
                self.data["purchase_log"].append({
                    "buyer": buyer_id, "item": fs_item["name"],
                    "price": fs_item["price"],
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                self._save_data()
                return purchased
        return None

    def format_shop_display(self, user_id: str = "") -> str:
        items = self.get_today_items()
        if not items:
            return "🏪 今日超市已售罄，明天再来吧~"

        owned = self.get_owned_collectibles(user_id) if user_id else []

        cat_emoji = {"food": "🍱", "item": "🎪", "decoration": "✨",
                     "collectible": "🏅", "flower": "💐"}
        cat_name = {"food": "食品", "item": "道具", "decoration": "装饰",
                    "collectible": "收藏品", "flower": "鲜花"}

        season_name = {"spring": "🌸春", "summer": "☀️夏", "autumn": "🍂秋", "winter": "❄️冬"}
        holiday = get_holiday()
        header = f"🏪 今日超市（{self.data['date']}）"
        header += f" {season_name.get(get_season(), '')}"
        if holiday:
            header += f" 🎉{holiday}"

        lines = [header + "\n"]

        # 今日主题食品店
        food_shop = self._get_today_food_shop()
        if food_shop:
            lines.append(f"╔═ {food_shop['name']} ═╗")
            for fs_item in food_shop["items"]:
                shelf = f" | {fs_item.get('shelf_life_days', 1)}天保质" if fs_item.get("shelf_life_days") else ""
                lines.append(f"  🍽️ {fs_item['name']} - {fs_item['price']}元{shelf}")
                lines.append(f"     {fs_item['desc']}")
            lines.append(f"╚═══════════════╝\n")

        # 普通超市
        lines.append("── 便利超市 ──")
        for item in items:
            emoji = cat_emoji.get(item["category"], "📦")
            cat = cat_name.get(item["category"], "其他")
            shelf = ""
            if item.get("shelf_life_days"):
                shelf = f" | 保质期{item['shelf_life_days']}天"
            elif item["category"] == "collectible":
                shelf = " | ⚠️永久收藏·稀有"

            owned_tag = ""
            if item["category"] == "collectible" and item["name"] in owned:
                owned_tag = " ✅已拥有"

            collectible_tag = " 🌟稀有!" if item["category"] == "collectible" and not owned_tag else ""
            lines.append(
                f"{emoji} [{item['id']}] {item['name']} - {item['price']}元"
                f" | {cat} | 库存{item['stock']}{shelf}{collectible_tag}{owned_tag}"
            )
            lines.append(f"   📝 {item['desc']}")

        lines.append(f"\n💡 购买超市商品：购买 <编号>")
        lines.append(f"💡 购买食品店：购买 <食品名>")
        return "\n".join(lines)

    @staticmethod
    def build_ai_prompt() -> str:
        """构建AI生成普通商品的prompt（不含收藏品和节日）"""
        season = get_season()
        season_cn = {"spring": "春天", "summer": "夏天", "autumn": "秋天", "winter": "冬天"}
        forbidden = "、".join(_FORBIDDEN_EMOJIS)

        prompt = (
            f"你是一个虚拟超市的进货员。现在是{season_cn[season]}。\n"
            f"请生成10个日常超市商品，要求：\n"
            f"- 7-8个食品(food)，带保质期(shelf_life_days)，范围1-90天\n"
            f"- 1-2个鲜花(flower)，带保鲜期(shelf_life_days)，3-7天\n"
            f"- 1个日用品/小物件(item)\n\n"
            f"命名规范：用一个emoji+朴素名称，如「🍇葡萄」「🧻纸巾」「🌷郁金香」。\n"
            f"不要起花哨原创名，就是超市货架上普通的东西。\n"
            f"根据季节选择应季商品。\n"
            f"价格：食品1-8元，鲜花3-8元，日用品1-5元。\n"
            f"描述：简短朴素一句话。\n\n"
            f"禁止使用以下emoji（已被其他系统占用）：{forbidden}\n"
            f"禁止生成收藏品(collectible)类别。\n\n"
            f"只输出JSON数组，格式：\n"
            f'[{{"name":"🍇葡萄","category":"food","price":3,'
            f'"desc":"一串紫葡萄","shelf_life_days":5}}]\n'
            f"不要输出其他任何内容。"
        )
        return prompt
