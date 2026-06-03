import json
import os
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from astrbot.api import logger


def _strip_emoji(text: str) -> str:
    import re
    cleaned = re.sub(r'^[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F\u200D\u20E3\u2000-\u3300]+\s*', '', text)
    return cleaned.strip() if cleaned.strip() else text.strip()


# ========== 季节/节日 ==========

def get_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5): return "spring"
    if month in (6, 7, 8): return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"

def get_holiday() -> str:
    m, d = datetime.now().month, datetime.now().day
    holidays = {
        (1, 1): "元旦", (2, 14): "情人节", (3, 8): "妇女节",
        (4, 1): "愚人节", (5, 1): "劳动节", (5, 4): "青年节",
        (6, 1): "儿童节", (10, 1): "国庆节", (10, 31): "万圣节",
        (12, 24): "平安夜", (12, 25): "圣诞节",
    }
    return holidays.get((m, d), "")


# ========== 收藏品 emoji 黑名单 ==========

_COLLECTIBLE_EMOJIS = {
    "🦆", "🐱", "🤡", "🐟", "🪲", "🥬", "🕊️", "🍳", "⌨️", "🍋",
    "🍗", "💇", "🏀", "🐠", "🔪", "🔌", "🖥️", "📺", "☁️", "🎓",
    "🍅", "🔘", "🧊",
}
_HOLIDAY_EMOJIS = {"🎄", "🎅", "🎃", "👻", "🎆", "🧨", "💘", "🌹", "🎁", "🎊"}
_FORBIDDEN_EMOJIS = _COLLECTIBLE_EMOJIS | _HOLIDAY_EMOJIS


# ========== 固定店铺定义 ==========

