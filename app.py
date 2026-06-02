from flask import Flask, jsonify, request, url_for
from datetime import datetime
import threading
import time
import uuid
import paho.mqtt.client as mqtt

app = Flask(__name__)

# ==========================
# MQTT CONFIGURATION
# ==========================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

TOPIC_VISITOR = "interphone/rakezyadiams/v2/visitor"
TOPIC_COMMAND = "interphone/rakezyadiams/v2/command"
TOPIC_STATUS = "interphone/rakezyadiams/v2/status"

mqtt_client = None
mqtt_connected = False

# ==========================
# DONNÉES
# ==========================
visiteurs = []
mqtt_logs = []

etat_porte = {
    "etat": "fermee",
    "dernier_changement": "Aucun changement",
    "commande": "Aucune",
    "source": "Initialisation"
}


# ==========================
# FONCTIONS VISITEURS / PORTE
# ==========================
def ajouter_visiteur(source="ESP32-Wokwi MQTT"):
    maintenant = datetime.now()

    visite = {
        "id": len(visiteurs) + 1,
        "date": maintenant.strftime("%d/%m/%Y"),
        "heure": maintenant.strftime("%H:%M:%S"),
        "message": "Visiteur détecté devant la porte",
        "photo": "photo_simulee.jpg",
        "source": source
    }

    visiteurs.append(visite)
    print("Visiteur ajouté :", visite)
    return visite


def changer_etat_porte(etat, commande, source):
    maintenant = datetime.now()

    etat_porte["etat"] = etat
    etat_porte["dernier_changement"] = maintenant.strftime("%d/%m/%Y %H:%M:%S")
    etat_porte["commande"] = commande
    etat_porte["source"] = source

    print("État porte :", etat_porte)
    return etat_porte


def get_photo_url():
    return url_for("static", filename="photo_simulee.jpg")


# ==========================
# MQTT CALLBACKS
# ==========================
def on_connect(client, userdata, flags, rc):
    global mqtt_connected

    if rc == 0:
        mqtt_connected = True
        print("MQTT connecté au broker HiveMQ")

        client.subscribe(TOPIC_VISITOR)
        client.subscribe(TOPIC_STATUS)

        print("Abonné aux topics :")
        print("-", TOPIC_VISITOR)
        print("-", TOPIC_STATUS)
    else:
        mqtt_connected = False
        print("Erreur connexion MQTT, code :", rc)


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("MQTT déconnecté, code :", rc)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8", errors="ignore").strip()

    print("MQTT reçu :", topic, "=>", payload)

    mqtt_logs.append({
        "topic": topic,
        "payload": payload,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })

    if topic == TOPIC_VISITOR:
        payload_upper = payload.upper()

        if payload_upper.startswith("VISITOR") or payload_upper.startswith("VISITEUR") or payload_upper.startswith("SONNETTE"):
            ajouter_visiteur(source="ESP32-Wokwi MQTT")

    elif topic == TOPIC_STATUS:
        if payload.upper() == "OPENED":
            changer_etat_porte(
                "ouverte",
                "Relais activé côté ESP32",
                "ESP32-Wokwi MQTT"
            )

        elif payload.upper() == "CLOSED":
            changer_etat_porte(
                "fermee",
                "Relais désactivé côté ESP32",
                "ESP32-Wokwi MQTT"
            )


def start_mqtt():
    global mqtt_client

    try:
        mqtt_client = mqtt.Client(
            client_id=f"flask-interphone-rakezyadiams-{uuid.uuid4()}"
        )

        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message

        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()

    except Exception as e:
        print("Erreur MQTT :", e)


def publier_mqtt(topic, message):
    global mqtt_client

    if mqtt_client is None:
        return False, "Client MQTT non initialisé"

    try:
        result = mqtt_client.publish(topic, message)
        result.wait_for_publish(timeout=5)

        if result.is_published():
            print("MQTT publié :", topic, "=>", message)
            return True, "Message MQTT publié"
        else:
            return False, "Publication MQTT échouée"

    except Exception as e:
        print("Erreur publication MQTT :", e)
        return False, str(e)


def publier_commande_mqtt(commande):
    return publier_mqtt(TOPIC_COMMAND, commande)


