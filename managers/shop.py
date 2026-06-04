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
        (4, 1): "愚人节", (5, 1): "劳动节", (6, 1): "儿童节",
        (10, 1): "国庆节", (10, 31): "万圣节",
        (12, 24): "平安夜", (12, 25): "圣诞节",
    }
    return holidays.get((m, d), "")


_FORBIDDEN_EMOJIS = {
    "🦆", "🐱", "🤡", "🐟", "🪲", "🥬", "🕊️", "🍳", "⌨️", "🍋",
    "🍗", "💇", "🏀", "🐠", "🔪", "🔌", "🖥️", "📺", "☁️", "🎓",
    "🍅", "🔘", "🧊", "🎄", "🎅", "🎃", "👻", "🎆", "🧨", "💘", "🌹", "🎁", "🎊",
}


# ================================================================
#  30+ 家主题店铺（每日随机开 ~7 家，便利超市固定）
# ================================================================

def _s(name, price, desc, days=None):
    """快捷生成商品dict"""
    d = {"name": name, "category": "food", "price": price, "desc": desc}
    if days:
        d["shelf_life_days"] = days
    return d

THEMED_SHOPS: Dict[str, Dict] = {
    # ====== 中式 ======
    "家常菜馆": {
        "emoji": "🥢", "desc": "妈妈的味道",
        "items": [
            _s("🥘 红烧肉", 6, "肥而不腻", 1), _s("🍜 兰州拉面", 4, "一清二白三红四绿", 1),
            _s("🥟 小笼包", 3, "鲜肉一屉", 1), _s("🍚 蛋炒饭", 3, "粒粒分明", 1),
            _s("🫕 麻辣烫", 5, "自选配菜", 1), _s("🥡 宫保鸡丁", 4, "花生米嘎嘣脆", 1),
        ],
    },
    "饺子馆": {
        "emoji": "🥟", "desc": "好吃不过饺子",
        "items": [
            _s("🥟 猪肉白菜饺", 3, "经典家常", 1), _s("🥟 韭菜鸡蛋饺", 3, "素馅清香", 1),
            _s("🥟 三鲜水饺", 4, "虾仁鲜肉", 1), _s("🥟 酸汤水饺", 4, "酸辣开胃", 1),
            _s("🫘 八宝粥", 2, "配饺子绝了", 1),
        ],
    },
    "火锅店": {
        "emoji": "🍲", "desc": "没有什么是一顿火锅解决不了的",
        "items": [
            _s("🍲 麻辣锅底", 5, "牛油麻辣锅", 1), _s("🥩 肥牛卷", 4, "鲜切肥牛", 1),
            _s("🧆 牛肉丸", 3, "手打Q弹", 1), _s("🥬 蔬菜拼盘", 2, "菠菜豆腐", 1),
            _s("🫕 番茄鸳鸯锅", 6, "一半麻辣一半番茄", 1), _s("🍢 关东煮拼盘", 3, "萝卜鱼丸", 1),
        ],
    },
    "烧烤摊": {
        "emoji": "🔥", "desc": "夜市撸串走起",
        "items": [
            _s("🍢 羊肉串x5", 5, "孜然羊肉串", 1), _s("🌽 烤玉米", 2, "刷酱烤玉米", 1),
            _s("🍗 烤鸡翅", 3, "蜜汁鸡翅", 1), _s("🫑 烤韭菜", 2, "烤韭菜把子", 1),
            _s("🍺 汽水", 2, "冰镇橘子汽水", 1), _s("🥚 烤鹌鹑蛋", 2, "一串五个", 1),
        ],
    },
    "早餐铺": {
        "emoji": "🌅", "desc": "元气早安",
        "items": [
            _s("🥞 煎饼果子", 3, "加蛋加肠", 1), _s("🫓 肉夹馍", 3, "腊汁肉夹馍", 1),
            _s("🥛 热豆浆", 2, "现磨豆浆", 1), _s("🧆 油条", 1, "炸得金黄", 1),
            _s("🍜 胡辣汤", 2, "河南胡辣汤", 1), _s("🥚 茶叶蛋", 1, "卤得入味", 1),
        ],
    },
    "粥铺": {
        "emoji": "🥣", "desc": "暖心暖胃",
        "items": [
            _s("🥣 皮蛋瘦肉粥", 3, "经典咸粥", 1), _s("🥣 南瓜小米粥", 2, "养胃暖粥", 1),
            _s("🥣 八宝粥", 3, "料足甜粥", 1), _s("🥣 鱼片粥", 4, "鲜鱼粥底", 1),
            _s("🥠 花卷", 1, "松软花卷", 1),
        ],
    },
    "串串香": {
        "emoji": "🍡", "desc": "数签签结账",
        "items": [
            _s("🍡 牛肉串x3", 3, "嫩滑牛肉", 1), _s("🍡 鹌鹑蛋串", 2, "卤鹌鹑蛋", 1),
            _s("🍡 藕片串", 1, "脆藕片", 1), _s("🍡 豆皮串", 1, "麻辣豆皮", 1),
            _s("🍡 毛肚串", 3, "七上八下", 1), _s("🥤 酸梅汤", 2, "解辣神器", 1),
        ],
    },
    # ====== 西式/日韩 ======
    "快餐店": {
        "emoji": "🍔", "desc": "快乐套餐即买即走",
        "items": [
            _s("🍔 经典汉堡", 4, "双层牛肉芝士", 1), _s("🍟 大份薯条", 2, "金黄脆薯条", 1),
            _s("🌮 墨西哥卷", 3, "鸡肉牛油果", 1), _s("🌭 热狗", 2, "芥末热狗", 1),
            _s("🥤 冰可乐", 2, "冰镇可乐", 30), _s("🍕 芝士披萨", 5, "拉丝芝士薄底", 1),
        ],
    },
    "寿司店": {
        "emoji": "🍣", "desc": "新鲜，一贯入魂",
        "items": [
            _s("🍣 三文鱼寿司", 5, "厚切三文鱼", 1), _s("🍣 鳗鱼寿司", 6, "蒲烧鳗鱼", 1),
            _s("🍣 玉子烧寿司", 3, "甜甜的玉子", 1), _s("🍙 饭团", 2, "梅干饭团", 1),
            _s("🍜 味噌汤", 2, "豆腐海带味噌", 1), _s("🥢 天妇罗", 4, "炸虾天妇罗", 1),
        ],
    },
    "拉面馆": {
        "emoji": "🍜", "desc": "汤头是灵魂",
        "items": [
            _s("🍜 豚骨拉面", 5, "浓白豚骨汤底", 1), _s("🍜 味噌拉面", 5, "北海道味噌", 1),
            _s("🍜 酱油拉面", 4, "清爽酱油汤", 1), _s("🥚 溏心蛋", 2, "加一颗溏心蛋", 1),
            _s("🥟 煎饺", 3, "锅贴煎饺", 1),
        ],
    },
    "韩餐店": {
        "emoji": "🥘", "desc": "辣得过瘾",
        "items": [
            _s("🥘 部队火锅", 6, "泡面年糕午餐肉", 1), _s("🍚 石锅拌饭", 4, "锅巴脆脆", 1),
            _s("🥟 韩式炸鸡", 5, "甜辣炸鸡", 1), _s("🍢 辣炒年糕", 3, "软糯辣甜", 1),
            _s("🥬 泡菜", 2, "正宗韩式泡菜", 7),
        ],
    },
    "意面屋": {
        "emoji": "🍝", "desc": "Al dente 就对了",
        "items": [
            _s("🍝 番茄肉酱面", 5, "经典bolognese", 1), _s("🍝 奶油培根面", 5, "carbonara", 1),
            _s("🍝 青酱意面", 4, "罗勒青酱", 1), _s("🥗 凯撒沙拉", 3, "配面包丁", 1),
            _s("🧀 焗芝士通心粉", 4, "芝士拉丝", 1),
        ],
    },
    # ====== 烘焙/甜品/饮品 ======
    "蛋糕店": {
        "emoji": "🎂", "desc": "甜蜜的糕点和面包",
        "items": [
            _s("🍰 草莓蛋糕", 6, "草莓奶油蛋糕", 2), _s("🧁 杯子蛋糕", 3, "巧克力杯子蛋糕", 3),
            _s("🍩 甜甜圈", 2, "糖霜甜甜圈", 2), _s("🥐 可颂", 3, "黄油可颂", 1),
            _s("🍮 焦糖布丁", 4, "焦脆布丁", 2), _s("🧇 华夫饼", 3, "蜂蜜华夫", 1),
        ],
    },
    "面包房": {
        "emoji": "🥖", "desc": "刚出炉的香气",
        "items": [
            _s("🥖 法棍", 3, "外脆里软法棍", 1), _s("🍞 吐司", 2, "手撕吐司", 3),
            _s("🥯 贝果", 3, "芝麻贝果", 2), _s("🧁 肉松卷", 3, "咸甜肉松面包", 2),
            _s("🥐 丹麦酥", 3, "千层丹麦", 1), _s("🍞 蜂蜜小面包", 2, "迷你蜂蜜包", 2),
        ],
    },
    "甜品站": {
        "emoji": "🍨", "desc": "甜蜜补给站",
        "items": [
            _s("🍨 芒果冰沙", 4, "新鲜芒果冰沙", 1), _s("🍡 三色团子", 2, "糯米团子", 2),
            _s("🍧 红豆刨冰", 3, "红豆抹茶刨冰", 1), _s("🥛 双皮奶", 3, "姜撞双皮奶", 1),
            _s("🍮 芒果班戟", 4, "新鲜芒果班戟", 1),
        ],
    },
    "冰淇淋店": {
        "emoji": "🍦", "desc": "一口冰凉一口甜",
        "items": [
            _s("🍦 香草冰淇淋", 3, "经典香草", 1), _s("🍦 巧克力冰淇淋", 3, "浓郁巧克力", 1),
            _s("🍦 抹茶冰淇淋", 4, "日式抹茶", 1), _s("🍨 芒果圣代", 5, "芒果酱+冰淇淋", 1),
            _s("🧊 冰棍", 1, "老冰棍", 1),
        ],
    },
    "咖啡馆": {
        "emoji": "☕", "desc": "来杯提神的",
        "items": [
            _s("☕ 美式咖啡", 3, "经典美式", 1), _s("☕ 拿铁", 4, "丝滑拿铁", 1),
            _s("🧋 摩卡", 4, "巧克力摩卡", 1), _s("🍵 抹茶拿铁", 4, "抹茶+牛奶", 1),
            _s("🥐 司康", 3, "英式司康配奶油", 1), _s("🍰 提拉米苏", 5, "手工提拉米苏", 1),
        ],
    },
    "奶茶店": {
        "emoji": "🧋", "desc": "续命水",
        "items": [
            _s("🧋 珍珠奶茶", 4, "波霸珍珠", 1), _s("🧋 芋泥奶茶", 4, "芋泥波波", 1),
            _s("🧋 杨枝甘露", 5, "芒果西柚", 1), _s("🧋 椰椰芒芒", 4, "椰汁芒果", 1),
            _s("🧋 乌龙奶盖", 4, "乌龙茶+咸奶盖", 1),
        ],
    },
    # ====== 零食/小吃 ======
    "零食铺": {
        "emoji": "🍿", "desc": "追剧必备",
        "items": [
            _s("🍿 焦糖爆米花", 2, "焦糖味", 7), _s("🥜 坚果拼盘", 4, "腰果杏仁核桃", 30),
            _s("🍫 巧克力棒", 3, "夹心巧克力", 90), _s("🍘 仙贝", 2, "旺旺同款", 60),
            _s("🥨 椒盐脆饼", 2, "嘎嘣脆", 30), _s("🧀 芝士条", 3, "拉丝芝士条", 14),
        ],
    },
    "水果摊": {
        "emoji": "🍉", "desc": "新鲜应季水果",
        "items": [
            _s("🍎 苹果", 2, "红富士苹果", 7), _s("🍌 香蕉", 2, "进口香蕉", 3),
            _s("🍊 橘子", 2, "蜜橘", 7), _s("🍇 葡萄", 3, "紫葡萄一串", 5),
            _s("🥝 猕猴桃", 3, "新西兰奇异果", 5), _s("🫐 蓝莓", 4, "一盒蓝莓", 3),
        ],
    },
    # ====== 烤肉/炸物 ======
    "烤肉店": {
        "emoji": "🥩", "desc": "炭火香气大口吃肉",
        "items": [
            _s("🥩 和牛五花", 8, "A5和牛雪花", 1), _s("🍖 秘制猪排", 4, "酱烤猪排", 1),
            _s("🍗 蜜汁鸡翅", 3, "蜜汁烤鸡翅", 1), _s("🌽 烤玉米", 2, "刷酱烤玉米", 1),
            _s("🍢 烤串拼盘", 5, "羊肉+牛肉+鸡心", 1),
        ],
    },
    "炸鸡店": {
        "emoji": "🍗", "desc": "外酥里嫩",
        "items": [
            _s("🍗 原味炸鸡", 4, "黄金脆皮炸鸡", 1), _s("🍗 蜂蜜炸鸡", 5, "甜辣蜂蜜味", 1),
            _s("🍟 薯条", 2, "粗薯条", 1), _s("🥤 可乐", 2, "冰可乐", 30),
            _s("🧀 芝士球", 3, "炸芝士球", 1),
        ],
    },
    # ====== 非食品 ======
    "花店": {
        "emoji": "💐", "desc": "鲜花与美好",
        "items": [
            {"name": "🌹 红玫瑰", "category": "flower", "price": 8, "desc": "一枝鲜红玫瑰", "shelf_life_days": 5},
            {"name": "🌷 郁金香", "category": "flower", "price": 5, "desc": "粉色郁金香", "shelf_life_days": 5},
            {"name": "🌻 向日葵", "category": "flower", "price": 4, "desc": "一枝向日葵", "shelf_life_days": 5},
            {"name": "💐 混合花束", "category": "flower", "price": 10, "desc": "精选混搭", "shelf_life_days": 5},
            {"name": "🪻 薰衣草", "category": "flower", "price": 5, "desc": "干薰衣草束", "shelf_life_days": 30},
        ],
    },
    "文具店": {
        "emoji": "📝", "desc": "学习使我快乐",
        "items": [
            {"name": "🖊️ 中性笔", "category": "item", "price": 1, "desc": "0.5mm黑色中性笔"},
            {"name": "📓 笔记本", "category": "item", "price": 2, "desc": "A5方格笔记本"},
            {"name": "📏 尺子", "category": "item", "price": 1, "desc": "透明直尺"},
            {"name": "🖍️ 彩色马克笔", "category": "item", "price": 3, "desc": "荧光色记号笔"},
            {"name": "📎 文件夹", "category": "item", "price": 2, "desc": "透明文件袋"},
        ],
    },
    "杂货铺": {
        "emoji": "🏬", "desc": "什么都有的小店",
        "items": [
            {"name": "🧻 纸巾", "category": "item", "price": 1, "desc": "一包抽纸"},
            {"name": "🪥 牙刷", "category": "item", "price": 2, "desc": "软毛牙刷"},
            {"name": "🧴 洗手液", "category": "item", "price": 2, "desc": "泡沫洗手液"},
            {"name": "🔋 电池", "category": "item", "price": 2, "desc": "5号电池两节"},
            {"name": "💡 小夜灯", "category": "item", "price": 3, "desc": "暖光小夜灯"},
            {"name": "⭐ 小星星", "category": "decoration", "price": 1, "desc": "亮晶晶的小星星"},
        ],
    },
    "礼品店": {
        "emoji": "🎀", "desc": "送礼佳品",
        "items": [
            {"name": "🧸 小熊玩偶", "category": "decoration", "price": 6, "desc": "毛绒小熊"},
            {"name": "🎀 蝴蝶结发卡", "category": "decoration", "price": 3, "desc": "丝带蝴蝶结"},
            {"name": "🪞 化妆镜", "category": "item", "price": 4, "desc": "便携折叠镜"},
            {"name": "🕯️ 香薰蜡烛", "category": "decoration", "price": 5, "desc": "薰衣草香薰"},
            {"name": "📸 拍立得相纸", "category": "item", "price": 3, "desc": "10张装相纸"},
        ],
    },
    "盲盒店": {
        "emoji": "📦", "desc": "拆盒一时爽",
        "items": [
            {"name": "📦 神秘盲盒A", "category": "item", "price": 5, "desc": "不知道里面有啥"},
            {"name": "📦 神秘盲盒B", "category": "item", "price": 5, "desc": "可能是惊喜"},
            {"name": "📦 豪华盲盒", "category": "item", "price": 10, "desc": "大概率是惊喜"},
            {"name": "📦 迷你盲盒", "category": "item", "price": 2, "desc": "小小的快乐"},
        ],
    },
    "书店": {
        "emoji": "📚", "desc": "精神食粮",
        "items": [
            {"name": "📖 轻小说", "category": "item", "price": 4, "desc": "热门轻小说一本"},
            {"name": "📚 漫画", "category": "item", "price": 3, "desc": "单行本漫画"},
            {"name": "📕 推理小说", "category": "item", "price": 5, "desc": "烧脑推理一本"},
            {"name": "📗 编程书", "category": "item", "price": 6, "desc": "从入门到放弃"},
            {"name": "🔖 书签", "category": "decoration", "price": 1, "desc": "金属镂空书签"},
        ],
    },
    "宠物店": {
        "emoji": "🐾", "desc": "毛孩子的小天地",
        "items": [
            {"name": "🐾 猫粮小包", "category": "item", "price": 3, "desc": "试吃装猫粮"},
            {"name": "🦴 狗咬胶", "category": "item", "price": 2, "desc": "磨牙洁齿"},
            {"name": "🎾 宠物球", "category": "item", "price": 2, "desc": "弹力小球"},
            {"name": "🐟 逗猫棒", "category": "item", "price": 3, "desc": "羽毛逗猫棒"},
            {"name": "🛏️ 宠物垫", "category": "item", "price": 5, "desc": "软绵绵宠物垫"},
        ],
    },
}