FIXED_SHOPS: Dict[str, Dict] = {
    "便利超市": {
        "emoji": "🏪",
        "desc": "日常用品和应季商品",
        "type": "convenience",  # 特殊类型：季节刷新 + 收藏品
    },
    "蛋糕店": {
        "emoji": "🎂",
        "desc": "甜蜜的糕点和面包",
        "items": [
            {"name": "🍰 草莓蛋糕", "category": "food", "price": 6, "desc": "铺满草莓的奶油蛋糕", "shelf_life_days": 2},
            {"name": "🧁 杯子蛋糕", "category": "food", "price": 3, "desc": "巧克力霜淇淋杯子蛋糕", "shelf_life_days": 3},
            {"name": "🍩 甜甜圈", "category": "food", "price": 2, "desc": "糖霜甜甜圈", "shelf_life_days": 2},
            {"name": "🥐 可颂", "category": "food", "price": 3, "desc": "黄油可颂，外酥里嫩", "shelf_life_days": 1},
            {"name": "🍮 焦糖布丁", "category": "food", "price": 4, "desc": "表面焦脆的经典布丁", "shelf_life_days": 2},
            {"name": "🧇 华夫饼", "category": "food", "price": 3, "desc": "淋蜂蜜的格子华夫", "shelf_life_days": 1},
            {"name": "🥧 苹果派", "category": "food", "price": 3, "desc": "肉桂苹果派", "shelf_life_days": 2},
            {"name": "🍞 吐司面包", "category": "food", "price": 2, "desc": "手撕吐司，松软拉丝", "shelf_life_days": 3},
        ],
    },
    "烤肉店": {
        "emoji": "🥩",
        "desc": "炭火香气，大口吃肉",
        "items": [
            {"name": "🥩 和牛五花", "category": "food", "price": 8, "desc": "A5和牛雪花五花肉", "shelf_life_days": 1},
            {"name": "🍖 秘制猪排", "category": "food", "price": 4, "desc": "酱烤猪排", "shelf_life_days": 1},
            {"name": "🍗 蜜汁鸡翅", "category": "food", "price": 3, "desc": "蜜汁烤鸡翅", "shelf_life_days": 1},
            {"name": "🌽 烤玉米", "category": "food", "price": 2, "desc": "刷酱烤玉米", "shelf_life_days": 1},
            {"name": "🫑 烤青椒", "category": "food", "price": 1, "desc": "微辣烤青椒", "shelf_life_days": 1},
            {"name": "🍢 烤串拼盘", "category": "food", "price": 5, "desc": "羊肉串+牛肉串+鸡心", "shelf_life_days": 1},
        ],
    },
    "快餐店": {
        "emoji": "🍔",
        "desc": "快乐套餐，即买即走",
        "items": [
            {"name": "🍔 经典汉堡", "category": "food", "price": 4, "desc": "双层牛肉芝士汉堡", "shelf_life_days": 1},
            {"name": "🍟 大份薯条", "category": "food", "price": 2, "desc": "金黄脆薯条", "shelf_life_days": 1},
            {"name": "🌮 墨西哥卷", "category": "food", "price": 3, "desc": "鸡肉牛油果卷", "shelf_life_days": 1},
            {"name": "🌭 热狗", "category": "food", "price": 2, "desc": "美式芥末热狗", "shelf_life_days": 1},
            {"name": "🥤 冰可乐", "category": "food", "price": 2, "desc": "冰镇可乐", "shelf_life_days": 30},
            {"name": "🍕 芝士披萨", "category": "food", "price": 5, "desc": "拉丝芝士薄底披萨", "shelf_life_days": 1},
        ],
    },
    "家常菜馆": {
        "emoji": "🥢",
        "desc": "妈妈的味道",
        "items": [
            {"name": "🥘 红烧肉", "category": "food", "price": 6, "desc": "肥而不腻的红烧肉", "shelf_life_days": 1},
            {"name": "🍜 兰州拉面", "category": "food", "price": 4, "desc": "一清二白三红四绿五黄", "shelf_life_days": 1},
            {"name": "🥟 小笼包", "category": "food", "price": 3, "desc": "鲜肉小笼包一屉", "shelf_life_days": 1},
            {"name": "🍚 蛋炒饭", "category": "food", "price": 3, "desc": "粒粒分明的蛋炒饭", "shelf_life_days": 1},
            {"name": "🫕 麻辣烫", "category": "food", "price": 5, "desc": "自选配菜麻辣烫", "shelf_life_days": 1},
            {"name": "🥡 宫保鸡丁", "category": "food", "price": 4, "desc": "花生米嘎嘣脆", "shelf_life_days": 1},
        ],
    },
    "甜品站": {
        "emoji": "🍨",
        "desc": "甜蜜补给站",
        "items": [
            {"name": "🍨 芒果冰沙", "category": "food", "price": 4, "desc": "新鲜芒果冰沙", "shelf_life_days": 1},
            {"name": "🧋 珍珠奶茶", "category": "food", "price": 4, "desc": "波霸珍珠奶茶", "shelf_life_days": 1},
            {"name": "🍡 三色团子", "category": "food", "price": 2, "desc": "糯米团子", "shelf_life_days": 2},
            {"name": "🍧 红豆刨冰", "category": "food", "price": 3, "desc": "红豆抹茶刨冰", "shelf_life_days": 1},
            {"name": "🫘 红豆汤", "category": "food", "price": 2, "desc": "温热红豆汤", "shelf_life_days": 1},
            {"name": "🥛 双皮奶", "category": "food", "price": 3, "desc": "姜撞双皮奶", "shelf_life_days": 1},
        ],
    },
    "零食铺": {
        "emoji": "🍿",
        "desc": "追剧必备零食",
        "items": [
            {"name": "🍿 焦糖爆米花", "category": "food", "price": 2, "desc": "焦糖味爆米花", "shelf_life_days": 7},
            {"name": "🥜 坚果拼盘", "category": "food", "price": 4, "desc": "腰果杏仁核桃", "shelf_life_days": 30},
            {"name": "🍫 巧克力棒", "category": "food", "price": 3, "desc": "夹心巧克力棒", "shelf_life_days": 90},
            {"name": "🍘 仙贝", "category": "food", "price": 2, "desc": "旺旺同款", "shelf_life_days": 60},
            {"name": "🥨 椒盐脆饼", "category": "food", "price": 2, "desc": "嘎嘣脆椒盐饼", "shelf_life_days": 30},
            {"name": "🧀 芝士条", "category": "food", "price": 3, "desc": "拉丝芝士条", "shelf_life_days": 14},
        ],
    },
    "花店": {
        "emoji": "💐",
        "desc": "鲜花与美好",
        "items": [
            {"name": "🌹 红玫瑰", "category": "flower", "price": 8, "desc": "一枝鲜红的玫瑰", "shelf_life_days": 5},
            {"name": "🌷 郁金香", "category": "flower", "price": 5, "desc": "粉色郁金香", "shelf_life_days": 5},
            {"name": "🌻 向日葵", "category": "flower", "price": 4, "desc": "一枝向日葵", "shelf_life_days": 5},
            {"name": "💐 混合花束", "category": "flower", "price": 10, "desc": "精选混合鲜花束", "shelf_life_days": 5},
            {"name": "🌸 樱花枝", "category": "flower", "price": 6, "desc": "一枝粉樱花", "shelf_life_days": 3},
            {"name": "🪻 薰衣草", "category": "flower", "price": 5, "desc": "一束干薰衣草", "shelf_life_days": 30},
        ],
    },
}


