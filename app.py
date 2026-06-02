from flask import Flask, jsonify, request, url_for
from datetime import datetime

app = Flask(__name__)

# Historique des visiteurs en mémoire
# Pour le projet simulation, c'est suffisant.
visiteurs = []

# État simulé de la porte / relais
etat_porte = {
    "etat": "fermee",
    "dernier_changement": "Aucun changement",
    "commande": "Aucune"
}


def ajouter_visiteur(source="Flask / Telegram"):
    """Ajoute un visiteur avec horodatage."""
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


def get_photo_url():
    """Retourne le chemin de la photo simulée."""
    return url_for("static", filename="photo_simulee.jpg")


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
                    Serveur Flask — galerie visiteurs horodatée, historique et commande relais simulée.
                </p>

                <div class="status">
                    <strong>État de la porte :</strong> {etat_porte["etat"]}<br>
                    <strong>Dernier changement :</strong> {etat_porte["dernier_changement"]}<br>
                    <strong>Dernière commande :</strong> {etat_porte["commande"]}
                </div>

                <div class="grid">
                    <a class="button" href="/sonnette">Simuler une sonnerie</a>
                    <a class="button" href="/visiteurs">Galerie visiteurs</a>
                    <a class="button secondary" href="/api/visiteurs">API JSON visiteurs</a>
                    <a class="button" href="/ouvrir">Ouvrir la porte</a>
                    <a class="button secondary" href="/fermer">Fermer la porte</a>
                    <a class="button secondary" href="/etat-porte">État de la porte</a>
                    <a class="button danger" href="/reset">Réinitialiser historique</a>
                </div>

                <p class="small">
                    Dans la simulation, la photo est représentée par une image statique.
                    Le relais est simulé côté Wokwi et la commande web est représentée par les routes Flask.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/sonnette", methods=["GET", "POST"])
def sonnette():
    """
    Enregistre un visiteur.
    Cette route peut être ouverte depuis le lien Telegram reçu après appui sur la sonnette.
    """
    source = "Lien Telegram / Flask"

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
    """Galerie visiteurs horodatée."""
    if len(visiteurs) == 0:
        contenu = """
        <div class="empty">
            Aucun visiteur enregistré pour le moment.
        </div>
        """
    else:
        contenu = ""
        for visite in visiteurs:
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
                <strong>État de la porte :</strong> {etat_porte["etat"]}<br>
                <strong>Dernier changement :</strong> {etat_porte["dernier_changement"]}
            </div>

            <div class="top-actions">
                <a class="button" href="/">Accueil</a>
                <a class="button" href="/sonnette">Ajouter visiteur test</a>
                <a class="button secondary" href="/ouvrir">Ouvrir porte</a>
                <a class="button secondary" href="/fermer">Fermer porte</a>
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
    """API JSON pour l'application Kivy."""
    return jsonify({
        "status": "success",
        "nombre_visiteurs": len(visiteurs),
        "visiteurs": visiteurs
    })


@app.route("/ouvrir", methods=["GET", "POST"])
def ouvrir_porte():
    """Commande web simulée du relais : ouverture porte."""
    maintenant = datetime.now()

    etat_porte["etat"] = "ouverte"
    etat_porte["dernier_changement"] = maintenant.strftime("%d/%m/%Y %H:%M:%S")
    etat_porte["commande"] = "Ouverture demandée depuis Flask"

    return jsonify({
        "status": "success",
        "message": "Commande relais : porte ouverte",
        "etat_porte": etat_porte
    })


@app.route("/fermer", methods=["GET", "POST"])
def fermer_porte():
    """Commande web simulée du relais : fermeture porte."""
    maintenant = datetime.now()

    etat_porte["etat"] = "fermee"
    etat_porte["dernier_changement"] = maintenant.strftime("%d/%m/%Y %H:%M:%S")
    etat_porte["commande"] = "Fermeture demandée depuis Flask"

    return jsonify({
        "status": "success",
        "message": "Commande relais : porte fermée",
        "etat_porte": etat_porte
    })


@app.route("/etat-porte")
def voir_etat_porte():
    """État actuel de la porte pour Flask/Kivy."""
    return jsonify({
        "status": "success",
        "etat_porte": etat_porte
    })


@app.route("/reset")
def reset_historique():
    """Réinitialise l'historique de test."""
    visiteurs.clear()

    return jsonify({
        "status": "success",
        "message": "Historique réinitialisé"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)