# 便利超市商品池
CONVENIENCE_POOL = {
    "all_season": [
        _s("🍎 苹果", 2, "红红的苹果", 7), _s("🥛 牛奶", 2, "一盒纯牛奶", 7),
        _s("🍞 面包", 2, "切片面包", 3), _s("🧃 果汁", 2, "盒装橙汁", 14),
        _s("🍪 饼干", 2, "原味饼干", 60), _s("🥚 鸡蛋", 1, "一颗鸡蛋", 14),
        {"name": "🧻 纸巾", "category": "item", "price": 1, "desc": "一包抽纸"},
        {"name": "🖊️ 圆珠笔", "category": "item", "price": 1, "desc": "蓝色圆珠笔"},
        {"name": "⭐ 小星星", "category": "decoration", "price": 1, "desc": "亮晶晶的小星星"},
    ],
    "spring": [_s("🫖 茉莉花茶", 3, "茉莉花茶包", 90), _s("🥒 黄瓜", 2, "新鲜黄瓜", 5)],
    "summer": [_s("🍉 西瓜", 4, "冰镇大西瓜", 2), _s("🍦 冰淇淋", 3, "香草冰淇淋", 1)],
    "autumn": [_s("🌰 板栗", 3, "糖炒板栗", 7), _s("🍠 烤红薯", 3, "热乎乎烤红薯", 1)],
    "winter": [_s("🥟 饺子", 4, "猪肉白菜馅", 1), _s("☕ 热可可", 3, "暖暖的热巧克力", 1)],
}

