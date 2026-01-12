from flask import Flask, render_template, request, session, make_response, url_for, redirect
import pandas as pd
import numpy as np
from scipy import stats
import uuid
import io
import hashlib
import os
import tempfile
import subprocess
import sys

# -------------------------------------------------------------------------
# AUTO-INSTALACJA BRAKUJĄCYCH PAKIETÓW
# -------------------------------------------------------------------------
def ensure_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"⚠️ Brak pakietu '{package_name}'. Próba automatycznej instalacji...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ Pomyślnie zainstalowano '{package_name}'.")
            return True
        except Exception as e:
            print(f"❌ Błąd instalacji '{package_name}': {e}")
            return False

# Konfiguracja Statsmodels
HAS_STATSMODELS = False
if ensure_package('statsmodels'):
    try:
        from statsmodels.stats.diagnostic import lilliefors
        HAS_STATSMODELS = True
    except ImportError:
        print("OSTRZEŻENIE: Zainstalowano statsmodels, ale import lilliefors nie powiódł się.")

# Konfiguracja Pyreadstat
HAS_PYREADSTAT = ensure_package('pyreadstat')

app = Flask(__name__)
app.secret_key = 'bardzo_tajny_klucz_moodle_securit_key'

ADMIN_PASSWORD = "1234"

# -------------------------------------------------------------------------
# 1. FUNKCJA GENERUJĄCA DANE
# -------------------------------------------------------------------------
def generuj_dane_studenta(user_id, n=100):
    seed_hex = hashlib.md5(str(user_id).encode('utf-8')).hexdigest()
    seed = int(seed_hex, 16) % (2**32)
    np.random.seed(seed)
    
    mean = [12, 12, 12, 13, 14] 
    cov_matrix = [
        [1.0, -0.6, 0.5, 0.3, 0.1],    
        [-0.6, 1.0, -0.4, -0.1, -0.2], 
        [0.5, -0.4, 1.0, 0.2, 0.2],    
        [0.3, -0.1, 0.2, 1.0, 0.3],    
        [0.1, -0.2, 0.2, 0.3, 1.0]     
    ]
    sd = 3.5
    cov_matrix = np.array(cov_matrix) * (sd ** 2)
    data = np.random.multivariate_normal(mean, cov_matrix, size=n)
    data = np.rint(data).astype(int)
    data = np.clip(data, 5, 20)
    
    df = pd.DataFrame(data, columns=['Ekstrawersja', 'Neurotyzm', 'Otwartosc', 'Ugodowosc', 'Sumiennosc'])
    return df

# -------------------------------------------------------------------------
# 2. FUNKCJE POMOCNICZE
# -------------------------------------------------------------------------
def ocen_sile(r):
    abs_r = abs(r)
    if abs_r < 0.1: return "brak"
    if abs_r < 0.3: return "słaby"
    if abs_r < 0.5: return "umiarkowany"
    return "silny"

def ocen_kierunek(r):
    if abs(r) < 0.1: return "związku"
    return "pozytywny" if r > 0 else "negatywny"

def format_r_z_gwiazdkami(r, p):
    stars = ""
    if p < 0.001: stars = "***"
    elif p < 0.01: stars = "**"
    elif p < 0.05: stars = "*"
    return f"{r:.2f}{stars}".replace('.', ',')

PREFIX_MAP = {
    'Ekstrawersja': 'ekstra',
    'Neurotyzm': 'neuro',
    'Otwartosc': 'otwar',
    'Ugodowosc': 'ugoda',
    'Sumiennosc': 'sumien'
}