# ==========================
# ROUTES FLASK
# ==========================
@app.route("/")
def accueil():
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Interphone vidéo connecté</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f5;
                color: #222;
                margin: 0;
                padding: 40px;
            }}
            .container {{
                max-width: 950px;
                margin: auto;
            }}
            .card {{
                background: white;
                padding: 28px;
                border-radius: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.10);
            }}
            h1 {{
                color: #2e5d4f;
                margin-top: 0;
            }}
            .subtitle {{
                color: #555;
                margin-bottom: 25px;
            }}
            .status {{
                background: #e8f3ee;
                border-left: 5px solid #2e5d4f;
                padding: 12px;
                margin: 20px 0;
                border-radius: 8px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 14px;
                margin-top: 20px;
            }}
            a.button {{
                display: block;
                background: #2e5d4f;
                color: white;
                text-decoration: none;
                text-align: center;
                padding: 13px;
                border-radius: 8px;
                font-weight: bold;
            }}
            a.button.secondary {{
                background: #5f7f73;
            }}
            a.button.danger {{
                background: #9b3d3d;
            }}
            .small {{
                font-size: 14px;
                color: #666;
                margin-top: 25px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Interphone vidéo connecté</h1>
                <p class="subtitle">
                    Serveur Flask — galerie visiteurs horodatée, historique, MQTT et commande relais.
                </p>

                <div class="status">
                    <strong>MQTT :</strong> {"connecté" if mqtt_connected else "non connecté"}<br>
                    <strong>Broker :</strong> {MQTT_BROKER}:{MQTT_PORT}<br>
                    <strong>État de la porte :</strong> {etat_porte["etat"]}<br>
                    <strong>Dernier changement :</strong> {etat_porte["dernier_changement"]}<br>
                    <strong>Dernière commande :</strong> {etat_porte["commande"]}<br>
                    <strong>Nombre visiteurs :</strong> {len(visiteurs)}
                </div>

                <div class="grid">
                    <a class="button" href="/sonnette">Simuler une sonnerie locale</a>
                    <a class="button" href="/visiteurs">Galerie visiteurs</a>
                    <a class="button secondary" href="/api/visiteurs">API JSON visiteurs</a>
                    <a class="button" href="/ouvrir">Ouvrir la porte MQTT</a>
                    <a class="button secondary" href="/fermer">Fermer la porte MQTT</a>
                    <a class="button secondary" href="/etat-porte">État de la porte</a>
                    <a class="button secondary" href="/mqtt-info">Infos MQTT</a>
                    <a class="button secondary" href="/mqtt-logs">Logs MQTT</a>
                    <a class="button secondary" href="/test-mqtt-visitor">Tester visiteur MQTT</a>
                    <a class="button danger" href="/reset">Réinitialiser historique</a>
                </div>

                <p class="small">
                    L’ESP32 Wokwi publie les événements de sonnerie via MQTT.
                    Flask enregistre automatiquement les visiteurs.
                    Kivy commande la porte via Flask, puis Flask publie OPEN/CLOSE vers l’ESP32.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/sonnette", methods=["GET", "POST"])
def sonnette():
    source = "Simulation locale Flask"

    if request.method == "POST":
        data = request.get_json(silent=True)
        if data and "source" in data:
            source = data["source"]

    visite = ajouter_visiteur(source)

    return jsonify({
        "status": "success",
        "message": "Visiteur enregistré avec succès",
        "visiteur": visite
    })


@app.route("/visiteurs")
def afficher_visiteurs():
    if len(visiteurs) == 0:
        contenu = """
        <div class="empty">
            Aucun visiteur enregistré pour le moment.
        </div>
        """
    else:
        contenu = ""
        for visite in reversed(visiteurs):
            contenu += f"""
            <div class="visitor-card">
                <div class="photo-box">
                    <img src="{get_photo_url()}" alt="Photo simulée visiteur"
                         onerror="this.style.display='none'; this.parentElement.innerHTML='Photo simulée';">
                </div>
                <div class="visitor-info">
                    <h3>Visiteur #{visite['id']}</h3>
                    <p><strong>Date :</strong> {visite['date']}</p>
                    <p><strong>Heure :</strong> {visite['heure']}</p>
                    <p><strong>Message :</strong> {visite['message']}</p>
                    <p><strong>Source :</strong> {visite['source']}</p>
                </div>
            </div>
            """

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Galerie visiteurs</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f5;
                color: #222;
                margin: 0;
                padding: 40px;
            }}
            .container {{
                max-width: 1100px;
                margin: auto;
            }}
            h1 {{
                color: #2e5d4f;
            }}
            .top-actions {{
                margin: 20px 0;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            a.button {{
                background: #2e5d4f;
                color: white;
                padding: 10px 14px;
                border-radius: 7px;
                text-decoration: none;
                font-weight: bold;
            }}
            a.secondary {{
                background: #5f7f73;
            }}
            a.danger {{
                background: #9b3d3d;
            }}
            .status {{
                background: white;
                border-left: 5px solid #2e5d4f;
                padding: 14px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 1px 6px rgba(0,0,0,0.08);
            }}
            .gallery {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 18px;
            }}
            .visitor-card {{
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.10);
            }}
            .photo-box {{
                height: 160px;
                background: #e8f3ee;
                color: #2e5d4f;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
            }}
            .photo-box img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            .visitor-info {{
                padding: 15px;
            }}
            .visitor-info h3 {{
                color: #2e5d4f;
                margin-top: 0;
            }}
            .visitor-info p {{
                margin: 7px 0;
                font-size: 14px;
            }}
            .empty {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.10);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Galerie des visiteurs horodatée</h1>

            <div class="status">
                <strong>Nombre de visiteurs :</strong> {len(visiteurs)}<br>
                <strong>MQTT :</strong> {"connecté" if mqtt_connected else "non connecté"}<br>
                <strong>État de la porte :</strong> {etat_porte["etat"]}<br>
                <strong>Dernier changement :</strong> {etat_porte["dernier_changement"]}
            </div>

            <div class="top-actions">
                <a class="button" href="/">Accueil</a>
                <a class="button" href="/sonnette">Ajouter visiteur test</a>
                <a class="button secondary" href="/ouvrir">Ouvrir porte MQTT</a>
                <a class="button secondary" href="/fermer">Fermer porte MQTT</a>
                <a class="button secondary" href="/mqtt-logs">Logs MQTT</a>
                <a class="button secondary" href="/test-mqtt-visitor">Test MQTT visiteur</a>
                <a class="button danger" href="/reset">Reset</a>
            </div>

            <div class="gallery">
                {contenu}
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/api/visiteurs")
def api_visiteurs():
    return jsonify({
        "status": "success",
        "nombre_visiteurs": len(visiteurs),
        "visiteurs": visiteurs
    })