COLLECTIBLE_POOL = [
    {"name": "🦆 柯尔鸭", "category": "collectible", "price": 30, "desc": "致敬鸭鸭老师的限定收藏"},
    {"name": "🐱 薛定谔的猫罐头", "category": "collectible", "price": 25, "desc": "打开之前不知道有没有猫"},
    {"name": "🤡 打工人的面具", "category": "collectible", "price": 20, "desc": "今天也是元气满满的一天呢！"},
    {"name": "🐟 失去梦想的咸鱼", "category": "collectible", "price": 18, "desc": "翻个身依然是咸鱼"},
    {"name": "🪲 祖传代码Bug", "category": "collectible", "price": 35, "desc": "千万不要删！"},
    {"name": "🥬 一捆新鲜的韭菜", "category": "collectible", "price": 15, "desc": "你听到了镰刀的破风声"},
    {"name": "🍳 黑漆漆的平底锅", "category": "collectible", "price": 20, "desc": "进可挡子弹退可炒冷饭"},
    {"name": "⌨️ 键仙的遗物", "category": "collectible", "price": 28, "desc": "输入'懂得都懂'造成真实伤害"},
    {"name": "🍋 发光的柠檬", "category": "collectible", "price": 15, "desc": "为什么别人都能抽到SSR"},
    {"name": "🖥️ 禁忌符咒rm -rf /", "category": "collectible", "price": 40, "desc": "威力过于强大的毁灭魔法"},
    {"name": "📺 下次一定硬币", "category": "collectible", "price": 15, "desc": "正面白嫖反面下次"},
    {"name": "☁️ 502护身符", "category": "collectible", "price": 20, "desc": "把所有请求拒之门外"},
    {"name": "🧊 融化的雪糕刺客", "category": "collectible", "price": 30, "desc": "结账时才发动致命一击"},
]

