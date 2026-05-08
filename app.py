from flask import Flask, render_template_string, jsonify, request
import random
import string

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Play Kod Üretici</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: #16213e;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #64dd17;
            text-align: center;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #888;
            text-align: center;
            font-size: 12px;
            margin-bottom: 25px;
        }
        .amount-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 20px;
        }
        .amount-btn {
            padding: 10px;
            border: 2px solid #1a508b;
            background: transparent;
            color: #aaa;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .amount-btn:hover, .amount-btn.active {
            background: #1a508b;
            color: #64dd17;
            border-color: #64dd17;
        }
        .generate-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #00c853, #64dd17);
            color: #1a1a2e;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,200,83,0.4);
        }
        .result-box {
            background: #0f3460;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #1a508b;
            margin-bottom: 15px;
        }
        .result-label {
            color: #64dd17;
            font-size: 11px;
            margin-bottom: 10px;
            text-align: center;
        }
        .result-code {
            color: white;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            font-family: 'Courier New', monospace;
            letter-spacing: 3px;
        }
        .result-json {
            background: #000;
            color: #64dd17;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin-top: 15px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .copy-btn {
            width: 100%;
            padding: 12px;
            background: transparent;
            border: 2px solid #1a508b;
            color: #64dd17;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #1a508b;
        }
        .toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #00c853;
            color: #1a1a2e;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            opacity: 0;
            transition: all 0.3s;
            z-index: 1000;
        }
        .toast.show {
            opacity: 1;
            top: 30px;
        }
    </style>
</head>
<body>
    <div id="toast" class="toast">✅ Kopyalandı!</div>
    
    <div class="container">
        <h1>🎮 Play Kod</h1>
        <p class="subtitle">HEDİYE KODU ÜRETİCİ</p>
        
        <div class="amount-buttons">
            <button class="amount-btn" onclick="selectAmount(10, this)">10 TL</button>
            <button class="amount-btn active" onclick="selectAmount(25, this)">25 TL</button>
            <button class="amount-btn" onclick="selectAmount(50, this)">50 TL</button>
            <button class="amount-btn" onclick="selectAmount(100, this)">100 TL</button>
        </div>
        
        <button class="generate-btn" onclick="generateCode()">
            🎲 KOD ÜRET
        </button>
        
        <div class="result-box" id="resultBox">
            <div class="result-label">SONUÇ</div>
            <div class="result-code" id="codeDisplay">----</div>
            <div class="result-json" id="jsonDisplay"></div>
        </div>
        
        <button class="copy-btn" onclick="copyCode()">📋 KOPYALA</button>
    </div>

    <script>
        let selectedAmount = 25;
        let currentCode = '';
        let currentJson = '';

        function selectAmount(amount, element) {
            selectedAmount = amount;
            document.querySelectorAll('.amount-btn').forEach(btn => btn.classList.remove('active'));
            element.classList.add('active');
        }

        async function generateCode() {
            try {
                const response = await fetch(`/api/playkod?miktar=${selectedAmount}`);
                const data = await response.json();
                
                currentCode = data.kod;
                currentJson = JSON.stringify(data, null, 2);
                
                document.getElementById('codeDisplay').textContent = currentCode;
                document.getElementById('jsonDisplay').textContent = currentJson;
                
            } catch (error) {
                document.getElementById('codeDisplay').textContent = 'HATA';
                document.getElementById('jsonDisplay').textContent = 'Bir hata oluştu';
            }
        }

        function copyCode() {
            if (!currentCode) {
                alert('Önce kod üretin!');
                return;
            }
            
            navigator.clipboard.writeText(currentCode).then(() => {
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2000);
            });
        }

        // Sayfa yüklendiğinde otomatik kod üret
        window.onload = generateCode;
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/playkod')
def play_kod():
    miktar = request.args.get('miktar', '25')
    
    # Rastgele kod üret
    chars = string.ascii_uppercase + string.digits
    kod = '-'.join(''.join(random.choice(chars) for _ in range(4)) for _ in range(4))
    
    return jsonify({
        "kod": kod,
        "miktar": f"{miktar} TL",
        "durum": "başarılı",
        "Kurucu": "@OwnerSanal"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
