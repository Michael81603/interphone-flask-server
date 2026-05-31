from flask import Flask, jsonify, request
from datetime import datetime
import requests
import threading
import time
import os

app = Flask(__name__)

# À mettre dans Render Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "8232723414")

visiteurs = []

etat_porte = {
    "etat": "fermee",
    "dernier_changement": None
}

last_update_id = None


def ajouter_visiteur(source="Telegram"):
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


def lire_telegram():
    global last_update_id

    if not BOT_TOKEN:
        print("BOT_TOKEN manquant")
        return

    url = f"https://api.telegram.org/bot8367660862:AAHsBXuGHFtZ-7DVnwk08N04dQWDm446YwQ/getUpdates"

    params = {}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data.get("ok"):
            print("Erreur Telegram :", data)
            return

        for update in data.get("result", []):
            last_update_id = update["update_id"]

            message = update.get("message", {})
            text = message.get("text", "")
            chat = message.get("chat", {})
            chat_id = str(chat.get("id", ""))

            if chat_id == str(CHAT_ID) and "Alerte interphone" in text:
                ajouter_visiteur(source="Telegram ESP32-Wokwi")

    except Exception as e:
        print("Erreur lecture Telegram :", e)


def boucle_telegram():
    while True:
        lire_telegram()
        time.sleep(5)


@app.route("/")
def accueil():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Interphone vidéo connecté</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f4f6f5;
                color: #222;
            }
            h1 {
                color: #2e5d4f;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 760px;
            }
            a {
                display: block;
                margin: 10px 0;
                color: #2e5d4f;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Interphone vidéo connecté</h1>
            <p>Serveur Flask actif.</p>

            <h3>Menu</h3>
            <a href="/sync-telegram">Synchroniser Telegram</a>
            <a href="/sonnette">Simuler une sonnerie locale</a>
            <a href="/visiteurs">Voir l'historique des visiteurs</a>
            <a href="/api/visiteurs">API JSON visiteurs</a>
            <a href="/ouvrir">Ouvrir la porte</a>
            <a href="/etat-porte">Voir état de la porte</a>
            <a href="/reset">Réinitialiser historique</a>
        </div>
    </body>
    </html>
    """


@app.route("/sync-telegram")
def sync_telegram():
    lire_telegram()
    return jsonify({
        "status": "success",
        "message": "Synchronisation Telegram terminée",
        "nombre_visiteurs": len(visiteurs)
    })


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
    lignes = ""

    if len(visiteurs) == 0:
        lignes = """
        <tr>
            <td colspan="6">Aucun visiteur enregistré pour le moment.</td>
        </tr>
        """
    else:
        for visite in visiteurs:
            lignes += f"""
            <tr>
                <td>{visite['id']}</td>
                <td>{visite['date']}</td>
                <td>{visite['heure']}</td>
                <td>{visite['message']}</td>
                <td>{visite['photo']}</td>
                <td>{visite['source']}</td>
            </tr>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Historique des visiteurs</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f4f6f5;
                color: #222;
            }}
            h1 {{
                color: #2e5d4f;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            th {{
                background: #2e5d4f;
                color: white;
                padding: 12px;
            }}
            td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: center;
            }}
            tr:nth-child(even) {{
                background: #f8f8f8;
            }}
            a {{
                display: inline-block;
                margin-top: 20px;
                color: #2e5d4f;
                font-weight: bold;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h1>Historique des visiteurs</h1>

        <table>
            <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Heure</th>
                <th>Message</th>
                <th>Photo</th>
                <th>Source</th>
            </tr>
            {lignes}
        </table>

        <a href="/">Retour accueil</a>
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
    maintenant = datetime.now()

    etat_porte["etat"] = "ouverte"
    etat_porte["dernier_changement"] = maintenant.strftime("%d/%m/%Y %H:%M:%S")

    return jsonify({
        "status": "success",
        "message": "Porte ouverte avec succès",
        "etat_porte": etat_porte
    })


@app.route("/fermer", methods=["GET", "POST"])
def fermer_porte():
    maintenant = datetime.now()

    etat_porte["etat"] = "fermee"
    etat_porte["dernier_changement"] = maintenant.strftime("%d/%m/%Y %H:%M:%S")

    return jsonify({
        "status": "success",
        "message": "Porte fermée avec succès",
        "etat_porte": etat_porte
    })


@app.route("/etat-porte")
def voir_etat_porte():
    return jsonify({
        "status": "success",
        "etat_porte": etat_porte
    })


@app.route("/reset")
def reset_historique():
    visiteurs.clear()

    return jsonify({
        "status": "success",
        "message": "Historique réinitialisé"
    })


# Lancer la synchronisation Telegram en arrière-plan
thread = threading.Thread(target=boucle_telegram)
thread.daemon = True
thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)