import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime

from astrbot.api import logger


# 成就定义：(id, 名称, 描述, 条件类型, 阈值, 经验奖励)
ACHIEVEMENTS = [
    # 余额成就
    ("rich_1", "💰 小有积蓄", "余额达到 100 元", "balance", 100, 30),
    ("rich_2", "💰 小康之家", "余额达到 500 元", "balance", 500, 60),
    ("rich_3", "💰 万元户", "余额达到 10000 元", "balance", 10000, 150),
    ("rich_4", "💰 富甲一方", "余额达到 50000 元", "balance", 50000, 300),
    ("rich_5", "💰 财富自由", "余额达到 100000 元", "balance", 100000, 500),
    # 等级成就
    ("level_1", "⭐ 初出茅庐", "达到 Lv.1", "level", 1, 20),
    ("level_5", "⭐ 小有所成", "达到 Lv.5", "level", 5, 80),
    ("level_10", "⭐ 身经百战", "达到 Lv.10", "level", 10, 200),
    ("level_15", "⭐ 炉火纯青", "达到 Lv.15", "level", 15, 400),
    ("level_20", "⭐ 登峰造极", "达到 Lv.20", "level", 20, 800),
    # 签到成就
    ("sign_7", "📅 一周坚持", "连续签到 7 天", "sign_streak", 7, 50),
    ("sign_30", "📅 月度之星", "连续签到 30 天", "sign_streak", 30, 200),
    ("sign_100", "📅 签到达人", "累计签到 100 次", "sign_total", 100, 300),
    # 交易成就
    ("trade_10", "🛒 购物新手", "累计购买 10 次", "purchase_count", 10, 40),
    ("trade_50", "🛒 购物达人", "累计购买 50 次", "purchase_count", 50, 100),
    ("scratch_10", "🎰 手气不错", "刮刮乐玩 10 次", "scratch_count", 10, 40),
    ("scratch_50", "🎰 刮刮乐之王", "刮刮乐玩 50 次", "scratch_count", 50, 100),
    ("stock_profit", "📈 股神", "炒股累计盈利 1000 元", "stock_profit", 1000, 200),
    # 银行成就
    ("bank_1", "🏦 储蓄新手", "首次银行存款", "bank_deposit_count", 1, 30),
    ("bank_interest", "🏦 利息猎人", "累计获得利息 100 元", "bank_interest", 100, 100),
    # 收藏成就
    ("collector_1", "🏅 收藏家", "拥有 1 件收藏品", "collectible_count", 1, 50),
    ("collector_5", "🏅 博物馆馆长", "拥有 5 件收藏品", "collectible_count", 5, 150),
    # ====== 新增成就 ======
    # 老虎机
    ("slots_10", "🎰 拉霸新手", "老虎机玩 10 次", "slots_count", 10, 40),
    ("slots_50", "🎰 拉霸高手", "老虎机玩 50 次", "slots_count", 50, 100),
    ("slots_jackpot", "🎰 头奖得主", "老虎机命中一次头奖", "slots_jackpots", 1, 200),
    # 21点
    ("bj_10", "🃏 牌桌新秀", "21点玩 10 局", "bj_count", 10, 40),
    ("bj_50", "🃏 赌场常客", "21点玩 50 局", "bj_count", 50, 100),
    ("bj_win10", "🃏 胜率之星", "21点赢 10 局", "bj_wins", 10, 80),
    ("bj_blackjack", "🃏 天选之人", "21点打出 Blackjack", "bj_blackjacks", 1, 150),
    # 猜大小
    ("dice_10", "🎲 骰子爱好者", "猜大小玩 10 次", "dice_count", 10, 40),
    ("dice_streak3", "🎲 三连胜", "猜大小连赢 3 次", "dice_streak", 3, 80),
    # 塔罗
    ("tarot_1", "🔮 初次问卦", "第一次塔罗占卜", "tarot_count", 1, 20),
    ("tarot_10", "🔮 命运探索者", "塔罗占卜 10 次", "tarot_count", 10, 60),
    ("tarot_daily7", "🌅 晨运达人", "累计看 7 次今日运势", "tarot_daily_count", 7, 50),
    # 社交
    ("praise_5", "💌 人缘不错", "收到 5 封表扬信", "praise_received", 5, 60),
    ("praise_20", "💌 万人迷", "收到 20 封表扬信", "praise_received", 20, 150),
    ("praise_send5", "💌 正能量使者", "发出 5 封表扬信", "praise_sent", 5, 40),
    # 综合
    ("game_all", "🎮 全能玩家", "玩过所有小游戏", "games_played_types", 5, 200),
    ("big_win", "🤑 暴发户", "单次赢得 500 元以上", "biggest_win", 500, 250),
    ("broke", "😅 身无分文", "余额降到 0 元", "been_broke", 1, 30),
]