@app.route("/ouvrir", methods=["GET", "POST"])
def ouvrir_porte():
    ok, message = publier_commande_mqtt("OPEN")

    changer_etat_porte(
        "ouverte",
        "Commande OPEN envoyée via MQTT",
        "Flask/Kivy"
    )

    return jsonify({
        "status": "success" if ok else "error",
        "message": message,
        "commande_mqtt": "OPEN",
        "etat_porte": etat_porte
    })


@app.route("/fermer", methods=["GET", "POST"])
def fermer_porte():
    ok, message = publier_commande_mqtt("CLOSE")

    changer_etat_porte(
        "fermee",
        "Commande CLOSE envoyée via MQTT",
        "Flask/Kivy"
    )

    return jsonify({
        "status": "success" if ok else "error",
        "message": message,
        "commande_mqtt": "CLOSE",
        "etat_porte": etat_porte
    })


@app.route("/etat-porte")
def voir_etat_porte():
    return jsonify({
        "status": "success",
        "mqtt_connected": mqtt_connected,
        "etat_porte": etat_porte
    })


@app.route("/mqtt-info")
def mqtt_info():
    return jsonify({
        "status": "success",
        "mqtt_connected": mqtt_connected,
        "broker": MQTT_BROKER,
        "port": MQTT_PORT,
        "topics": {
            "visitor": TOPIC_VISITOR,
            "command": TOPIC_COMMAND,
            "status": TOPIC_STATUS
        }
    })


@app.route("/mqtt-logs")
def voir_mqtt_logs():
    return jsonify({
        "status": "success",
        "logs": mqtt_logs[-30:]
    })


@app.route("/test-mqtt-visitor")
def test_mqtt_visitor():
    ok, message = publier_mqtt(TOPIC_VISITOR, "VISITOR")

    return jsonify({
        "status": "success" if ok else "error",
        "message": message,
        "topic": TOPIC_VISITOR,
        "payload": "VISITOR"
    })


@app.route("/reset")
def reset_historique():
    visiteurs.clear()
    mqtt_logs.clear()

    return jsonify({
        "status": "success",
        "message": "Historique et logs MQTT réinitialisés"
    })


# ==========================
# DÉMARRAGE MQTT
# ==========================
mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
