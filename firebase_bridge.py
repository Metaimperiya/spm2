"""Bridge CPM2 car submissions and approved listings to the website Firebase."""
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

import firebase_admin
from firebase_admin import credentials, db, storage

SITE = "www_metaimperiya_com"
_APP = None


def initialize():
    global _APP
    if _APP:
        return True
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    database_url = os.getenv("FIREBASE_DATABASE_URL", "https://myecosystem-e6414-default-rtdb.firebaseio.com").strip()
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "myecosystem-e6414.firebasestorage.app").strip()
    if not raw:
        return False
    try:
        service_account = json.loads(raw)
        _APP = firebase_admin.initialize_app(
            credentials.Certificate(service_account),
            {"databaseURL": database_url, "storageBucket": bucket_name},
            name="metaimperiya-telegram-bridge",
        )
        return True
    except ValueError:
        # Firebase Admin can already be initialized when a development worker reloads.
        try:
            _APP = firebase_admin.get_app("metaimperiya-telegram-bridge")
            return True
        except ValueError:
            raise


def _ref(path):
    if not initialize():
        raise RuntimeError("Firebase bridge is not configured")
    return db.reference(f"sites/{SITE}/{path}", app=_APP)


def consume_link_code(code, telegram_id, username, first_name):
    code_ref = _ref(f"telegram_link_codes/{code}")
    payload = code_ref.get()
    if not payload or not payload.get("uid") or int(payload.get("expiresAt", 0)) <= int(datetime.now(timezone.utc).timestamp() * 1000):
        return None
    uid = str(payload["uid"])
    current_telegram_link = _ref(f"telegram_user_links/{telegram_id}").get()
    current_site_link = _ref(f"telegram_links/{uid}").get()
    if current_telegram_link and current_telegram_link.get("uid") != uid:
        raise RuntimeError("Этот Telegram уже связан с другим аккаунтом сайта")
    if current_site_link and str(current_site_link.get("telegramId")) != str(telegram_id):
        raise RuntimeError("Этот аккаунт сайта уже связан с другим Telegram")
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    handle = (username or "").lstrip("@")[:64]
    mapping = {"uid": uid, "telegramId": str(telegram_id), "username": handle, "firstName": (first_name or "")[:80], "linkedAt": now}
    # Update both directions and consume the one-time code in a single RTDB multi-location write.
    db.reference(f"sites/{SITE}", app=_APP).update({
        f"telegram_user_links/{telegram_id}": mapping,
        f"telegram_links/{uid}": mapping,
        f"telegram_link_codes/{code}": None,
    })
    return uid


def get_linked_uid(telegram_id):
    value = _ref(f"telegram_user_links/{telegram_id}").get()
    return str(value["uid"]) if value and value.get("uid") else None


def unlink_telegram_account(telegram_id):
    mapping = _ref(f"telegram_user_links/{telegram_id}").get()
    if not mapping or not mapping.get("uid"):
        return False
    uid = str(mapping["uid"])
    db.reference(f"sites/{SITE}", app=_APP).update({
        f"telegram_user_links/{telegram_id}": None,
        f"telegram_links/{uid}": None,
    })
    return True


def set_newsletter_subscription(telegram_id, username, first_name, enabled):
    """Persist explicit Telegram DM consent in the existing Firebase RTDB."""
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    _ref(f"telegram_newsletter_subscribers/{telegram_id}").set({
        "telegramId": str(telegram_id),
        "username": (username or "")[:64],
        "firstName": (first_name or "")[:80],
        "enabled": bool(enabled),
        "updatedAt": now,
    })
    return bool(enabled)


def is_newsletter_subscriber(telegram_id):
    value = _ref(f"telegram_newsletter_subscribers/{telegram_id}").get()
    return bool(value and value.get("enabled") is True)


def get_newsletter_subscribers():
    values = _ref("telegram_newsletter_subscribers").get() or {}
    subscribers = []
    for key, value in values.items():
        if isinstance(value, dict) and value.get("enabled") is True:
            try:
                subscribers.append(int(value.get("telegramId") or key))
            except (TypeError, ValueError):
                continue
    return subscribers


def upload_photo(uid, submission_id, photo_bytes, content_type="image/jpeg"):
    if not initialize():
        raise RuntimeError("Firebase bridge is not configured")
    token = str(uuid.uuid4())
    blob = storage.bucket(app=_APP).blob(f"cpm2-garage-photos/{uid}/{submission_id}/main")
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(photo_bytes, content_type=content_type)
    bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "myecosystem-e6414.firebasestorage.app").strip()
    return f"https://firebasestorage.googleapis.com/v0/b/{quote(bucket, safe='')}/o/{quote(blob.name, safe='')}?alt=media&token={token}"


def create_garage_submission(telegram_id, title, description, price, game_id, contact, photo_bytes,
                             country, country_code, city, deal_mode, trade_for, seller_name):
    uid = get_linked_uid(telegram_id)
    if not uid:
        raise RuntimeError("Сначала привяжи аккаунт сайта командой /link КОД")
    ref = _ref(f"cpm2_garage_submissions/{uid}").push()
    image_url = upload_photo(uid, ref.key, photo_bytes)
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    item = {
        "sellerUid": uid, "sellerName": (seller_name or "Игрок")[:80], "gameId": game_id[:80],
        "title": title[:80], "description": description[:1000], "imageUrl": image_url,
        "price": int(price), "creditAmount": int(price), "dealMode": "trade" if deal_mode == "trade" else "sell",
        "tradeFor": trade_for[:160], "country": country[:80], "countryCode": country_code[:2].upper(),
        "city": city[:80], "status": "pending", "createdAt": now,
        "source": "telegram", "telegramId": str(telegram_id), "telegramContact": contact[:120],
    }
    ref.set(item)
    return uid, ref.key


def pending_telegram_listings(limit=50):
    query = _ref("marketplace_listings").order_by_child("telegramSync").equal_to(True).limit_to_last(limit)
    values = query.get() or {}
    return [(key, value) for key, value in values.items()
            if isinstance(value, dict) and value.get("isActive") is True
            and value.get("cpm2Broker") is True and value.get("moderationStatus") == "approved"
            and value.get("telegramSyncState") != "posted"]


def get_approved_site_car_listings(limit=50):
    """Return active, approved CPM2 car listings from the website catalog."""
    values = _ref("marketplace_listings").order_by_child("createdAt").limit_to_last(limit).get() or {}
    listings = []
    for listing_id, value in values.items():
        if not isinstance(value, dict):
            continue
        if (value.get("cpm2Broker") is True and value.get("moderationStatus") == "approved"
                and value.get("isActive") is True and value.get("brokerStatus") == "in_stock"):
            listings.append({"id": listing_id, **value})
    return sorted(listings, key=lambda item: item.get("createdAt", 0), reverse=True)


def mark_listing_posted(listing_id, channel, message_id):
    _ref(f"marketplace_listings/{listing_id}").update({
        "telegramSyncState": "posted", "telegramPostedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
        "telegramChannel": str(channel), "telegramMessageId": int(message_id),
    })
