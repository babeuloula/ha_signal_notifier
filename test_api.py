import asyncio
import aiohttp
import sys
import json

async def test_signal(url, sender, recipients, message, username=None, password=None, notify_self=True, text_mode="styled", attachment_path=None):
    """Simule l'envoi d'un message Signal tel que fait par l'intégration."""
    url = url.rstrip("/")
    endpoint = f"{url}/v2/send"

    # Gestion des destinataires
    if recipients:
        recipient_list = [r.strip() for r in recipients.split(";") if r.strip()]
    else:
        recipient_list = [sender]

    payload = {
        "message": message,
        "number": sender,
        "recipients": recipient_list,
        "notify_self": notify_self,
        "text_mode": text_mode
    }

    if attachment_path:
        import base64
        import mimetypes
        import os

        with open(attachment_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        content_type = mimetypes.guess_type(attachment_path)[0] or "application/octet-stream"
        filename = os.path.basename(attachment_path)
        payload["base64_attachments"] = [
            f"data:{content_type};filename={filename};base64,{encoded}"
        ]
        print(f"Pièce jointe  : {attachment_path} ({content_type})")

    print(f"--- Test de connexion Signal ---")
    print(f"URL API      : {endpoint}")
    print(f"Expéditeur   : {sender}")
    print(f"Destinataires: {', '.join(recipient_list)}")
    print(f"Message      : {message}")
    print(f"Notify Self  : {notify_self}")
    print(f"Text Mode    : {text_mode}")
    if username:
        print(f"Auth         : Basic Auth activée ({username})")
    print(f"--------------------------------")

    auth = None
    if username and password:
        auth = aiohttp.BasicAuth(username, password)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, auth=auth) as response:
                if response.status >= 400:
                    text = await response.text()
                    print(f"❌ Erreur lors de l'envoi ({response.status})")
                    print(f"Réponse du serveur : {text}")
                else:
                    print("✅ Message envoyé avec succès !")
                    try:
                        resp_json = await response.json()
                        print(f"Réponse API : {json.dumps(resp_json, indent=2)}")
                    except:
                        pass
    except aiohttp.ClientConnectorError:
        print(f"❌ Impossible de se connecter à l'API à l'adresse : {url}")
        print("Vérifiez que signal-cli-rest-api est bien lancé et accessible.")
    except Exception as e:
        print(f"❌ Une erreur inattendue est survenue : {e}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python test_api.py <URL_API> <SENDER> <RECIPIENTS> <MESSAGE> [<USERNAME> <PASSWORD> <NOTIFY_SELF> <TEXT_MODE> <ATTACHMENT_PATH>]")
        print("Note: <RECIPIENTS> peut être plusieurs numéros séparés par des points-virgules")
        print("Exemple: python test_api.py http://localhost:8080 +33612345678 +33612345678;+33600000000 \"Test local\"")
        sys.exit(1)

    url_arg = sys.argv[1]
    sender_arg = sys.argv[2]
    recipients_arg = sys.argv[3]
    message_arg = sys.argv[4]
    username_arg = sys.argv[5] if len(sys.argv) > 5 else None
    password_arg = sys.argv[6] if len(sys.argv) > 6 else None
    notify_self_arg = sys.argv[7].lower() == "true" if len(sys.argv) > 7 else True
    text_mode_arg = sys.argv[8] if len(sys.argv) > 8 else "styled"
    attachment_path_arg = sys.argv[9] if len(sys.argv) > 9 else None

    asyncio.run(test_signal(url_arg, sender_arg, recipients_arg, message_arg, username_arg, password_arg, notify_self_arg, text_mode_arg, attachment_path_arg))
