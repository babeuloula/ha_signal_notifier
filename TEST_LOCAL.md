# Test Local sans Home Assistant

Il est possible de tester la communication avec votre instance `signal-cli-rest-api` sans avoir besoin de lancer Home Assistant. Cela permet de valider que vos identifiants (URL et numéros) sont corrects et que l'API est accessible.

## Prérequis

- Python 3.8 ou supérieur installé.
- La bibliothèque `aiohttp` installée :
  ```bash
  pip install aiohttp
  ```
- Une instance de `signal-cli-rest-api` en cours d'exécution.

## Utilisation du script de test

Un script `test_api.py` est fourni à la racine du projet pour simuler l'envoi d'un message tel que le ferait l'intégration.

### Lancer le test

Ouvrez un terminal à la racine du projet et exécutez la commande suivante :

```bash
python test_api.py <URL_API> <SENDER> <RECIPIENTS> "<MESSAGE>" [<USERNAME> <PASSWORD> <NOTIFY_SELF> <TEXT_MODE> <ATTACHMENT_PATH>]
```

**Exemple sans authentification :**
```bash
python test_api.py http://192.168.1.10:8080 +33612345678 +33612345678 "Ceci est un test local"
```

**Exemple multi-destinataires :**
```bash
python test_api.py http://192.168.1.10:8080 +33612345678 "+33612345678;+33600000000" "Ceci est un test local"
```

**Exemple avec authentification :**
```bash
python test_api.py http://192.168.1.10:8080 +33612345678 +33612345678 "Ceci est un test local" mon_user mon_pass
```

### Paramètres :
- `<URL_API>` : L'URL complète vers votre instance Signal API (ex: `http://localhost:8080`).
- `<SENDER>` : Le numéro de téléphone expéditeur enregistré dans Signal (format international, ex: `+336...`).
- `<RECIPIENTS>` : Le ou les numéros de téléphone destinataires, séparés par des points-virgules (format international).
- `<MESSAGE>` : Le texte du message à envoyer (entre guillemets).
- `<USERNAME>` (Optionnel) : Le nom d'utilisateur pour le Basic Auth.
- `<PASSWORD>` (Optionnel) : Le mot de passe pour le Basic Auth.
- `<NOTIFY_SELF>` (Optionnel, défaut: `true`) : `true` ou `false` pour s'envoyer le message également à soi-même.
- `<TEXT_MODE>` (Optionnel, défaut: `styled`) : `normal` ou `styled`. `styled` permet le formatage Signal.
- `<ATTACHMENT_PATH>` (Optionnel) : Chemin vers un fichier image local à joindre au message, pour tester le champ `base64_attachments` de l'API.

## Interprétation des résultats

- **✅ Message envoyé avec succès !** : Tout fonctionne correctement. L'URL et les numéros sont valides, et l'API a accepté la requête.
- **❌ Erreur lors de l'envoi (400, 403, etc.)** : L'API est jointe mais refuse la requête. Vérifiez que le numéro expéditeur est bien enregistré sur cette instance et que le format est correct.
- **❌ Impossible de se connecter à l'API** : Le script n'a pas pu joindre le serveur. Vérifiez l'adresse IP, le port et que le pare-feu autorise la connexion.
