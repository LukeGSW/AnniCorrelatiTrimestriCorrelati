# app.py
"""
Kriterion Quant - Pattern Matching Analysis
Analisi di correlazione per identificare anni e trimestri storici simili
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =====================================================
# CONFIGURAZIONE PAGINA E STILE
# =====================================================
st.set_page_config(
    page_title="Kriterion Quant - Pattern Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato per i commenti didattici e fix visualizzazione
st.markdown("""
<style>
    /* Fix per le metriche con sfondo scuro */
    [data-testid="metric-container"] {
        background-color: #2a2a2a !important;
        border: 1px solid #4a4a4a !important;
        padding: 15px !important;
        border-radius: 5px !important;
        color: #f0f0f0 !important;
    }
    
    [data-testid="metric-container"] > div {
        color: #f0f0f0 !important;
    }
    
    /* Fix per i valori delle metriche */
    [data-testid="stMetricValue"] {
        color: #00ff00 !important;
        font-weight: bold !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }
    
    /* Fix per le tabelle */
    .dataframe {
        color: #f0f0f0 !important;
        background-color: #2a2a2a !important;
    }
    
    .dataframe td {
        color: #f0f0f0 !important;
        background-color: #2a2a2a !important;
    }
    
    .dataframe th {
        color: #f0f0f0 !important;
        background-color: #1a1a1a !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #3a3a3a !important;
    }
    
    /* Commenti didattici con tema scuro */
    .didactic {
        background-color: #1e3a5f;
        border-left: 5px solid #4682b4;
        padding: 15px;
        margin: 15px 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 1.1em;
        line-height: 1.6;
        color: #e0e0e0;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .didactic strong {
        color: #61dafb;
    }
    
    /* Fix per elementi streamlit */
    .stButton > button {
        background-color: #2a2a2a;
        color: #f0f0f0;
        border: 1px solid #4a4a4a;
    }
    
    .stButton > button:hover {
        background-color: #3a3a3a;
        border-color: #00ff00;
    }
    
    /* Fix per selectbox e input */
    .stSelectbox > div > div {
        background-color: #2a2a2a !important;
        color: #f0f0f0 !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #2a2a2a !important;
        color: #f0f0f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# CLASSE DI CONFIGURAZIONE
# =====================================================
class Config:
    """Configurazione centralizzata per l'applicazione"""
    # Parametri di analisi
    MIN_CORRELATION: float = 0.70
    TOP_N_SIMILAR: int = 5
    
    # Parametri temporali
    START_DATE: str = "2006-01-01"
    CURRENT_YEAR: int = datetime.now().year
    
    # Stile grafici
    CHART_TEMPLATE: str = "plotly_dark"
    COLOR_CURRENT: str = "#00ff00"
    COLOR_SIMILAR: List[str] = ["#ff9500", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4"]

# =====================================================
# DATA LOADER
# =====================================================
@st.cache_data(ttl=3600)
def fetch_data(ticker: str, exchange: str, start_date: str, api_key: str = None) -> pd.DataFrame:
    """
    Scarica i dati storici da EODHD o yfinance (fallback)
    Cache dei dati per 1 ora per evitare richieste ripetute
    """
    # Prima prova con EODHD se abbiamo l'API key
    if api_key and api_key != "YOUR_API_KEY_HERE" and not api_key.startswith("la-tu"):
        try:
            endpoint = f"https://eodhistoricaldata.com/api/eod/{ticker}.{exchange}"
            params = {
                'api_token': api_key,
                'from': start_date,
                'fmt': 'json',
                'period': 'd'
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df['returns'] = df['adjusted_close'].pct_change()
                df['cum_returns'] = (1 + df['returns']).cumprod() - 1
                return df.dropna()
        except Exception as e:
            st.warning(f"EODHD non disponibile: {str(e)[:100]}. Uso yfinance come fallback.")
    
    # Fallback su yfinance
    try:
        # Mapping intelligente del ticker per yfinance
        if exchange.lower() == "cc":
            # Crypto - usa il ticker così com'è ma in maiuscolo
            yf_ticker = ticker.upper()  # eth-usd -> ETH-USD
        else:
            # Azioni - usa solo il simbolo senza exchange
            yf_ticker = ticker.upper().replace('.US', '').replace('.EU', '')  # SPY.US -> SPY
            
        df = yf.download(yf_ticker, start=start_date, progress=False)
        if not df.empty:
            # Standardizza i nomi delle colonne per compatibilità
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df['adjusted_close'] = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
            df['returns'] = df['adjusted_close'].pct_change()
            df['cum_returns'] = (1 + df['returns']).cumprod() - 1
            return df.dropna()
    except Exception as e:
        st.error(f"Errore nel caricamento dati con yfinance: {str(e)}")
        return pd.DataFrame()

# =====================================================
# PATTERN MATCHER
# =====================================================
class PatternMatcher:
    """Motore di analisi per correlazioni e pattern matching"""
    
    def __init__(self, data: pd.DataFrame):
        if data.empty:
            raise ValueError("DataFrame vuoto")
        self.data = data
        self.current_year = datetime.now().year
        
    def calculate_ytd_correlation(self, year1: int, year2: int) -> float:
        """Calcola correlazione tra rendimenti cumulativi YTD di due anni"""
        end_month = datetime.now().month
        end_day = datetime.now().day
        
        try:
            # Estrai dati YTD per entrambi gli anni
            data1 = self.data[self.data.index.year == year1].copy()
            data1 = data1[(data1.index.month < end_month) | 
                         ((data1.index.month == end_month) & (data1.index.day <= end_day))]
            
            data2 = self.data[self.data.index.year == year2].copy()
            data2 = data2[(data2.index.month < end_month) |
                         ((data2.index.month == end_month) & (data2.index.day <= end_day))]
            
            min_len = min(len(data1), len(data2))
            if min_len < 20:
                return np.nan
                
            # Usa rendimenti cumulativi per correlazione più stabile
            cum_returns1 = ((1 + data1['returns'].iloc[:min_len]).cumprod() - 1).values
            cum_returns2 = ((1 + data2['returns'].iloc[:min_len]).cumprod() - 1).values
            
            mask = ~(np.isnan(cum_returns1) | np.isnan(cum_returns2))
            if mask.sum() < 20:
                return np.nan
                
            return np.corrcoef(cum_returns1[mask], cum_returns2[mask])[0, 1]
        except:
            return np.nan
            
    def find_similar_years(self, reference_year: int, min_correlation: float) -> pd.DataFrame:
        """Trova anni storici simili all'anno di riferimento"""
        correlations = []
        years = sorted(self.data.index.year.unique())
        
        for year in years:
            if year == reference_year:
                continue
                
            corr = self.calculate_ytd_correlation(reference_year, year)
            
            if not np.isnan(corr) and corr >= min_correlation:
                year_data = self.data[self.data.index.year == year]
                if len(year_data) > 0:
                    year_return = ((year_data['adjusted_close'].iloc[-1] / 
                                   year_data['adjusted_close'].iloc[0]) - 1) * 100
                    ytd_return = self._get_ytd_return(year, datetime.now().month, datetime.now().day)
                else:
                    year_return = np.nan
                    ytd_return = np.nan
                    
                correlations.append({
                    'year': year,
                    'correlation': corr,
                    'year_return': year_return,
                    'ytd_return_at_similar_point': ytd_return
                })
                
        if correlations:
            df_corr = pd.DataFrame(correlations)
            return df_corr.sort_values('correlation', ascending=False).head(Config.TOP_N_SIMILAR)
        return pd.DataFrame()
        
    def _get_ytd_return(self, year: int, month: int, day: int) -> float:
        """Calcola rendimento YTD fino a una data specifica"""
        try:
            year_data = self.data[self.data.index.year == year]
            subset = year_data[(year_data.index.month < month) |
                              ((year_data.index.month == month) & (year_data.index.day <= day))]
            if len(subset) > 1:
                return ((subset['adjusted_close'].iloc[-1] / 
                        subset['adjusted_close'].iloc[0]) - 1) * 100
        except:
            pass
        return np.nan
        
    def get_quarter_data(self, year: int, quarter: int) -> pd.DataFrame:
        """Estrai dati di un trimestre specifico"""
        quarter_months = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        months = quarter_months.get(quarter, [])
        data = self.data[self.data.index.year == year]
        return data[data.index.month.isin(months)]
        
    def calculate_quarterly_correlation(self, year1: int, q1: int, year2: int, q2: int) -> float:
        """Calcola correlazione tra rendimenti cumulativi di due trimestri"""
        try:
            data1 = self.get_quarter_data(year1, q1)
            data2 = self.get_quarter_data(year2, q2)
            
            if len(data1) < 15 or len(data2) < 15:
                return np.nan
                
            min_len = min(len(data1), len(data2))
            cum_returns1 = ((1 + data1['returns'].iloc[:min_len]).cumprod() - 1).values
            cum_returns2 = ((1 + data2['returns'].iloc[:min_len]).cumprod() - 1).values
            
            mask = ~(np.isnan(cum_returns1) | np.isnan(cum_returns2))
            if mask.sum() < 15:
                return np.nan
                
            return np.corrcoef(cum_returns1[mask], cum_returns2[mask])[0, 1]
        except:
            return np.nan
            
    def find_similar_quarters(self, reference_year: int, reference_quarter: int, 
                            min_correlation: float) -> pd.DataFrame:
        """Trova trimestri storici simili"""
        correlations = []
        years = sorted(self.data.index.year.unique())
        
        for year in years:
            for quarter in [1, 2, 3, 4]:
                if year == reference_year and quarter == reference_quarter:
                    continue
                    
                corr = self.calculate_quarterly_correlation(
                    reference_year, reference_quarter, year, quarter
                )
                
                if not np.isnan(corr) and corr >= min_correlation:
                    quarter_return = self._get_quarter_return(year, quarter)
                    correlations.append({
                        'year': year,
                        'quarter': quarter,
                        'year_quarter': f"{year}-Q{quarter}",
                        'correlation': corr,
                        'quarter_return': quarter_return
                    })
                    
        if correlations:
            df_corr = pd.DataFrame(correlations)
            return df_corr.sort_values('correlation', ascending=False).head(Config.TOP_N_SIMILAR)
        return pd.DataFrame()
        
    def _get_quarter_return(self, year: int, quarter: int) -> float:
        """Calcola rendimento totale di un trimestre"""
        try:
            data = self.get_quarter_data(year, quarter)
            if len(data) > 1:
                return ((data['adjusted_close'].iloc[-1] / 
                        data['adjusted_close'].iloc[0]) - 1) * 100
        except:
            pass
        return np.nan

# =====================================================
# FUNZIONI DI VISUALIZZAZIONE
# =====================================================
def create_yearly_comparison_chart(data: pd.DataFrame, ticker: str, 
                                  similar_years: pd.DataFrame) -> go.Figure:
    """Crea grafico confronto annuale"""
    fig = go.Figure()
    current_year = datetime.now().year
    
    # Linea anno corrente
    current_data = data[data.index.year == current_year].copy()
    current_data = current_data.reset_index()
    current_data['cum_return_pct'] = ((current_data['adjusted_close'] / 
                                       current_data['adjusted_close'].iloc[0]) - 1) * 100
    
    fig.add_trace(go.Scatter(
        x=current_data.index,
        y=current_data['cum_return_pct'],
        mode='lines',
        name=f'<b>{current_year} (Corrente)</b>',
        line=dict(color=Config.COLOR_CURRENT, width=4)
    ))
    
    # Linee anni simili
    if not similar_years.empty:
        for idx, row in similar_years.iterrows():
            year = int(row['year'])
            year_data = data[data.index.year == year].copy().reset_index()
            year_data['cum_return_pct'] = ((year_data['adjusted_close'] / 
                                           year_data['adjusted_close'].iloc[0]) - 1) * 100
            
            fig.add_trace(go.Scatter(
                x=year_data.index,
                y=year_data['cum_return_pct'],
                mode='lines',
                name=f"{year} (r={row['correlation']:.2f})",
                line=dict(color=Config.COLOR_SIMILAR[idx % len(Config.COLOR_SIMILAR)], 
                         width=2, dash='dash'),
                opacity=0.8
            ))
    
    fig.update_layout(
        title=f"<b>{ticker.upper()} - Confronto Annuale</b><br>Andamento YTD vs Anni Storici Simili",
        xaxis_title="Giorni di Trading dall'Inizio dell'Anno",
        yaxis_title="Rendimento Cumulativo (%)",
        template=Config.CHART_TEMPLATE,
        height=600,
        hovermode='x unified'
    )
    
    return fig

def create_quarterly_comparison_chart(data: pd.DataFrame, ticker: str, 
                                     similar_quarters: pd.DataFrame, matcher: PatternMatcher) -> go.Figure:
    """Crea grafico confronto trimestrale"""
    fig = go.Figure()
    current_year = datetime.now().year
    current_quarter = (datetime.now().month - 1) // 3 + 1
    
    # Linea trimestre corrente
    current_data = matcher.get_quarter_data(current_year, current_quarter).copy()
    if not current_data.empty:
        current_data = current_data.reset_index()
        current_data['quarter_return'] = ((current_data['adjusted_close'] / 
                                          current_data['adjusted_close'].iloc[0]) - 1) * 100
        
        fig.add_trace(go.Scatter(
            x=current_data.index,
            y=current_data['quarter_return'],
            mode='lines',
            name=f'<b>{current_year}-Q{current_quarter} (Corrente)</b>',
            line=dict(color=Config.COLOR_CURRENT, width=4)
        ))
    
    # Linee trimestri simili
    if not similar_quarters.empty:
        for idx, row in similar_quarters.iterrows():
            quarter_data = matcher.get_quarter_data(int(row['year']), int(row['quarter'])).copy()
            if not quarter_data.empty:
                quarter_data = quarter_data.reset_index()
                quarter_data['quarter_return'] = ((quarter_data['adjusted_close'] / 
                                                   quarter_data['adjusted_close'].iloc[0]) - 1) * 100
                
                fig.add_trace(go.Scatter(
                    x=quarter_data.index,
                    y=quarter_data['quarter_return'],
                    mode='lines',
                    name=f"{row['year_quarter']} (r={row['correlation']:.2f})",
                    line=dict(color=Config.COLOR_SIMILAR[idx % len(Config.COLOR_SIMILAR)], 
                             width=2, dash='dash'),
                    opacity=0.8
                ))
    
    fig.update_layout(
        title=f"<b>{ticker.upper()} - Confronto Trimestrale</b><br>Andamento QTD vs Trimestri Storici Simili",
        xaxis_title="Giorni di Trading dall'Inizio del Trimestre",
        yaxis_title="Rendimento Cumulativo Trimestrale (%)",
        template=Config.CHART_TEMPLATE,
        height=600,
        hovermode='x unified'
    )
    
    return fig

# =====================================================
# MAIN APP
# =====================================================
def main():
    st.title("📊 Kriterion Quant - Pattern Matching Analysis")
    st.markdown("**Analisi di correlazione per identificare anni e trimestri storici simili**")
    
    # Recupera subito la API key dai secrets (FUORI dal sidebar)
    try:
        api_key = st.secrets["EODHD_API_KEY"]
        api_status = "✅ Chiave API EODHD caricata con successo dai secrets."
    except:
        api_key = "YOUR_API_KEY_HERE"
        api_status = "⚠️ Chiave API EODHD non trovata nei secrets. Usando yfinance come fallback."
    
    # Sidebar per configurazione
    with st.sidebar:
        st.header("⚙️ Configurazione")
        
        # Input ticker
        ticker = st.text_input("Ticker", value="SPY", help="Es: SPY, QQQ, AAPL, ETH-USD")
        exchange = st.selectbox("Exchange", ["US", "CC", "FOREX"], 
                               help="US per azioni, CC per crypto, FOREX per forex")
        
        # Parametri di analisi
        st.subheader("📈 Parametri Analisi")
        min_correlation = st.slider("Correlazione Minima", 0.5, 0.95, 0.70, 0.05,
                                   help="Soglia minima per considerare un periodo simile")
        top_n = st.slider("Top N Simili", 3, 10, 5,
                         help="Numero massimo di periodi simili da visualizzare")
        
        # Aggiorna configurazione
        Config.MIN_CORRELATION = min_correlation
        Config.TOP_N_SIMILAR = top_n
        
        # Info API (solo mostra lo status)
        st.subheader("🔑 API Configuration")
        if api_key != "YOUR_API_KEY_HERE":
            st.success(api_status)
        else:
            st.warning(api_status)
    
    # Carica dati
    with st.spinner(f"Caricamento dati per {ticker}..."):
        data = fetch_data(ticker, exchange, Config.START_DATE, api_key)  # PASSA api_key qui!
    
    if data.empty:
        st.error("Impossibile caricare i dati. Verifica ticker e connessione.")
        return
    
    # Inizializza pattern matcher
    matcher = PatternMatcher(data)
    
    # Trova periodi simili
    current_quarter = (datetime.now().month - 1) // 3 + 1
    
    with st.spinner("Analisi pattern in corso..."):
        similar_years = matcher.find_similar_years(Config.CURRENT_YEAR, Config.MIN_CORRELATION)
        similar_quarters = matcher.find_similar_quarters(Config.CURRENT_YEAR, current_quarter, 
                                                        Config.MIN_CORRELATION)
    
    # Layout a tabs
    tab1, tab2, tab3 = st.tabs(["📅 Analisi Annuale", "📊 Analisi Trimestrale", "📈 Dati Storici"])
    
    # Tab 1: Analisi Annuale
    with tab1:
        st.markdown("""
        <div class="didactic">
            <p><strong>💡 Spunto Operativo (Annuale):</strong></p>
            <p>Questo grafico confronta l'andamento YTD dell'anno corrente (linea verde) con gli anni storici più simili. 
            Osserva come si sono comportati gli anni analoghi <strong>dopo</strong> il punto in cui ci troviamo oggi. 
            Una tendenza comune può suggerire uno scenario probabilistico per i mesi a venire.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not similar_years.empty:
            # Grafico
            yearly_chart = create_yearly_comparison_chart(data, ticker, similar_years)
            st.plotly_chart(yearly_chart, use_container_width=True)
            
            # Tabella riepilogativa
            st.subheader("📈 Dettaglio Anni Più Simili")
            
            # Formatta la tabella
            display_df = similar_years.copy()
            display_df['correlation'] = display_df['correlation'].apply(lambda x: f"{x:.3f}")
            display_df['ytd_return_at_similar_point'] = display_df['ytd_return_at_similar_point'].apply(
                lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A"
            )
            display_df['year_return'] = display_df['year_return'].apply(
                lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A"
            )
            display_df.columns = ['Anno', 'Correlazione', 'Rendimento Finale', 'YTD al Punto Simile']
            
            st.dataframe(display_df, use_container_width=True)
            
            # Statistiche con stile personalizzato
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_corr = similar_years['correlation'].mean()
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Correlazione Media</p>
                    <p style='color: #00ff00; margin: 5px 0; font-size: 24px; font-weight: bold;'>{avg_corr:.3f}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                avg_return = similar_years['year_return'].mean()
                color = "#00ff00" if avg_return > 0 else "#ff4444"
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Rendimento Medio Anni Simili</p>
                    <p style='color: {color}; margin: 5px 0; font-size: 24px; font-weight: bold;'>{avg_return:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                positive_years = (similar_years['year_return'] > 0).sum()
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Anni Positivi</p>
                    <p style='color: #00ff00; margin: 5px 0; font-size: 24px; font-weight: bold;'>{positive_years}/{len(similar_years)}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Nessun anno trovato con correlazione > {Config.MIN_CORRELATION:.2f}")
    
    # Tab 2: Analisi Trimestrale
    with tab2:
        st.markdown("""
        <div class="didactic">
            <p><strong>💡 Spunto Operativo (Trimestrale):</strong></p>
            <p>Analisi più tattica focalizzata sul trimestre corrente. È utile per identificare pattern stagionali 
            e potenziali dinamiche di prezzo nel breve-medio termine. Confronta la traiettoria attuale con quelle 
            dei trimestri storici più correlati.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not similar_quarters.empty:
            # Grafico
            quarterly_chart = create_quarterly_comparison_chart(data, ticker, similar_quarters, matcher)
            st.plotly_chart(quarterly_chart, use_container_width=True)
            
            # Tabella riepilogativa
            st.subheader(f"📊 Dettaglio Trimestri Più Simili a Q{current_quarter} {Config.CURRENT_YEAR}")
            
            # Formatta la tabella
            display_df_q = similar_quarters.copy()
            display_df_q['correlation'] = display_df_q['correlation'].apply(lambda x: f"{x:.3f}")
            display_df_q['quarter_return'] = display_df_q['quarter_return'].apply(
                lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A"
            )
            display_df_q = display_df_q[['year_quarter', 'correlation', 'quarter_return']]
            display_df_q.columns = ['Trimestre', 'Correlazione', 'Rendimento Trimestre']
            
            st.dataframe(display_df_q, use_container_width=True)
            
            # Statistiche con stile personalizzato
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_corr_q = similar_quarters['correlation'].mean()
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Correlazione Media</p>
                    <p style='color: #00ff00; margin: 5px 0; font-size: 24px; font-weight: bold;'>{avg_corr_q:.3f}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                avg_return_q = similar_quarters['quarter_return'].mean()
                color = "#00ff00" if avg_return_q > 0 else "#ff4444"
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Rendimento Medio Trimestri</p>
                    <p style='color: {color}; margin: 5px 0; font-size: 24px; font-weight: bold;'>{avg_return_q:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                positive_quarters = (similar_quarters['quarter_return'] > 0).sum()
                st.markdown(f"""
                <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                    <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Trimestri Positivi</p>
                    <p style='color: #00ff00; margin: 5px 0; font-size: 24px; font-weight: bold;'>{positive_quarters}/{len(similar_quarters)}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Nessun trimestre trovato con correlazione > {Config.MIN_CORRELATION:.2f}")
    
    # Tab 3: Dati Storici
    with tab3:
        st.subheader("📈 Panoramica Dati Storici")
        
        # Statistiche generali con stile personalizzato
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Periodo Dati</p>
                <p style='color: #fafafa; margin: 5px 0; font-size: 20px; font-weight: bold;'>{data.index[0].year}-{data.index[-1].year}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Giorni Trading</p>
                <p style='color: #fafafa; margin: 5px 0; font-size: 20px; font-weight: bold;'>{len(data):,}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            current_price = data['adjusted_close'].iloc[-1]
            st.markdown(f"""
            <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>Prezzo Attuale</p>
                <p style='color: #fafafa; margin: 5px 0; font-size: 20px; font-weight: bold;'>${current_price:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            ytd_data = data[data.index.year == Config.CURRENT_YEAR]
            if len(ytd_data) > 0:
                ytd_return = ((ytd_data['adjusted_close'].iloc[-1] / 
                              ytd_data['adjusted_close'].iloc[0]) - 1) * 100
                color = "#00ff00" if ytd_return > 0 else "#ff4444"
            else:
                ytd_return = 0
                color = "#fafafa"
            st.markdown(f"""
            <div style='background-color: #262730; padding: 15px; border-radius: 5px; border: 1px solid #4a4a4a;'>
                <p style='color: #b0b0b0; margin: 0; font-size: 14px;'>YTD Return</p>
                <p style='color: {color}; margin: 5px 0; font-size: 20px; font-weight: bold;'>{ytd_return:.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Grafico storico completo
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=data.index,
            y=data['adjusted_close'],
            mode='lines',
            name='Prezzo Chiusura Adjusted',
            line=dict(color='#4ecdc4', width=1)
        ))
        fig_hist.update_layout(
            title=f"<b>{ticker.upper()} - Serie Storica Completa</b>",
            xaxis_title="Data",
            yaxis_title="Prezzo ($)",
            template=Config.CHART_TEMPLATE,
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Ultimi dati
        st.subheader("Ultimi 10 Giorni")
        recent_data = data.tail(10)[['adjusted_close', 'returns']].copy()
        recent_data['returns'] = (recent_data['returns'] * 100).apply(lambda x: f"{x:.2f}%")
        recent_data['adjusted_close'] = recent_data['adjusted_close'].apply(lambda x: f"${x:.2f}")
        recent_data.columns = ['Prezzo Adjusted', 'Rendimento Giornaliero']
        st.dataframe(recent_data, use_container_width=True)

if __name__ == "__main__":
    main()
