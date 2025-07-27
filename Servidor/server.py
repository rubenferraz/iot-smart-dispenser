from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
import threading
import time as time_module
import pytz
import uuid

app = Flask(__name__)

ultimo_peso = 0
rodar_motor = False
agendamentos = []  # lista de dicts {"id": uuid, "datetime": datetime obj}

tz_lisboa = pytz.timezone("Europe/Lisbon")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/foto", methods=["POST"])
def receber_foto():
    foto = request.data
    with open("static/foto.jpg", "wb") as f:
        f.write(foto)
    print("📸 Nova foto recebida")
    return "OK"

@app.route("/peso", methods=["POST"])
def receber_peso():
    global ultimo_peso
    data = request.json
    if data and "peso" in data:
        ultimo_peso = data["peso"]
        print("📦 Peso recebido:", ultimo_peso)
        return "OK"
    return "Missing peso", 400

@app.route("/peso", methods=["GET"])
def enviar_peso():
    return jsonify({"peso": ultimo_peso})

@app.route("/motor", methods=["POST"])
def ativar_motor():
    global rodar_motor
    rodar_motor = True
    return "OK"

@app.route("/motor", methods=["GET"])
def get_motor():
    global rodar_motor
    if rodar_motor:
        rodar_motor = False
        print("🟢 Motor ativado pelo frontend")
        return jsonify({"motor": True})
    return jsonify({"motor": False})

@app.route("/agendar_motor", methods=["POST"])
def agendar_motor():
    data = request.json
    if not data or "datetime" not in data:
        return "Missing datetime", 400
    try:
        dt = datetime.fromisoformat(data["datetime"])
        if dt.tzinfo is None:
            dt = tz_lisboa.localize(dt)
        agora = datetime.now(tz_lisboa)
        if dt <= agora:
            return "A data/hora deve ser no futuro", 400
        agendamento_id = str(uuid.uuid4())
        agendamentos.append({"id": agendamento_id, "datetime": dt})
        print(f"⏰ Agendado motor para {dt} com id {agendamento_id}")
        return jsonify({"id": agendamento_id})
    except Exception as e:
        return f"Formato inválido: {e}", 400

@app.route("/agendamentos", methods=["GET"])
def listar_agendamentos():
    return jsonify([
        {"id": a["id"], "datetime": a["datetime"].isoformat()} for a in agendamentos
    ])

@app.route("/agendamentos/<agendamento_id>", methods=["DELETE"])
def apagar_agendamento(agendamento_id):
    global agendamentos
    before = len(agendamentos)
    agendamentos = [a for a in agendamentos if a["id"] != agendamento_id]
    after = len(agendamentos)
    if before == after:
        return "Agendamento não encontrado", 404
    print(f"🗑️ Agendamento {agendamento_id} apagado")
    return "OK"

def verificar_agendamento():
    global rodar_motor, agendamentos
    while True:
        agora = datetime.now(tz_lisboa)
        para_remover = []
        for a in agendamentos:
            delta = (agora - a["datetime"]).total_seconds()
            if 0 <= delta < 60:
                rodar_motor = True
                print(f"🟢 Motor rodando por agendamento! Hora: {agora}, id: {a['id']}")
                para_remover.append(a)
        for a in para_remover:
            agendamentos.remove(a)
        time_module.sleep(15)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    threading.Thread(target=verificar_agendamento, daemon=True).start()
    app.run(host="0.0.0.0", port=7453, ssl_context=('server.crt', 'server.key'))



