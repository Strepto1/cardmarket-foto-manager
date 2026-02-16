# 📷 Cardmarket Foto Manager

Een Progressive Web App (PWA) voor het beheren van foto-verzoeken van Cardmarket kopers. Werkt volledig offline na installatie en synchroniseert handmatig met Gmail.

## ✨ Features

- **Progressive Web App**: Installeerbaar als standalone app op Android/iOS
- **Gmail Integratie**: Automatisch foto-verzoeken detecteren uit Cardmarket emails
- **Camera Functionaliteit**: Direct foto's maken met de achtercamera
- **Offline Werking**: Alle data wordt lokaal opgeslagen in IndexedDB
- **Meerdere Foto's**: Maak meerdere foto's per verzoek (voor/achterkant)
- **Batch Download**: Download alle foto's van een taak tegelijk
- **Email Compose**: Direct Gmail openen met voorgevulde reply
- **Export/Import**: Backup en herstel je data

## 🚀 Snelle Start

### Stap 1: Google Cloud Project Setup

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Maak een nieuw project aan (of selecteer een bestaand project)
3. Ga naar **APIs & Services** > **Library**
4. Zoek en activeer **Gmail API**
5. Ga naar **APIs & Services** > **Credentials**
6. Klik **Create Credentials** > **OAuth client ID**
7. Selecteer **Web application**
8. Geef het een naam (bijv. "Cardmarket Foto Manager")
9. Voeg toe bij **Authorized JavaScript origins**:
   - `http://localhost:8000` (voor lokaal testen)
   - `https://jouw-domein.com` (voor productie)
10. Klik **Create** en kopieer je **Client ID**

### Stap 2: OAuth Consent Screen

1. Ga naar **APIs & Services** > **OAuth consent screen**
2. Selecteer **External** (tenzij je G Suite hebt)
3. Vul de vereiste velden in:
   - App naam: "Cardmarket Foto Manager"
   - User support email: je email
   - Developer contact: je email
4. Klik **Save and Continue**
5. Bij **Scopes**, klik **Add or Remove Scopes**
6. Voeg toe: `https://www.googleapis.com/auth/gmail.readonly`
7. Klik **Save and Continue**
8. Voeg jezelf toe als Test User
9. Klik **Save and Continue**

### Stap 3: Client ID Configureren

Open `index.html` en vervang deze regel:

```javascript
const GOOGLE_CLIENT_ID = 'YOUR_CLIENT_ID_HERE.apps.googleusercontent.com';
```

Met je eigen Client ID:

```javascript
const GOOGLE_CLIENT_ID = '123456789-abc123def456.apps.googleusercontent.com';
```

### Stap 4: Iconen Genereren

1. Open `icon-generator.html` in een browser
2. Klik op elke "Download" link om de PNG iconen te downloaden
3. Plaats de gedownloade bestanden in de `icons/` map

### Stap 5: Hosten

De app vereist HTTPS voor camera en PWA functionaliteit. Kies een van deze opties:

#### Optie A: GitHub Pages (Gratis)

1. Maak een nieuwe GitHub repository
2. Upload alle bestanden
3. Ga naar **Settings** > **Pages**
4. Selecteer **main** branch en **root** folder
5. Je app is beschikbaar op `https://username.github.io/repo-naam/`

#### Optie B: Netlify (Gratis)

1. Ga naar [netlify.com](https://netlify.com)
2. Sleep de projectmap naar de dropzone
3. Je krijgt direct een HTTPS URL

#### Optie C: Firebase Hosting

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

#### Optie D: Lokaal Testen

```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .
```

Open `http://localhost:8000` in Chrome (HTTPS niet nodig voor localhost)

### Stap 6: Installeren op Android

1. Open de app URL in Chrome op je Android telefoon
2. Wacht tot de pagina geladen is
3. Tik op de drie puntjes (menu) rechtsboven
4. Kies **"Toevoegen aan startscherm"** of **"App installeren"**
5. Bevestig de installatie
6. De app verschijnt als icoon op je startscherm

## 📱 Gebruik

### Gmail Synchroniseren

1. Tik op de **🔄** knop rechtsboven
2. Log in met je Google account (eerste keer)
3. De app zoekt naar emails met "Cardmarket message from" in het onderwerp
4. Alleen foto-gerelateerde verzoeken worden toegevoegd

### Foto's Maken

1. Tik op een taak om hem uit te vouwen
2. Tik op **📸 Foto**
3. De camera opent - maak zoveel foto's als nodig
4. Tik op **✕** om de camera te sluiten
5. Foto's worden automatisch opgeslagen

### Email Beantwoorden

1. Download eerst alle foto's met **💾 Download Alle**
2. Tik op **✉️ Email**
3. Gmail opent met voorgevulde reply
4. Voeg de gedownloade foto's toe als bijlage
5. Verstuur!

### Handmatig Taak Toevoegen

Voor emails die niet automatisch gedetecteerd worden:

1. Tik op **➕** rechtsboven
2. Vul de gegevens in
3. Tik op **Opslaan**

## 🔧 Troubleshooting

### "Token verlopen" fout

- Log uit via Instellingen en log opnieuw in

### Camera werkt niet

- Controleer of je toestemming hebt gegeven voor camera gebruik
- Zorg dat de app via HTTPS draait (of localhost)
- Probeer Chrome te herstarten

### Emails worden niet gevonden

- Controleer of de Gmail API geactiveerd is
- Zorg dat je jezelf hebt toegevoegd als Test User
- Controleer de email filter: alleen emails met foto-gerelateerde keywords worden gedetecteerd

### App installeert niet

- De app moet via HTTPS geserveerd worden
- Wacht tot de pagina volledig geladen is
- Controleer of `manifest.json` correct geladen wordt (DevTools > Application)

## 📁 Bestandsstructuur

```
cardmarket-pwa/
├── index.html          # Hoofdapplicatie
├── sw.js               # Service Worker
├── manifest.json       # PWA manifest
├── icon-generator.html # Tool om iconen te genereren
├── icons/
│   ├── icon.svg        # Bronbestand icoon
│   ├── icon-72.png
│   ├── icon-96.png
│   ├── icon-128.png
│   ├── icon-144.png
│   ├── icon-152.png
│   ├── icon-192.png
│   ├── icon-384.png
│   └── icon-512.png
└── README.md           # Deze documentatie
```

## 🔐 Privacy & Veiligheid

- Alle data wordt **lokaal** opgeslagen op je apparaat
- Er is **geen backend server** - alles draait client-side
- Gmail tokens worden veilig opgeslagen in IndexedDB
- De app vraagt alleen **leestoegang** tot Gmail (geen schrijftoegang)
- Foto's verlaten nooit je apparaat tenzij je ze exporteert

## 🔄 Updates

De Service Worker cached de app voor offline gebruik. Om updates te forceren:

1. Open de app in Chrome
2. Ga naar DevTools (F12) > Application > Service Workers
3. Klik op "Update" of "Unregister"
4. Herlaad de pagina

## 📜 Licentie

MIT License - Vrij te gebruiken en aan te passen.

## 🙏 Credits

Gebouwd met:
- Vanilla JavaScript (geen frameworks)
- IndexedDB voor lokale opslag
- Gmail API voor email sync
- Service Workers voor offline functionaliteit