# ========== 便利超市默认商品池 ==========

CONVENIENCE_POOL = {
    "all_season": [
        {"name": "🍇 葡萄", "category": "food", "price": 3, "desc": "一串紫葡萄", "shelf_life_days": 5},
        {"name": "🍎 苹果", "category": "food", "price": 2, "desc": "红红的苹果", "shelf_life_days": 7},
        {"name": "🥛 牛奶", "category": "food", "price": 2, "desc": "一盒纯牛奶", "shelf_life_days": 7},
        {"name": "🍞 面包", "category": "food", "price": 2, "desc": "切片面包", "shelf_life_days": 3},
        {"name": "🧃 果汁", "category": "food", "price": 2, "desc": "盒装橙汁", "shelf_life_days": 14},
        {"name": "🍪 饼干", "category": "food", "price": 2, "desc": "原味饼干", "shelf_life_days": 60},
        {"name": "🥚 鸡蛋", "category": "food", "price": 1, "desc": "一颗鸡蛋", "shelf_life_days": 14},
        {"name": "🧻 纸巾", "category": "item", "price": 1, "desc": "一包抽纸"},
        {"name": "🖊️ 圆珠笔", "category": "item", "price": 1, "desc": "蓝色圆珠笔"},
        {"name": "⭐ 小星星", "category": "decoration", "price": 1, "desc": "亮晶晶的小星星"},
    ],
    "spring": [
        {"name": "🫖 茉莉花茶", "category": "food", "price": 3, "desc": "茉莉花茶包", "shelf_life_days": 90},
        {"name": "🥒 黄瓜", "category": "food", "price": 2, "desc": "新鲜黄瓜", "shelf_life_days": 5},
    ],
    "summer": [
        {"name": "🍉 西瓜", "category": "food", "price": 4, "desc": "冰镇大西瓜", "shelf_life_days": 2},
        {"name": "🍦 冰淇淋", "category": "food", "price": 3, "desc": "香草冰淇淋", "shelf_life_days": 1},
    ],
    "autumn": [
        {"name": "🌰 板栗", "category": "food", "price": 3, "desc": "糖炒板栗", "shelf_life_days": 7},
        {"name": "🍠 烤红薯", "category": "food", "price": 3, "desc": "热乎乎烤红薯", "shelf_life_days": 1},
    ],
    "winter": [
        {"name": "🥟 饺子", "category": "food", "price": 4, "desc": "猪肉白菜馅饺子", "shelf_life_days": 1},
        {"name": "☕ 热可可", "category": "food", "price": 3, "desc": "暖暖的热巧克力", "shelf_life_days": 1},
    ],
}

