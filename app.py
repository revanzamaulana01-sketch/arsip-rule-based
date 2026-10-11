from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Load knowledge base
with open('rules.json', 'r', encoding='utf-8') as f:
    KNOWLEDGE = json.load(f)

# Load data surat (jika ada)
SURAT_FILE = 'data_surat.json'
if os.path.exists(SURAT_FILE):
    with open(SURAT_FILE, 'r', encoding='utf-8') as f:
        SURAT_DATA = json.load(f)
else:
    SURAT_DATA = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# === FORWARD CHAINING ENGINE ===
def forward_chain(fakta, rules):
    """Forward chaining: cocokkan fakta dengan aturan, return hasil klasifikasi"""
    fired = []
    hasil = None
    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule['nama'] not in fired:
                keywords = rule.get('keywords', [])
                # Rule dengan keywords kosong = fallback (selalu cocok)
                if not keywords or any(k in fakta['isi_surat'] for k in keywords):
                    hasil = rule['hasil']
                    fired.append(rule['nama'])
                    changed = True
    return hasil, fired

# === API ENDPOINTS ===
@app.route('/api/klasifikasi', methods=['POST'])
def klasifikasi():
    data = request.get_json()
    if not data or 'isi_surat' not in data:
        return jsonify({'status': 'error', 'message': 'Field isi_surat wajib diisi'}), 400
    fakta = {'isi_surat': data['isi_surat'].lower()}
    hasil, fired = forward_chain(fakta, KNOWLEDGE['rules'])
    return jsonify({
        'status': 'success',
        'data': {
            'klasifikasi': hasil,
            'aturan_terpicu': fired,
            'jumlah_aturan': len(fired)
        }
    })

@app.route('/api/surat', methods=['GET'])
def get_surat():
    return jsonify({'status': 'success', 'data': SURAT_DATA})

@app.route('/api/surat', methods=['POST'])
def tambah_surat():
    data = request.get_json()
    if not data or 'isi_surat' not in data:
        return jsonify({'status': 'error', 'message': 'Field isi_surat wajib diisi'}), 400
    fakta = {'isi_surat': data['isi_surat'].lower()}
    hasil, fired = forward_chain(fakta, KNOWLEDGE['rules'])
    surat = {
        'id': len(SURAT_DATA) + 1,
        'isi_surat': data['isi_surat'],
        'klasifikasi': hasil,
        'aturan_terpicu': fired
    }
    SURAT_DATA.append(surat)
    with open(SURAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(SURAT_DATA, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success', 'data': surat})

@app.route('/api/surat/<int:id>', methods=['DELETE'])
def hapus_surat(id):
    global SURAT_DATA
    SURAT_DATA = [s for s in SURAT_DATA if s['id'] != id]
    with open(SURAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(SURAT_DATA, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success', 'message': 'Surat dihapus'})

@app.route('/api/rules', methods=['GET'])
def get_rules():
    return jsonify({'status': 'success', 'data': KNOWLEDGE['rules']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
