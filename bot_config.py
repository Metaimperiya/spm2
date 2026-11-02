"""Shared bot configuration imported by handlers without importing bot.py."""

ADMIN_IDS = [806159173, 5493746865]

MAIN_CLAN_CHANNEL = "@cpm_2_clan"
SALE_CHANNEL = "@cpm_2_sale"
TRADE_CHANNEL = "@cpm_2_trade"
SELL_ACC_CHANNEL = "@Sell_CPM_2_accounts"
PODSLUSHKA_CHANNEL = "@podslushkacpm2"


def is_admin(user_or_id):
    user_id = getattr(user_or_id, "id", user_or_id)
    return user_id in ADMIN_IDS