COLLECTIBLE_POOL = [
    {"name": "🦆 柯尔鸭", "category": "collectible", "price": 30, "desc": "致敬鸭鸭老师的限定收藏"},
    {"name": "🐱 薛定谔的猫罐头", "category": "collectible", "price": 25, "desc": "打开之前不知道里面有没有猫"},
    {"name": "🤡 打工人的面具", "category": "collectible", "price": 20, "desc": "戴上它，今天也是元气满满的一天呢！"},
    {"name": "🐟 失去梦想的咸鱼", "category": "collectible", "price": 18, "desc": "翻个身，发现依然是咸鱼"},
    {"name": "🪲 祖传代码Bug", "category": "collectible", "price": 35, "desc": "千万不要删！据说它是这个游戏运行的基石"},
    {"name": "🥬 一捆新鲜的韭菜", "category": "collectible", "price": 15, "desc": "你仿佛听到了镰刀挥舞的破风声"},
    {"name": "🕊️ 鸽子精的绒毛", "category": "collectible", "price": 22, "desc": "收集齐100根可兑换一个'下次一定更新'的承诺"},
    {"name": "🍳 黑漆漆的平底锅", "category": "collectible", "price": 20, "desc": "进可挡子弹，退可炒冷饭"},
    {"name": "⌨️ 键仙的遗物", "category": "collectible", "price": 28, "desc": "输入'懂得都懂'可造成真实伤害"},
    {"name": "🍋 发光的柠檬", "category": "collectible", "price": 15, "desc": "好酸啊！为什么别人都能抽到SSR"},
    {"name": "🍗 V我50的神秘炸鸡", "category": "collectible", "price": 25, "desc": "一到星期四就散发耀眼光芒的圣物"},
    {"name": "💇 强者的最后遗物", "category": "collectible", "price": 35, "desc": "全栈大佬跑通最后一个Bug时掉落的一撮头发"},
    {"name": "🏀 神秘的背带裤", "category": "collectible", "price": 20, "desc": "穿上它耳边会自动响起动感旋律"},
    {"name": "🐠 尊嘟假嘟测谎仪", "category": "collectible", "price": 22, "desc": "捏一下会发出'O.o'的声音"},
    {"name": "🖥️ 禁忌符咒rm -rf /", "category": "collectible", "price": 40, "desc": "威力过于强大的毁灭魔法"},
    {"name": "📺 下次一定硬币", "category": "collectible", "price": 15, "desc": "正面写着'白嫖'反面写着'下次'"},
    {"name": "☁️ 502护身符", "category": "collectible", "price": 20, "desc": "把所有访问请求拒之门外"},
    {"name": "🎓 赛博无敌学生证", "category": "collectible", "price": 25, "desc": "白嫖各路大厂云服务的无价之宝"},
    {"name": "🧊 融化的雪糕刺客", "category": "collectible", "price": 30, "desc": "结账时才发动致命一击"},
]

HOLIDAY_ITEMS = {
    "元旦": [{"name": "🎆 新年烟花糖", "category": "food", "price": 3, "desc": "噼里啪啦的跳跳糖", "shelf_life_days": 30}],
    "情人节": [
        {"name": "💘 心形巧克力", "category": "food", "price": 5, "desc": "粉色包装心形巧克力", "shelf_life_days": 30},
        {"name": "🌹 红玫瑰花束", "category": "flower", "price": 12, "desc": "情人节限定大花束", "shelf_life_days": 5},
    ],
    "儿童节": [
        {"name": "🍭 超大棒棒糖", "category": "food", "price": 2, "desc": "彩虹色大棒棒糖", "shelf_life_days": 60},
    ],
    "万圣节": [
        {"name": "🎃 南瓜灯", "category": "decoration", "price": 5, "desc": "笑嘻嘻的南瓜灯"},
        {"name": "👻 幽灵糖果", "category": "food", "price": 3, "desc": "白色幽灵形软糖", "shelf_life_days": 30},
    ],
    "圣诞节": [
        {"name": "🎄 迷你圣诞树", "category": "decoration", "price": 6, "desc": "桌上摆的小圣诞树"},
        {"name": "🎅 圣诞袜糖果", "category": "food", "price": 3, "desc": "红袜子里装满了糖", "shelf_life_days": 30},
    ],
}


