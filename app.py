from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import random
import string
import hashlib
import time
import json
import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# CORS ayarları - sadece belirli domainlere izin ver
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Production'da spesifik domain belirtin
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate Limiting - DDoS koruması
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Loglama ayarları
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/api.log', maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Şifreleme anahtarı - production'da environment variable'dan alın
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# API Gizli Anahtarı
SECRET_KEY = os.environ.get('SECRET_KEY', 'play_kod_super_gizli_2024')

# Kullanılan kodları takip et - tekrar kullanımı engelle
used_codes = set()
MAX_USED_CODES = 10000

def encrypt_data(data):
    """Veriyi şifrele"""
    try:
        if isinstance(data, dict):
            data = json.dumps(data)
        encrypted = cipher_suite.encrypt(data.encode())
        return encrypted.decode()
    except:
        return None

def decrypt_data(encrypted_data):
    """Veriyi çöz"""
    try:
        decrypted = cipher_suite.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())
    except:
        return None

def generate_signature(data):
    """İstek için imza oluştur"""
    timestamp = str(int(time.time() / 60))  # Dakika bazlı timestamp
    raw = f"{SECRET_KEY}{data}{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def verify_request(f):
    """İstek doğrulama dekoratörü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            # Content-Type kontrolü
            if not request.is_json:
                logger.warning("Geçersiz Content-Type")
                return jsonify({"sonuc": "GECERSIZ-ISTEK"})
            
            # İmza kontrolü (opsiyonel)
            client_signature = request.headers.get('X-Signature', '')
            if client_signature:
                raw_data = request.get_data()
                expected_signature = generate_signature(raw_data.decode())
                if client_signature != expected_signature:
                    logger.warning("Geçersiz imza")
                    return jsonify({"sonuc": "IMZA-HATASI"})
        
        return f(*args, **kwargs)
    return decorated_function

def generate_play_code(pattern='standard'):
    """Gelişmiş Play kod üretici"""
    if pattern == 'standard':
        chars = string.ascii_uppercase + string.digits
        groups = [''.join(random.sample(chars, 4)) for _ in range(4)]
        return '-'.join(groups)
    
    elif pattern == 'numeric':
        groups = [str(random.randint(1000, 9999)) for _ in range(4)]
        return '-'.join(groups)
    
    elif pattern == 'secure':
        # Daha güvenli karakter setleri
        upper = random.sample(string.ascii_uppercase, 8)
        digits = random.sample(string.digits, 4)
        special = random.sample('@#$%&*', 4)
        all_chars = upper + digits + special
        random.shuffle(all_chars)
        return '-' .join([''.join(all_chars[i:i+4]) for i in range(0, 16, 4)])

def calculate_checksum(code):
    """Kod için checksum hesapla"""
    clean_code = code.replace('-', '')
    checksum = sum(ord(c) for c in clean_code) % 100
    return f"{checksum:02d}"

def get_code_expiry():
    """Kod son kullanma tarihi"""
    expiry_days = random.choice([30, 60, 90, 180, 365])
    expiry_date = datetime.now() + timedelta(days=expiry_days)
    return expiry_date.strftime("%Y-%m-%d")

@app.route('/api/playkod', methods=['POST'])
@limiter.limit("30 per minute")
@verify_request
def create_play_code():
    """
    Gelişmiş Play Kod API'si
    Tamamen gizli parametreler ve iç işleyiş
    """
    try:
        # Gelen veriyi al ve doğrula
        data = request.get_json()
        
        if not data:
            logger.warning("Boş istek gövdesi")
            return jsonify({"sonuc": None})
        
        # Gizli parametre işleme
        raw_input = data.get('v', data.get('value', ''))
        
        # Input validasyonu - görünmez
        try:
            if isinstance(raw_input, dict):
                # Şifreli veri geldiyse çöz
                decrypted = decrypt_data(raw_input.get('d', ''))
                if decrypted:
                    value = str(decrypted.get('amount', 25))
                else:
                    value = str(raw_input.get('amount', 25))
            else:
                value = str(raw_input)
        except:
            value = None
        
        # Miktar kontrolü ve varsayılan atama
        valid_amounts = [10, 25, 50, 100, 200, 500]
        try:
            amount = int(value)
            if amount not in valid_amounts:
                amount = random.choice([25, 50, 100])
        except:
            amount = random.choice([25, 50, 100])
        
        # Pattern seçimi
        pattern = data.get('type', random.choice(['standard', 'numeric', 'secure']))
        
        # Benzersiz kod üret
        attempts = 0
        while attempts < 10:
            code = generate_play_code(pattern)
            if code not in used_codes:
                break
            attempts += 1
        
        # Kullanılan kodları yönet
        if len(used_codes) > MAX_USED_CODES:
            used_codes.clear()
        used_codes.add(code)
        
        # Metadata oluştur
        checksum = calculate_checksum(code)
        expiry = get_code_expiry()
        
        # İstek loglaması
        logger.info(f"Kod üretildi - Pattern: {pattern}, Amount: {amount}")
        
        # Yanıt hazırla - sadece gerekli alanlar
        response_data = {
            "k": code,  # Sadeleştirilmiş anahtar ismi
            "c": checksum,  # Checksum
            "e": expiry  # Son kullanma
        }
        
        # İsteğe bağlı: yanıtı şifrele
        if data.get('encrypted', False):
            response_data = {"d": encrypt_data(response_data)}
        
        logger.info(f"Başarılı yanıt: {len(str(response_data))} bytes")
        
        return jsonify({"sonuc": response_data})
        
    except Exception as e:
        logger.error(f"İşlem hatası: {str(e)}")
        return jsonify({"sonuc": None})

@app.route('/api/status', methods=['GET'])
@limiter.limit("5 per minute")
def api_status():
    """API durum kontrolü - sınırlı bilgi"""
    return jsonify({
        "s": int(time.time()),
        "v": "3.0"
    })

@app.route('/')
def index():
    """Ana sayfa - boş"""
    return "", 204

@app.before_request
def before_request():
    """Her istek öncesi çalışır"""
    # User-Agent kontrolü
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent:
        logger.warning("User-Agent yok - potansiyel bot")
    
    # İstek IP'sini logla
    logger.debug(f"İstek: {request.remote_addr} - {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Her istek sonrası çalışır"""
    # Güvenlik başlıkları ekle
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Sunucu bilgisini gizle
    response.headers['Server'] = 'Unknown'
    
    return response

# Hata yakalama
@app.errorhandler(404)
def not_found(e):
    return "", 404

@app.errorhandler(405)
def method_not_allowed(e):
    return "", 405

@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify({"sonuc": None})

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Sunucu hatası: {str(e)}")
    return "", 500

if __name__ == "__main__":
    # Production'da debug=False ve gunicorn gibi WSGI server kullanın
    port = int(os.environ.get('PORT', 7000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"API başlatılıyor - Port: {port}, Debug: {debug}")
    
    try:
        app.run(
            host="0.0.0.0",
            port=port,
            debug=debug,
            ssl_context='adhoc' if not debug else None  # Production'da SSL
        )
    except Exception as e:
        logger.critical(f"Başlatma hatası: {str(e)}")
