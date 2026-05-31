from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Historique des visiteurs
# Version simple en mémoire pour la simulation
visiteurs = []

# État de la porte
etat_porte = {
    "etat": "fermee",
    "dernier_changement": None
}


def ajouter_visiteur(source="ESP32-Wokwi"):
    """Ajoute un visiteur avec date et heure."""
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
    return visite


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
                max-width: 700px;
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
            <a href="/sonnette">Simuler une sonnerie</a>
            <a href="/visiteurs">Voir l'historique des visiteurs</a>
            <a href="/api/visiteurs">API JSON visiteurs</a>
            <a href="/ouvrir">Ouvrir la porte</a>
            <a href="/etat-porte">Voir état de la porte</a>
        </div>
    </body>
    </html>
    """


@app.route("/sonnette", methods=["GET", "POST"])
def sonnette():
    """
    Route appelée par l'ESP32/Wokwi quand le bouton sonnette est appuyé.
    Elle enregistre un visiteur avec horodatage.
    """
    source = "ESP32-Wokwi"

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
    """Affiche l'historique des visiteurs en HTML."""
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
    """API utilisée plus tard par l'application Kivy."""
    return jsonify({
        "status": "success",
        "nombre_visiteurs": len(visiteurs),
        "visiteurs": visiteurs
    })


@app.route("/ouvrir", methods=["GET", "POST"])
def ouvrir_porte():
    """
    Route pour simuler l'ouverture de la porte.
    Plus tard, Kivy pourra appeler cette route.
    """
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
    """Route pour simuler la fermeture de la porte."""
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
    """Retourne l'état actuel de la porte."""
    return jsonify({
        "status": "success",
        "etat_porte": etat_porte
    })


@app.route("/reset")
def reset_historique():
    """Réinitialise l'historique. Utile pendant les tests."""
    visiteurs.clear()

    return jsonify({
        "status": "success",
        "message": "Historique réinitialisé"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