def oblicz_poprawne_statystyki(df):
    klucz = {}
    
    # 1. Statystyki opisowe
    for col_name, prefix in PREFIX_MAP.items():
        series = df[col_name]
        klucz[f'{prefix}_m'] = series.mean()
        klucz[f'{prefix}_mdn'] = series.median()
        klucz[f'{prefix}_sd'] = series.std()
        klucz[f'{prefix}_sk'] = series.skew()
        klucz[f'{prefix}_kurt'] = series.kurt()
        klucz[f'{prefix}_min'] = series.min()
        klucz[f'{prefix}_max'] = series.max()
        
        # Obliczanie testu normalności
        if HAS_STATSMODELS:
            d_stat, p_val = lilliefors(series, dist='norm')
        else:
            # Fallback jeśli instalacja się nie udała
            z_score = (series - series.mean()) / series.std()
            d_stat, p_val = stats.kstest(z_score, 'norm')
            
        klucz[f'{prefix}_d'] = d_stat
        klucz[f'{prefix}_p'] = p_val

    # 2. Założenia
    if klucz['neuro_p'] < 0.05:
        klucz['rozklad_typ'] = 'niespełnienie'
        klucz['korelacja_typ'] = 'rho-Spearmana'
    else:
        klucz['rozklad_typ'] = 'spełnienie'
        klucz['korelacja_typ'] = 'r-Pearsona'

    # 3. Korelacje
    vars_list = ['Ekstrawersja', 'Neurotyzm', 'Otwartosc', 'Ugodowosc', 'Sumiennosc']
    rho, p_matrix = stats.spearmanr(df[vars_list])
    idx = {name: i for i, name in enumerate(vars_list)}
    
    def get_rp(v1, v2):
        i, j = idx[v1], idx[v2]
        return rho[i, j], p_matrix[i, j]

    r, p = get_rp('Neurotyzm', 'Ekstrawersja')
    klucz['corr_neuro_ekstra'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Otwartosc', 'Ekstrawersja')
    klucz['corr_otwar_ekstra'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Otwartosc', 'Neurotyzm')
    klucz['corr_otwar_neuro'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Ugodowosc', 'Ekstrawersja')
    klucz['corr_ugoda_ekstra'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Ugodowosc', 'Neurotyzm')
    klucz['corr_ugoda_neuro'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Ugodowosc', 'Otwartosc')
    klucz['corr_ugoda_otwar'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Sumiennosc', 'Ekstrawersja')
    klucz['corr_sumien_ekstra'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Sumiennosc', 'Neurotyzm')
    klucz['corr_sumien_neuro'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Sumiennosc', 'Otwartosc')
    klucz['corr_sumien_otwar'] = format_r_z_gwiazdkami(r, p)
    
    r, p = get_rp('Sumiennosc', 'Ugodowosc')
    klucz['corr_sumien_ugoda'] = format_r_z_gwiazdkami(r, p)

    # 4. Hipotezy
    r_ne, p_ne = get_rp('Neurotyzm', 'Ekstrawersja')
    klucz['h1_sila'] = ocen_sile(r_ne)
    klucz['h1_kierunek'] = ocen_kierunek(r_ne)
    klucz['h1_decyzja'] = 'potwierdza' if (p_ne < 0.05 and r_ne < 0) else 'nie potwierdza'

    r_oe, p_oe = get_rp('Otwartosc', 'Ekstrawersja')
    klucz['h2_sila'] = ocen_sile(r_oe)
    klucz['h2_kierunek'] = ocen_kierunek(r_oe)
    klucz['h2_decyzja'] = 'potwierdza' if (p_oe < 0.05 and r_oe > 0) else 'nie potwierdza'

    r_on, p_on = get_rp('Otwartosc', 'Neurotyzm')
    klucz['h3_sila'] = ocen_sile(r_on)
    klucz['h3_kierunek'] = ocen_kierunek(r_on)
    klucz['h3_decyzja'] = 'potwierdza' if (p_on < 0.05 and r_on < 0) else 'nie potwierdza'

    r_ue, p_ue = get_rp('Ugodowosc', 'Ekstrawersja')
    klucz['h4_sila'] = ocen_sile(r_ue)
    klucz['h4_kierunek'] = ocen_kierunek(r_ue)
    if abs(r_ue) < 0.1 or p_ue >= 0.05:
         klucz['h4_decyzja'] = 'nie potwierdza'
    else:
         klucz['h4_decyzja'] = 'potwierdza' if r_ue > 0 else 'nie potwierdza'

    return klucz

# -------------------------------------------------------------------------
# 3. TRASY APLIKACJI
# -------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        manual_id = request.form.get('manual_id')
        if manual_id:
            session['user_id'] = manual_id.strip()
            return redirect(url_for('index', **request.args))

    user_id_from_url = request.args.get('user_id')
    if user_id_from_url:
        session['user_id'] = user_id_from_url
    elif 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    
    user_id = session['user_id']
    
    df = generuj_dane_studenta(user_id)
    answers = oblicz_poprawne_statystyki(df)
    
    return render_template('index.html', user_id=user_id, answers=answers)

@app.route('/pobierz_csv')
def pobierz_csv():
    if 'user_id' not in session: return redirect(url_for('index'))
    user_id = session['user_id']
    df = generuj_dane_studenta(user_id)
    output = io.BytesIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8')
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=dane_{user_id}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/pobierz_sav')
def pobierz_sav():
    if 'user_id' not in session: return redirect(url_for('index'))
    
    # Podwójne sprawdzenie przy żądaniu, w razie gdyby instalacja zadziałała później
    global HAS_PYREADSTAT
    if not HAS_PYREADSTAT:
        HAS_PYREADSTAT = ensure_package('pyreadstat')

    if not HAS_PYREADSTAT:
        return "Błąd: Nie udało się zainstalować biblioteki 'pyreadstat'. Sprawdź logi serwera.", 500

    user_id = session['user_id']
    df = generuj_dane_studenta(user_id)
    
    # Zapis do pliku tymczasowego
    fd, path = tempfile.mkstemp(suffix='.sav')
    try:
        os.close(fd) 
        import pyreadstat
        pyreadstat.write_sav(df, path)
        
        with open(path, 'rb') as f:
            data = f.read()
            
        output = io.BytesIO(data)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=dane_{user_id}.sav"
        response.headers["Content-type"] = "application/x-spss-sav"
        return response
    except Exception as e:
        return f"Wystąpił błąd podczas generowania pliku SAV: {e}", 500
    finally:
        if os.path.exists(path):
            os.remove(path)

@app.route('/sprawdz', methods=['GET', 'POST'])
def sprawdz():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
    