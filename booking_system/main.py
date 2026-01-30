import json
import os
import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# ==========================================
# 【已配置】你的钉钉机器人地址
DING_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=a41d4e65015ca4350fa86fc88e3c2f87e2b6425d77434e1e175cbdd0735490c3'
# ==========================================

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 【关键修改】数据专门存在 data 文件夹下，方便 Zeabur 挂载
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATA_FILE = os.path.join(DATA_DIR, 'booking_data.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'admin_config.json')

# --- 钉钉通知 ---
def send_dingtalk_msg(applicant, unit, leader, date, time, reason):
    text = f"### 🔔 新预约申请\n- **申请人**：{applicant}\n- **单位**：{unit}\n- **领导**：{leader}\n- **时间**：{date} {time}\n- **事由**：{reason}\n> 请管理员登录审批"
    try:
        requests.post(DING_WEBHOOK, json={"msgtype": "markdown", "markdown": {"title": "新预约", "text": text}}, timeout=3)
    except: pass

def send_reject_notice(applicant, leader, suggestion):
    text = f"### ❌ 预约被驳回\n- **申请人**：{applicant}\n- **领导**：{leader}\n- **建议调整至**：{suggestion}\n> 请重新提交申请"
    try:
        requests.post(DING_WEBHOOK, json={"msgtype": "markdown", "markdown": {"title": "驳回通知", "text": text}}, timeout=3)
    except: pass

def send_approve_notice(applicant, leader, date, time):
    text = f"### ✅ 预约已通过\n- **申请人**：{applicant}\n- **领导**：{leader}\n- **确认时间**：{date} {time}\n> 请准时参加"
    try:
        requests.post(DING_WEBHOOK, json={"msgtype": "markdown", "markdown": {"title": "通过通知", "text": text}}, timeout=3)
    except: pass

# --- 数据读写 ---
def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_admin_password():
    if not os.path.exists(CONFIG_FILE): return "admin"
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f).get('password', 'admin')
    except: return "admin"

def set_admin_password(new_pwd):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"password": new_pwd}, f, ensure_ascii=False)

# --- 路由 ---
@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'templates'), 'index.html')

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    return jsonify(load_data())

@app.route('/api/book', methods=['POST'])
def add_appointment():
    new_app = request.json
    data = load_data()
    data.append(new_app)
    save_data(data)
    send_dingtalk_msg(new_app.get('applicantName'), new_app.get('applicantUnit'), new_app.get('leader'), new_app.get('date'), new_app.get('time'), new_app.get('reason'))
    return jsonify({"status": "success", "data": data})

@app.route('/api/approve', methods=['POST'])
def approve_appointment():
    req = request.json
    data = load_data()
    target_app = None
    for item in data:
        if item['id'] == req.get('id'):
            item['status'] = 'booked'
            target_app = item
            break
    save_data(data)
    if target_app:
        send_approve_notice(target_app.get('applicantName'), target_app.get('leader'), target_app.get('date'), target_app.get('time'))
    return jsonify({"status": "success"})

@app.route('/api/reject', methods=['POST'])
def reject_appointment():
    req = request.json
    target_id = req.get('id')
    suggestion = req.get('suggestion', '建议另行预约')
    data = load_data()
    target_app = None
    for item in data:
        if item['id'] == target_id:
            item['status'] = 'rejected'
            item['rejectSuggestion'] = suggestion
            target_app = item
            break
    save_data(data)
    if target_app:
        send_reject_notice(target_app.get('applicantName'), target_app.get('leader'), suggestion)
    return jsonify({"status": "success"})

@app.route('/api/login_check', methods=['POST'])
def login_check():
    if request.json.get('password') == get_admin_password():
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"}), 401

@app.route('/api/change_password', methods=['POST'])
def change_password():
    req = request.json
    if req.get('oldPassword') != get_admin_password():
        return jsonify({"status": "fail", "msg": "旧密码错误"})
    set_admin_password(req.get('newPassword'))
    return jsonify({"status": "success"})

# 【Zeabur 启动方式】监听 0.0.0.0 和 环境变量 PORT
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)