class ShopManager:
    """
    多店铺购物系统
    - 固定店铺：便利超市（季节刷新+收藏品）+ 各主题食品店
    - AI动态店铺：用户想逛没有的店 → LLM 生成，当日缓存
    - 收藏品唯一：每人只能买一个
    """

    def __init__(self, data_dir: str, daily_item_count: int = 10, item_pool: Dict = None):
        self.data_dir = data_dir
        self.daily_item_count = daily_item_count
        self.item_pool = item_pool or CONVENIENCE_POOL
        os.makedirs(self.data_dir, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, "shop.json")
        if not os.path.exists(path):
            return {"date": "", "items": [], "purchase_log": [],
                    "owned_collectibles": {}, "ai_shops": {}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("date", "")
                data.setdefault("items", [])
                data.setdefault("purchase_log", [])
                data.setdefault("owned_collectibles", {})
                data.setdefault("ai_shops", {})
                return data
        except (json.JSONDecodeError, TypeError):
            return {"date": "", "items": [], "purchase_log": [],
                    "owned_collectibles": {}, "ai_shops": {}}

    def _save_data(self):
        path = os.path.join(self.data_dir, "shop.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ========== 收藏品唯一性 ==========

    def get_owned_collectibles(self, user_id: str) -> List[str]:
        return self.data.get("owned_collectibles", {}).get(user_id, [])

    def _record_collectible(self, user_id: str, item_name: str):
        owned = self.data.setdefault("owned_collectibles", {})
        user_list = owned.setdefault(user_id, [])
        if item_name not in user_list:
            user_list.append(item_name)
            self._save_data()

    def has_collectible(self, user_id: str, item_name: str) -> bool:
        return item_name in self.get_owned_collectibles(user_id)

    # ========== 店铺列表 ==========

    def get_all_shop_names(self) -> List[Dict]:
        """获取所有可用店铺（固定 + 今日AI生成的）"""
        shops = []
        for name, info in FIXED_SHOPS.items():
            shops.append({"name": name, "emoji": info["emoji"], "desc": info["desc"]})
        # 加上今日AI生成的店铺
        today = datetime.now().strftime("%Y-%m-%d")
        ai_shops = self.data.get("ai_shops", {}).get(today, {})
        for name, info in ai_shops.items():
            shops.append({"name": name, "emoji": info.get("emoji", "🏬"), "desc": info.get("desc", "")})
        return shops

    def format_shop_list(self) -> str:
        """格式化店铺列表"""
        shops = self.get_all_shop_names()
        holiday = get_holiday()
        header = "🛍️ 购物街"
        if holiday:
            header += f" 🎉{holiday}"

        lines = [header + "\n"]
        for s in shops:
            lines.append(f"  {s['emoji']} {s['name']} — {s['desc']}")
        lines.append(f"\n💡 逛店：逛 <店名>（如「逛蛋糕店」）")
        lines.append(f"💡 购买：购买 <商品名>")
        lines.append(f"💡 没有的店也可以逛，bot会现场开一家~")
        return "\n".join(lines)

    # ========== 便利超市（季节刷新） ==========

    def needs_refresh(self) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data.get("date") != today

    def refresh_convenience(self):
        """刷新便利超市"""
        today = datetime.now().strftime("%Y-%m-%d")
        season = get_season()

        pool = list(self.item_pool.get("all_season", []))
        pool += self.item_pool.get(season, [])

        count = min(self.daily_item_count, len(pool))
        selected = random.sample(pool, count)

        # 节日商品
        holiday = get_holiday()
        if holiday and holiday in HOLIDAY_ITEMS:
            for hi in HOLIDAY_ITEMS[holiday]:
                if selected:
                    idx = random.randint(0, len(selected) - 1)
                    selected[idx] = hi

        # 2%概率出收藏品
        if COLLECTIBLE_POOL and random.random() < 0.02:
            idx = random.randint(0, len(selected) - 1)
            selected[idx] = random.choice(COLLECTIBLE_POOL)

        shop_items = []
        for i, item in enumerate(selected, 1):
            shop_item = {
                "id": i, "name": item.get("name", "?"),
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
        # 清理旧AI店铺
        self.data["ai_shops"] = {today: self.data.get("ai_shops", {}).get(today, {})}
        # 清理旧日志
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.data["purchase_log"] = [
            log for log in self.data.get("purchase_log", []) if log.get("time", "") >= cutoff
        ]
        self._save_data()

    def refresh_with_ai_items(self, ai_items: List[Dict]):
        """AI生成的便利超市商品"""
        today = datetime.now().strftime("%Y-%m-%d")
        # 注入收藏品和节日
        selected = list(ai_items)
        holiday = get_holiday()
        if holiday and holiday in HOLIDAY_ITEMS:
            for hi in HOLIDAY_ITEMS[holiday]:
                if selected:
                    idx = random.randint(0, len(selected) - 1)
                    selected[idx] = hi
        if COLLECTIBLE_POOL and random.random() < 0.02:
            idx = random.randint(0, len(selected) - 1)
            selected[idx] = random.choice(COLLECTIBLE_POOL)

        shop_items = []
        for i, item in enumerate(selected, 1):
            shop_item = {
                "id": i, "name": item.get("name", "?"),
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
        self.data["ai_shops"] = {today: self.data.get("ai_shops", {}).get(today, {})}
        self._save_data()

    # ========== 浏览店铺 ==========

    def browse_shop(self, shop_name: str, user_id: str = "") -> Optional[str]:
        """浏览指定店铺，返回格式化的商品列表。None = 没有这家店"""
        owned = self.get_owned_collectibles(user_id) if user_id else []

        # 1. 便利超市
        if shop_name in ("便利超市", "超市", "便利店"):
            if self.needs_refresh():
                self.refresh_convenience()
            items = [i for i in self.data["items"] if i.get("stock", 0) > 0]
            if not items:
                return "🏪 便利超市今日已售罄~"
            lines = [f"🏪 便利超市\n"]
            for item in items:
                tag = ""
                if item["category"] == "collectible":
                    if item["name"] in owned:
                        tag = " ✅已拥有"
                    else:
                        tag = " 🌟稀有!"
                lines.append(f"  [{item['id']}] {item['name']} - {item['price']}元 | 库存{item['stock']}{tag}")
                lines.append(f"      {item['desc']}")
            lines.append(f"\n💡 购买 <编号> 或 购买 <商品名>")
            return "\n".join(lines)

        # 2. 固定主题店
        for fixed_name, info in FIXED_SHOPS.items():
            if shop_name in (fixed_name, _strip_emoji(fixed_name)):
                if info.get("type") == "convenience":
                    return self.browse_shop("便利超市", user_id)
                items = info.get("items", [])
                if not items:
                    return None
                lines = [f"{info['emoji']} {fixed_name} — {info['desc']}\n"]
                for item in items:
                    shelf = f" | {item.get('shelf_life_days', 1)}天" if item.get("shelf_life_days") else ""
                    lines.append(f"  🍽️ {item['name']} - {item['price']}元{shelf}")
                    lines.append(f"      {item['desc']}")
                lines.append(f"\n💡 购买 <商品名>")
                return "\n".join(lines)

        # 3. 今日AI生成的店铺
        today = datetime.now().strftime("%Y-%m-%d")
        ai_shops = self.data.get("ai_shops", {}).get(today, {})
        if shop_name in ai_shops:
            info = ai_shops[shop_name]
            lines = [f"{info.get('emoji', '🏬')} {shop_name} — {info.get('desc', '')}\n"]
            for item in info.get("items", []):
                shelf = f" | {item.get('shelf_life_days', 1)}天" if item.get("shelf_life_days") else ""
                lines.append(f"  🍽️ {item['name']} - {item['price']}元{shelf}")
                lines.append(f"      {item.get('desc', '')}")
            lines.append(f"\n💡 购买 <商品名>")
            return "\n".join(lines)

        # 4. 没找到
        return None

    def save_ai_shop(self, shop_name: str, shop_data: Dict):
        """保存AI生成的店铺（当日缓存）"""
        today = datetime.now().strftime("%Y-%m-%d")
        ai_shops = self.data.setdefault("ai_shops", {})
        day_shops = ai_shops.setdefault(today, {})
        day_shops[shop_name] = shop_data
        self._save_data()
        logger.info(f"[Shop] AI生成店铺已保存：{shop_name}（{len(shop_data.get('items', []))}种商品）")

    # ========== 购买 ==========

    def find_item_across_shops(self, item_name: str) -> Optional[Tuple[Dict, str]]:
        """跨所有店铺搜索商品。返回 (item_dict, shop_name) 或 None"""
        query = item_name.strip().lower().replace(" ", "")
        query_ne = _strip_emoji(item_name).lower().replace(" ", "")

        def _match(name):
            n = name.strip().lower().replace(" ", "")
            n_ne = _strip_emoji(name).lower().replace(" ", "")
            return query in (n, n_ne) or query_ne in (n, n_ne)

        # 便利超市
        if self.needs_refresh():
            self.refresh_convenience()
        for item in self.data["items"]:
            if item.get("stock", 0) > 0 and _match(item["name"]):
                return item, "便利超市"

        # 固定主题店
        for shop_name, info in FIXED_SHOPS.items():
            for item in info.get("items", []):
                if _match(item["name"]):
                    return {**item, "_shop": shop_name}, shop_name

        # AI店铺
        today = datetime.now().strftime("%Y-%m-%d")
        for shop_name, info in self.data.get("ai_shops", {}).get(today, {}).items():
            for item in info.get("items", []):
                if _match(item["name"]):
                    return {**item, "_shop": shop_name}, shop_name

        return None

    def buy_from_shop(self, item_name: str, buyer_id: str) -> Optional[Dict]:
        """跨店购买商品"""
        result = self.find_item_across_shops(item_name)
        if not result:
            return None

        item, shop_name = result

        # 收藏品唯一性
        if item.get("category") == "collectible":
            if self.has_collectible(buyer_id, item["name"]):
                return {"error": "already_owned", "name": item["name"]}

        # 便利超市商品要减库存
        if shop_name == "便利超市":
            for si in self.data["items"]:
                if si["name"] == item["name"] and si.get("stock", 0) > 0:
                    si["stock"] -= 1
                    break

        purchased = {
            "name": item["name"],
            "category": item.get("category", "food"),
            "price": item["price"],
            "desc": item.get("desc", ""),
            "shop": shop_name,
        }
        if item.get("shelf_life_days"):
            purchased["expires_at"] = (
                datetime.now() + timedelta(days=item["shelf_life_days"])
            ).strftime("%Y-%m-%d %H:%M:%S")
            purchased["shelf_life_days"] = item["shelf_life_days"]

        if item.get("category") == "collectible":
            self._record_collectible(buyer_id, item["name"])

        self.data["purchase_log"].append({
            "buyer": buyer_id, "item": item["name"],
            "price": item["price"], "shop": shop_name,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self._save_data()
        return purchased

    # 兼容旧接口
    def buy_item(self, item_id: int, buyer_id: str) -> Optional[Dict]:
        """按编号从便利超市购买"""
        if self.needs_refresh():
            self.refresh_convenience()
        for item in self.data["items"]:
            if item["id"] == item_id and item.get("stock", 0) > 0:
                return self.buy_from_shop(item["name"], buyer_id)
        return None

    def get_today_items(self) -> List[Dict]:
        if self.needs_refresh():
            self.refresh_convenience()
        return [item for item in self.data["items"] if item.get("stock", 0) > 0]

    def find_item_by_name(self, name: str) -> Optional[Dict]:
        result = self.find_item_across_shops(name)
        return result[0] if result else None

    def format_shop_display(self, user_id: str = "") -> str:
        """兼容旧接口 → 返回店铺列表"""
        return self.format_shop_list()

    # ========== AI 生成店铺 prompt ==========

    @staticmethod
    def build_ai_shop_prompt(shop_name: str) -> str:
        """构建AI生成主题店铺的prompt"""
        return (
            f"你是一个虚拟购物街的店长，要开一家「{shop_name}」。\n"
            f"请生成6-8个符合这家店主题的商品，要求：\n"
            f"- 每个商品用一个emoji+名称，如「🍰草莓蛋糕」\n"
            f"- 价格1-10元\n"
            f"- 食品要有保质期(shelf_life_days)，1-90天\n"
            f"- 描述简短朴素一句话\n"
            f"- category全部填food\n\n"
            f"另外给这家店取一个emoji和一句短描述。\n\n"
            f"只输出JSON，格式：\n"
            f'{{"emoji":"🍰","desc":"一句店铺描述","items":['
            f'{{"name":"🍰草莓蛋糕","category":"food","price":6,'
            f'"desc":"铺满草莓的奶油蛋糕","shelf_life_days":2}}]}}\n'
            f"不要输出其他任何内容。"
        )

    @staticmethod
    def build_ai_prompt() -> str:
        """构建AI生成便利超市普通商品的prompt"""
        season = get_season()
        season_cn = {"spring": "春天", "summer": "夏天", "autumn": "秋天", "winter": "冬天"}
        forbidden = "、".join(_FORBIDDEN_EMOJIS)
        return (
            f"你是一个虚拟超市的进货员。现在是{season_cn[season]}。\n"
            f"请生成10个日常超市商品，要求：\n"
            f"- 7-8个食品(food)，带保质期(shelf_life_days)，1-90天\n"
            f"- 1-2个鲜花(flower)，保鲜期3-7天\n"
            f"- 1个日用品(item)\n\n"
            f"命名规范：emoji+朴素名称。根据季节选应季商品。\n"
            f"价格：食品1-8元，鲜花3-8元，日用品1-5元。\n"
            f"禁止使用emoji：{forbidden}\n"
            f"禁止生成collectible类别。\n\n"
            f"只输出JSON数组。"
        )