class AchievementManager:
    """
    成就系统
    - 达到特定条件自动解锁
    - 解锁时可给奖励经验
    """

    UNLOCK_XP_REWARD = 50  # 每解锁一个成就奖励的经验

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, "achievements.json")
        if not os.path.exists(path):
            return {"users": {}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("users", {})
                return data
        except (json.JSONDecodeError, TypeError):
            return {"users": {}}

    def _save_data(self):
        path = os.path.join(self.data_dir, "achievements.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _get_user_achievements(self, user_id: str) -> Dict:
        users = self.data.setdefault("users", {})
        if user_id not in users:
            users[user_id] = {"unlocked": {}, "counters": {}}
        return users[user_id]

    def is_unlocked(self, user_id: str, achievement_id: str) -> bool:
        user = self._get_user_achievements(user_id)
        return achievement_id in user.get("unlocked", {})

    def increment_counter(self, user_id: str, counter_name: str, amount: float = 1) -> None:
        """增加计数器值（用于追踪购买次数、盈利等）"""
        user = self._get_user_achievements(user_id)
        counters = user.setdefault("counters", {})
        counters[counter_name] = counters.get(counter_name, 0) + amount
        self._save_data()

    def get_counter(self, user_id: str, counter_name: str) -> float:
        user = self._get_user_achievements(user_id)
        return user.get("counters", {}).get(counter_name, 0)

    def check_and_unlock(self, user_id: str, **stats) -> List[Tuple[str, str, int]]:
        """
        检查并解锁成就
        :param stats: 当前状态值字典，如 balance=1000, level=5, sign_streak=7 等
        :return: 新解锁的成就列表 [(名称, 描述, 经验奖励), ...]
        """
        user = self._get_user_achievements(user_id)
        counters = user.get("counters", {})

        # 合并 counters 到 stats（counters 优先级低于传入的 stats）
        merged = {**counters, **stats}

        newly_unlocked = []
        for ach_tuple in ACHIEVEMENTS:
            # 兼容新旧格式（6元素含XP / 5元素不含）
            if len(ach_tuple) == 6:
                aid, name, desc, condition, threshold, xp_reward = ach_tuple
            else:
                aid, name, desc, condition, threshold = ach_tuple
                xp_reward = self.UNLOCK_XP_REWARD

            if aid in user.get("unlocked", {}):
                continue
            value = merged.get(condition, 0)
            if value >= threshold:
                user.setdefault("unlocked", {})[aid] = {
                    "name": name,
                    "desc": desc,
                    "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                newly_unlocked.append((name, desc, xp_reward))
                logger.info(f"[Achievement] 用户 {user_id} 解锁成就: {name} (+{xp_reward}XP)")

        if newly_unlocked:
            self._save_data()

        return newly_unlocked

    def get_unlocked_list(self, user_id: str) -> List[Dict]:
        user = self._get_user_achievements(user_id)
        return list(user.get("unlocked", {}).values())

    def format_achievements(self, user_id: str) -> str:
        unlocked = self.get_unlocked_list(user_id)
        total = len(ACHIEVEMENTS)

        if not unlocked:
            return f"🏆 成就（0/{total}）：还没有解锁任何成就，继续加油！"

        lines = [f"🏆 成就（{len(unlocked)}/{total}）：\n"]
        for ach in unlocked:
            lines.append(f"  {ach['name']} - {ach['desc']}")
            lines.append(f"    📅 {ach['unlocked_at'][:10]}")

        # 显示未解锁的下一个目标
        user = self._get_user_achievements(user_id)
        locked = [
            (name, desc) for aid, name, desc, _, _ in ACHIEVEMENTS
            if aid not in user.get("unlocked", {})
        ]
        if locked:
            next_name, next_desc = locked[0]
            lines.append(f"\n🔜 下一个目标：{next_name} - {next_desc}")

        return "\n".join(lines)