HOLIDAY_ITEMS = {
    "元旦": [_s("🎆 新年烟花糖", 3, "噼里啪啦跳跳糖", 30)],
    "情人节": [_s("💘 心形巧克力", 5, "粉色心形巧克力", 30),
               {"name": "🌹 玫瑰花束", "category": "flower", "price": 12, "desc": "情人节限定大花束", "shelf_life_days": 5}],
    "儿童节": [_s("🍭 超大棒棒糖", 2, "彩虹色大棒棒糖", 60)],
    "万圣节": [{"name": "🎃 南瓜灯", "category": "decoration", "price": 5, "desc": "笑嘻嘻的南瓜灯"},
               _s("👻 幽灵糖果", 3, "白色幽灵形软糖", 30)],
    "圣诞节": [{"name": "🎄 迷你圣诞树", "category": "decoration", "price": 6, "desc": "桌上摆的小圣诞树"},
               _s("🎅 圣诞袜糖果", 3, "红袜子里装满了糖", 30)],
}

# 每日显示的店铺数（不含固定的便利超市）
DAILY_SHOP_COUNT = 7


class ShopManager:
    """
    多店铺购物街
    - 便利超市：固定，每日刷新商品（季节+收藏品）
    - 主题店铺：30家池子，每日随机开 7 家
    - AI动态店铺：用户想逛没有的店 → LLM 生成，当日缓存
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
                for k in ("date", "items", "purchase_log", "owned_collectibles", "ai_shops"):
                    data.setdefault(k, "" if k == "date" else [] if k in ("items", "purchase_log") else {})
                return data
        except (json.JSONDecodeError, TypeError):
            return {"date": "", "items": [], "purchase_log": [],
                    "owned_collectibles": {}, "ai_shops": {}}

    def _save_data(self):
        path = os.path.join(self.data_dir, "shop.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ========== 收藏品 ==========

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

    # ========== 每日店铺选择 ==========

    def _get_today_shops(self) -> List[str]:
        """每天用日期做种子随机选 N 家主题店"""
        today = datetime.now().strftime("%Y-%m-%d")
        seed = int(today.replace("-", ""))
        rng = random.Random(seed)
        all_names = list(THEMED_SHOPS.keys())
        count = min(DAILY_SHOP_COUNT, len(all_names))
        return rng.sample(all_names, count)

    def get_all_shop_names(self) -> List[Dict]:
        """获取今日所有可逛的店铺"""
        shops = [{"name": "便利超市", "emoji": "🏪", "desc": "日常用品·应季商品·稀有收藏"}]
        for name in self._get_today_shops():
            info = THEMED_SHOPS[name]
            shops.append({"name": name, "emoji": info["emoji"], "desc": info["desc"]})
        # AI生成的店铺
        today = datetime.now().strftime("%Y-%m-%d")
        for name, info in self.data.get("ai_shops", {}).get(today, {}).items():
            shops.append({"name": name, "emoji": info.get("emoji", "🏬"), "desc": info.get("desc", "")})
        return shops

    def format_shop_list(self) -> str:
        shops = self.get_all_shop_names()
        holiday = get_holiday()
        header = "🛍️ 今日购物街"
        if holiday:
            header += f" · 🎉{holiday}"
        lines = [header + "\n"]
        for s in shops:
            lines.append(f"  {s['emoji']} {s['name']}  {s['desc']}")
        lines.append(f"\n💡 逛店铺：逛 <店名>")
        lines.append(f"💡 直接买：购买 <商品名>")
        lines.append(f"💡 想逛别的店？直接说，没有的会现开一家")
        return "\n".join(lines)

    # ========== 便利超市 ==========

    def needs_refresh(self) -> bool:
        return self.data.get("date") != datetime.now().strftime("%Y-%m-%d")

    def refresh_convenience(self):
        today = datetime.now().strftime("%Y-%m-%d")
        season = get_season()
        pool = list(self.item_pool.get("all_season", []))
        pool += self.item_pool.get(season, [])

        count = min(self.daily_item_count, len(pool))
        selected = random.sample(pool, count)

        holiday = get_holiday()
        if holiday and holiday in HOLIDAY_ITEMS:
            for hi in HOLIDAY_ITEMS[holiday]:
                if selected:
                    selected[random.randint(0, len(selected) - 1)] = hi

        if COLLECTIBLE_POOL and random.random() < 0.02:
            selected[random.randint(0, len(selected) - 1)] = random.choice(COLLECTIBLE_POOL)

        shop_items = []
        for i, item in enumerate(selected, 1):
            si = {"id": i, "name": item.get("name", "?"), "category": item.get("category", "item"),
                  "price": item.get("price", 1), "desc": item.get("desc", ""),
                  "stock": random.randint(1, 5)}
            if item.get("shelf_life_days"):
                si["shelf_life_days"] = item["shelf_life_days"]
            shop_items.append(si)

        self.data["date"] = today
        self.data["items"] = shop_items
        self.data["ai_shops"] = {today: self.data.get("ai_shops", {}).get(today, {})}
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.data["purchase_log"] = [l for l in self.data.get("purchase_log", []) if l.get("time", "") >= cutoff]
        self._save_data()

    def refresh_with_ai_items(self, ai_items: List[Dict]):
        today = datetime.now().strftime("%Y-%m-%d")
        selected = list(ai_items)
        holiday = get_holiday()
        if holiday and holiday in HOLIDAY_ITEMS:
            for hi in HOLIDAY_ITEMS[holiday]:
                if selected:
                    selected[random.randint(0, len(selected) - 1)] = hi
        if COLLECTIBLE_POOL and random.random() < 0.02:
            selected[random.randint(0, len(selected) - 1)] = random.choice(COLLECTIBLE_POOL)
        shop_items = []
        for i, item in enumerate(selected, 1):
            si = {"id": i, "name": item.get("name", "?"), "category": item.get("category", "item"),
                  "price": item.get("price", 1), "desc": item.get("desc", ""),
                  "stock": random.randint(1, 5)}
            if item.get("shelf_life_days"):
                si["shelf_life_days"] = item["shelf_life_days"]
            shop_items.append(si)
        self.data["date"] = today
        self.data["items"] = shop_items
        self._save_data()

    # ========== 浏览店铺 ==========

    def browse_shop(self, shop_name: str, user_id: str = "") -> Optional[str]:
        owned = self.get_owned_collectibles(user_id) if user_id else []

        # 便利超市
        if shop_name in ("便利超市", "超市", "便利店"):
            if self.needs_refresh():
                self.refresh_convenience()
            items = [i for i in self.data["items"] if i.get("stock", 0) > 0]
            if not items:
                return "🏪 便利超市今日已售罄~"
            lines = ["🏪 便利超市\n"]
            for item in items:
                tag = ""
                if item["category"] == "collectible":
                    tag = " ✅已拥有" if item["name"] in owned else " 🌟稀有!"
                lines.append(f"  [{item['id']}] {item['name']} - {item['price']}元 | 库存{item['stock']}{tag}")
                lines.append(f"      {item['desc']}")
            lines.append(f"\n💡 购买 <编号> 或 购买 <商品名>")
            return "\n".join(lines)

        # 今日开放的主题店
        today_shops = self._get_today_shops()
        for sn in today_shops:
            if shop_name in (sn, _strip_emoji(sn)):
                info = THEMED_SHOPS[sn]
                return self._format_themed_shop(sn, info)

        # 不在今日列表但在总池子里 → 也可以逛
        for sn, info in THEMED_SHOPS.items():
            if shop_name in (sn, _strip_emoji(sn)):
                return self._format_themed_shop(sn, info)

        # AI 店铺缓存
        today = datetime.now().strftime("%Y-%m-%d")
        ai_shops = self.data.get("ai_shops", {}).get(today, {})
        if shop_name in ai_shops:
            return self._format_themed_shop(shop_name, ai_shops[shop_name])

        return None

    def _format_themed_shop(self, name: str, info: Dict) -> str:
        items = info.get("items", [])
        emoji = info.get("emoji", "🏬")
        desc = info.get("desc", "")
        lines = [f"{emoji} {name} — {desc}\n"]
        for item in items:
            shelf = f" | {item.get('shelf_life_days', '')}天" if item.get("shelf_life_days") else ""
            lines.append(f"  🍽️ {item['name']} - {item['price']}元{shelf}")
            lines.append(f"      {item.get('desc', '')}")
        lines.append(f"\n💡 购买 <商品名>")
        return "\n".join(lines)

    def save_ai_shop(self, shop_name: str, shop_data: Dict):
        today = datetime.now().strftime("%Y-%m-%d")
        ai_shops = self.data.setdefault("ai_shops", {})
        day_shops = ai_shops.setdefault(today, {})
        day_shops[shop_name] = shop_data
        self._save_data()
        logger.info(f"[Shop] AI店铺已保存：{shop_name}")

    # ========== 跨店购买 ==========

    def find_item_across_shops(self, item_name: str) -> Optional[Tuple[Dict, str]]:
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

        # 所有主题店（不限今日开放的）
        for shop_name, info in THEMED_SHOPS.items():
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
        result = self.find_item_across_shops(item_name)
        if not result:
            return None
        item, shop_name = result

        if item.get("category") == "collectible":
            if self.has_collectible(buyer_id, item["name"]):
                return {"error": "already_owned", "name": item["name"]}

        if shop_name == "便利超市":
            for si in self.data["items"]:
                if si["name"] == item["name"] and si.get("stock", 0) > 0:
                    si["stock"] -= 1
                    break

        purchased = {"name": item["name"], "category": item.get("category", "food"),
                     "price": item["price"], "desc": item.get("desc", ""), "shop": shop_name}
        if item.get("shelf_life_days"):
            purchased["expires_at"] = (datetime.now() + timedelta(days=item["shelf_life_days"])).strftime("%Y-%m-%d %H:%M:%S")
            purchased["shelf_life_days"] = item["shelf_life_days"]
        if item.get("category") == "collectible":
            self._record_collectible(buyer_id, item["name"])

        self.data["purchase_log"].append({
            "buyer": buyer_id, "item": item["name"], "price": item["price"],
            "shop": shop_name, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        self._save_data()
        return purchased

    def buy_item(self, item_id: int, buyer_id: str) -> Optional[Dict]:
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
        return self.format_shop_list()

    # ========== AI Prompt ==========

    @staticmethod
    def build_ai_shop_prompt(shop_name: str) -> str:
        return (
            f"你是一个虚拟购物街的店长，要开一家「{shop_name}」。\n"
            f"请生成6-8个符合主题的商品：\n"
            f"- emoji+名称，价格1-10元\n"
            f"- 食品带shelf_life_days(1-90)\n"
            f"- 描述简短一句话\n"
            f"- category填food/item/decoration\n\n"
            f"给店取一个emoji和一句短描述。\n"
            f'只输出JSON：{{"emoji":"🍰","desc":"描述","items":[{{"name":"🍰蛋糕","category":"food","price":6,"desc":"描述","shelf_life_days":2}}]}}'
        )

    @staticmethod
    def build_ai_prompt() -> str:
        season = get_season()
        season_cn = {"spring": "春天", "summer": "夏天", "autumn": "秋天", "winter": "冬天"}
        forbidden = "、".join(_FORBIDDEN_EMOJIS)
        return (
            f"你是虚拟超市进货员。现在是{season_cn[season]}。\n"
            f"生成10个日常超市商品：7-8个食品(food)+1-2个鲜花(flower)+1个日用品(item)。\n"
            f"emoji+朴素名称，价格1-8元，食品带shelf_life_days。\n"
            f"禁用emoji：{forbidden}。禁止collectible。\n只输出JSON数组。"
        )
