# 📊 Kriterion Quant - Pattern Matching Analysis

Analisi quantitativa avanzata per identificare pattern storici simili nei mercati finanziari utilizzando correlazioni basate su rendimenti cumulativi.

## 🎯 Descrizione

Questa applicazione Streamlit implementa un sistema di pattern matching che:
- **Analizza correlazioni annuali**: Confronta l'andamento Year-to-Date (YTD) con anni storici simili
- **Analizza correlazioni trimestrali**: Identifica trimestri storici con dinamiche di prezzo simili
- **Visualizza pattern**: Genera grafici interattivi per confrontare le traiettorie dei prezzi
- **Fornisce insight operativi**: Offre spunti didattici e operativi basati su analisi statistiche

## 🚀 Demo Live

[Link alla demo su Streamlit Cloud](https://your-app-name.streamlit.app) *(da configurare dopo il deployment)*

## 📋 Caratteristiche Principali

- ✅ **Doppia fonte dati**: EODHD API (primaria) e yfinance (fallback)
- ✅ **Analisi multi-timeframe**: Annuale e trimestrale
- ✅ **Correlazione robusta**: Basata su rendimenti cumulativi per maggiore stabilità
- ✅ **Interfaccia interattiva**: Parametri configurabili in real-time
- ✅ **Grafici Plotly**: Visualizzazioni professionali e interattive
- ✅ **Commenti didattici**: Spiegazioni integrate per interpretare i risultati

## 🛠️ Installazione Locale

### Prerequisiti
- Python 3.8 o superiore
- Git

### Passaggi

1. **Clona il repository**
```bash
git clone https://github.com/tuousername/kriterion-quant-pattern.git
cd kriterion-quant-pattern
```

2. **Crea un ambiente virtuale** (consigliato)
```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

4. **Configura i secrets**
```bash
# Copia il file di esempio
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Modifica il file con la tua API key EODHD
# nano .streamlit/secrets.toml  # o usa il tuo editor preferito
```

5. **Esegui l'applicazione**
```bash
streamlit run app.py
```

L'app sarà disponibile su `http://localhost:8501`

## 🔑 Configurazione API

### EODHD (Opzionale ma consigliato)
1. Registrati su [EOD Historical Data](https://eodhistoricaldata.com/)
2. Ottieni la tua API key
3. Inseriscila nel file `.streamlit/secrets.toml`

**Nota**: L'app funziona anche senza API key utilizzando yfinance come fallback, ma con limitazioni sui dati disponibili.

## 📊 Come Utilizzare l'Applicazione

### 1. Configurazione Parametri (Sidebar)
- **Ticker**: Inserisci il simbolo dell'asset (es. SPY, QQQ, ETH-USD)
- **Exchange**: Seleziona US per azioni, CC per crypto
- **Correlazione Minima**: Soglia per considerare un periodo "simile" (default: 0.70)
- **Top N Simili**: Numero di periodi simili da visualizzare (default: 5)

### 2. Interpretazione dei Risultati

#### Tab Analisi Annuale
- **Grafico**: Confronta l'andamento YTD corrente con anni storici simili
- **Tabella**: Mostra correlazioni e rendimenti degli anni analoghi
- **Metriche**: Statistiche aggregate sui pattern identificati

#### Tab Analisi Trimestrale
- **Grafico**: Focus sul trimestre corrente vs trimestri storici simili
- **Tabella**: Dettaglio correlazioni e performance trimestrali
- **Metriche**: Analisi statistica dei trimestri correlati

#### Tab Dati Storici
- Panoramica completa della serie storica
- Statistiche generali e ultimi movimenti

### 3. Interpretazione degli Insight

I commenti didattici evidenziati in blu forniscono:
- **Spunti operativi**: Come utilizzare i pattern per decisioni di trading
- **Avvertenze**: Ricordano che si tratta di analisi probabilistiche, non previsionali
- **Suggerimenti**: Per affinare l'analisi modificando i parametri

## 🌐 Deploy su Streamlit Cloud

1. **Fork questo repository** su GitHub
2. **Vai su** [Streamlit Cloud](https://streamlit.io/cloud)
3. **Connetti il tuo account GitHub**
4. **Crea una nuova app** selezionando il repository
5. **Configura i secrets**:
   - Vai in App Settings → Secrets
   - Aggiungi: `EODHD_API_KEY = "tua_api_key"`
6. **Deploy!** L'app sarà live in pochi minuti

## 📁 Struttura del Progetto

```
kriterion-quant-pattern/
│
├── app.py                      # Applicazione principale Streamlit
├── requirements.txt            # Dipendenze Python
├── README.md                   # Documentazione (questo file)
├── .gitignore                  # File da ignorare in git
│
└── .streamlit/
    ├── config.toml             # Configurazione Streamlit
    └── secrets.toml.example    # Template per i secrets
```

## 🔧 Personalizzazione

### Modificare i Parametri di Default
Edita la classe `Config` in `app.py`:
```python
class Config:
    MIN_CORRELATION: float = 0.70  # Modifica soglia correlazione
    TOP_N_SIMILAR: int = 5         # Modifica numero risultati
    START_DATE: str = "2006-01-01" # Modifica data inizio storico
```

### Cambiare il Tema Visivo
Modifica `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#00ff00"        # Colore principale
backgroundColor = "#1e1e1e"     # Sfondo
textColor = "#f0f0f0"           # Testo
```

## 📈 Metodologia

### Calcolo delle Correlazioni
L'algoritmo utilizza la correlazione di Pearson sui **rendimenti cumulativi** invece che sui rendimenti giornalieri. Questo approccio:
- Riduce il rumore statistico
- Si concentra sulla "forma" della traiettoria
- Produce risultati più stabili e significativi

### Formula
```python
cum_returns = (1 + daily_returns).cumprod() - 1
correlation = pearson_correlation(cum_returns_1, cum_returns_2)
```

## ⚠️ Disclaimer

**IMPORTANTE**: Questo strumento fornisce analisi storiche e correlazioni statistiche a scopo educativo e informativo. 
- NON costituisce consulenza finanziaria
- I risultati passati NON garantiscono performance future
- Usa sempre il tuo giudizio e consulta professionisti qualificati per decisioni di investimento

## 🤝 Contributi

I contributi sono benvenuti! Per contribuire:
1. Fork il progetto
2. Crea un branch (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📝 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 📧 Contatti

Kriterion Quant - [info@kriterionquant.com](mailto:info@kriterionquant.com)

Link Progetto: [https://github.com/tuousername/kriterion-quant-pattern](https://github.com/tuousername/kriterion-quant-pattern)

## 🙏 Riconoscimenti

- [Streamlit](https://streamlit.io/) per il framework
- [Plotly](https://plotly.com/) per le visualizzazioni
- [yfinance](https://github.com/ranaroussi/yfinance) per i dati di fallback
- [EODHD](https://eodhistoricaldata.com/) per i dati storici premium

---

*Sviluppato con ❤️ per la community di trading quantitativo*
