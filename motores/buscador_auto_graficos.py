# -*- coding: utf-8 -*-
"""
Buscador automático – Ojo de Zeus 2 (DUAL DRIVER + outcomes + extracción + heurística)
– Ejecuta TODOS los métodos guardados en sitios.json (sin preguntar).
– Navegador real si hay GUI: Firefox → fallback Chromium; si no, HTTP.
– Si la decisión por métodos queda Indeterminado, aplica una HEURÍSTICA de existencia
  (TikTok/Pinterest + genérica) usando el HTML más completo capturado.
– Extrae info útil (título, canonical, descripción, OG, conteos) cuando decide Existe.
"""

import os, re, json, time, random, platform, shutil
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# ===== Colores =====
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    GREEN=Fore.GREEN; RED=Fore.RED; YELLOW=Fore.YELLOW; CYAN=Fore.CYAN; MAG=Fore.MAGENTA; BLUE=Fore.BLUE
    BOLD=Style.BRIGHT; RESET=Style.RESET_ALL
    OK=GREEN+"✓"+RESET; BAD=RED+"✗"+RESET; WARN=YELLOW+"!"+RESET
except Exception:
    class _NC: 
        def __getattr__(self,_): return ""
    GREEN=RED=YELLOW=CYAN=MAG=BLUE=BOLD=RESET=_NC()
    OK="✓"; BAD="✗"; WARN="!"

def log(evento:str, detalle:str): print(f"{CYAN}[{evento}]{RESET} {detalle}", flush=True)
def log_exc(prefix:str, e:Exception): print(f"{RED}[ERROR]{RESET} {prefix}: {e}", flush=True)

# ===== HTTP =====
HTTP_BACKEND="httpx"
try:
    import httpx
except Exception:
    HTTP_BACKEND="requests"
    import requests  # type: ignore

def rand_ua()->str:
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",
    ])

JSON_CT=("application/json","application/ld+json","application/vnd.api+json")
CAPTCHA_MARKERS=["captcha","cf-challenge","hcaptcha","g-recaptcha","cloudflare","attention required!","/cdn-cgi/challenge-platform","are you a human","just a moment..."]

@dataclass
class Resp:
    url:str; final_url:str; status:int; headers:Dict[str,str]; text:str; is_json:bool; json_obj:Any=None; via:str="http"; took_ms:int=0

def fetch_http(url:str, timeout:float=16.0, follow_redirects:bool=True)->Resp:
    t0=int(time.time()*1000)
    headers={"User-Agent":rand_ua(),"Accept":"*/*","Accept-Language":"es-MX,es;q=0.9,en;q=0.8","Cache-Control":"no-cache","Pragma":"no-cache"}
    final_url=url; status=0; resp_headers={}; text=""; is_json=False; jobj=None
    try:
        if HTTP_BACKEND=="httpx":
            with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, verify=True) as c:
                r=c.get(url); final_url=str(r.url); status=r.status_code; resp_headers={k.lower():v for k,v in r.headers.items()}; text=r.text or ""
        else:
            r=requests.get(url, headers=headers, allow_redirects=follow_redirects, timeout=timeout)
            final_url=r.url; status=r.status_code; resp_headers={k.lower():v for k,v in r.headers.items()}; text=r.text or ""
        ct=resp_headers.get("content-type","").split(";")[0].strip().lower()
        if ct in JSON_CT:
            try: jobj=json.loads(text); is_json=True
            except Exception: is_json=False
    except Exception as e:
        text=f"[HTTP_ERROR] {e}"; status=-1
    took=int(time.time()*1000)-t0
    return Resp(url, final_url, status, resp_headers, text, is_json, jobj, "http", took)

# ===== Selenium DUAL (Firefox → Chromium) =====
SELENIUM_OK=False
try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_OK=True
except Exception:
    SELENIUM_OK=False

DEFAULT_PATHS = {
    "geckodriver": ["/usr/local/bin/geckodriver", "/usr/bin/geckodriver"],
    "firefox": ["/usr/bin/firefox-esr", "/usr/bin/firefox"],
    "chromedriver": ["/usr/bin/chromedriver"],
    "chromium": ["/usr/bin/chromium", "/usr/bin/chromium-browser"],
}

def which_any(paths: List[str]) -> Optional[str]:
    import shutil
    for p in paths:
        if os.path.isfile(p) and os.access(p, os.X_OK): return p
    for p in paths:
        w = shutil.which(os.path.basename(p))
        if w: return w
    return None

def has_display()->bool:
    if platform.system().lower()=="linux": return bool(os.environ.get("DISPLAY"))
    return True

SELENIUM_PAGELOAD_TIMEOUT=35
DOM_READY_MAX_WAIT=12
URL_STABILIZE_WINDOW_MS=700
URL_STABILIZE_MAX_MS=8000
POST_LOAD_SETTLE_MS=450

def _wait_dom_complete(driver, max_wait_s:int)->None:
    WebDriverWait(driver, max_wait_s).until(lambda d: d.execute_script("return document.readyState")=="complete")

def _stabilize_url(driver, window_ms:int, max_ms:int)->str:
    start=time.time()*1000; last=driver.current_url; stable_since=start
    while True:
        time.sleep(0.12); cur=driver.current_url; now=time.time()*1000
        if cur!=last: last=cur; stable_since=now
        if (now-stable_since)>=window_ms: return cur
        if (now-start)>=max_ms: return cur

def get_webdriver()->Tuple[Optional[str], Optional["webdriver.Remote"]]:
    if not (SELENIUM_OK and has_display()):
        return (None, None)
    # Firefox
    try:
        from selenium.webdriver.firefox.service import Service as FxService
        from selenium.webdriver.firefox.options import Options as FxOptions
        gecko=which_any(DEFAULT_PATHS["geckodriver"])
        fxbin=which_any(DEFAULT_PATHS["firefox"])
        if gecko and fxbin:
            opts=FxOptions(); opts.binary_location=fxbin
            svc=FxService(executable_path=gecko)
            drv=webdriver.Firefox(service=svc, options=opts)
            log("NAVEGADOR", f"Firefox → {fxbin} + {gecko}")
            return ("firefox", drv)
    except Exception as e:
        log("AVISO", f"Firefox no disponible ({e}). Probando Chromium…")
    # Chromium
    try:
        from selenium.webdriver.chrome.service import Service as ChService
        from selenium.webdriver.chrome.options import Options as ChOptions
        chd=which_any(DEFAULT_PATHS["chromedriver"])
        chbin=which_any(DEFAULT_PATHS["chromium"])
        if chd and chbin:
            opts=ChOptions(); opts.binary_location=chbin
            svc=ChService(executable_path=chd)
            drv=webdriver.Chrome(service=svc, options=opts)
            log("NAVEGADOR", f"Chromium → {chbin} + {chd}")
            return ("chromium", drv)
    except Exception as e:
        log("AVISO", f"Chromium no disponible ({e}).")
    return (None, None)

def selenium_fetch(url:str)->Optional[Resp]:
    name, drv = get_webdriver()
    if not drv: return None
    try:
        print(f"{MAG}{BOLD}→ Abriendo navegador real ({name}) para: {url}{RESET}")
        try: drv.set_page_load_timeout(SELENIUM_PAGELOAD_TIMEOUT)
        except Exception: pass
        t0=int(time.time()*1000)
        drv.get(url)
        try: _wait_dom_complete(drv, DOM_READY_MAX_WAIT)
        except Exception: pass
        final=_stabilize_url(drv, URL_STABILIZE_WINDOW_MS, URL_STABILIZE_MAX_MS)
        time.sleep(POST_LOAD_SETTLE_MS/1000.0)
        html=drv.page_source or ""; took=int(time.time()*1000)-t0
        return Resp(url, final, 200, {"via":name}, html, False, None, name, took)
    except Exception as e:
        log_exc("selenium_fetch", e); return None
    finally:
        try: drv.quit()
        except Exception: pass

# ===== sitios.json =====
def cargar_sitios(path:str="sitios.json")->List[Dict[str,Any]]:
    try:
        with open(path,"r",encoding="utf-8") as f:
            d=json.load(f)
            if isinstance(d,list): return d
    except Exception as e:
        log_exc("cargar_sitios", e)
    return []

# ===== outcomes =====
def _final_url_from_resp(r_http:Resp, r_sel:Optional[Resp])->str:
    if r_sel and r_sel.final_url: return r_sel.final_url
    return r_http.final_url

def method_outcome_signature(metodo:str, params:Dict[str,Any], r_http:Resp, r_sel:Optional[Resp])->Optional[str]:
    try:
        if metodo=="status_code": return f"status={r_http.status}"
        elif metodo in ("url_check","redirect_check"): return f"final_url={_final_url_from_resp(r_http, r_sel)}"
        elif metodo=="status_code_y_texto":
            code=params.get("codigo"); keys=[k.lower() for k in params.get("debe_contener",[])]
            txt=(r_sel.text if (r_sel and len(r_sel.text)>len(r_http.text)) else r_http.text).lower()
            hit=(r_http.status==code) and all(k in txt for k in keys[:5])
            return f"status_text_hit={bool(hit)}"
        elif metodo=="html_contains":
            keys=[k.lower() for k in params.get("claves",[])]
            txt=(r_sel.text if (r_sel and len(r_sel.text)>len(r_http.text)) else r_http.text).lower()
            hit=all(k in txt for k in keys[:5]) if keys else False
            return f"html_hit={bool(hit)}"
        elif metodo=="json_response_check":
            if r_http.is_json and isinstance(r_http.json_obj, dict):
                keys=params.get("claves_presentes",[])
                hit=all(k in r_http.json_obj for k in keys[:5])
                return f"json_hit={bool(hit)}"
            return "json_hit=False"
        elif metodo=="captcha_detect":
            txt=(r_sel.text if (r_sel and len(r_sel.text)>len(r_http.text)) else r_http.text)
            return f"captcha={'true' if any(m in txt.lower() for m in CAPTCHA_MARKERS) else 'false'}"
        elif metodo=="palabras_clave":
            keys=[k.lower() for k in params.get("claves",[])]
            txt=(r_sel.text if (r_sel and len(r_sel.text)>len(r_http.text)) else r_http.text).lower()
            hit=any(k in txt for k in keys)
            return f"kw_hit={bool(hit)}"
        elif metodo=="custom_selector_check":
            return f"dom_loaded={bool(r_sel)}"
    except Exception:
        return None
    return None

def evaluar_metodo(url_base:str, usuario:str, metodo:str, params:Dict[str,Any], use_browser:bool)->Tuple[str, Dict[str,Any], Resp, Optional[Resp]]:
    url=url_base.replace("{user}",usuario).replace("{usuario}",usuario)
    r_sel=selenium_fetch(url) if use_browser else None
    r_http=fetch_http(url)
    outcome=method_outcome_signature(metodo, params, r_http, r_sel)
    meta={"final_url": _final_url_from_resp(r_http, r_sel), "status": r_http.status, "via": (r_sel.via if r_sel else "http")}
    return (outcome or "None"), meta, r_http, r_sel

def decidir_por_outcome(outcome:str, outcomes_real:List[str], outcomes_fake:List[str])->str:
    r = outcome in outcomes_real
    f = outcome in outcomes_fake
    if r and not f: return "Existe"
    if f and not r: return "No existe"
    return "Indeterminado"

# ===== extracción y heurística =====
def _rg(pat:str, text:str, flags=re.I|re.S) -> Optional[str]:
    m=re.search(pat, text, flags); return m.group(1).strip() if m else None
def _rg_all(pat:str, text:str, flags=re.I|re.S) -> List[str]:
    return [g.strip() for g in re.findall(pat, text, flags)]

def extraer_info_relevante(html:str, final_url:str)->Dict[str,Any]:
    info:Dict[str,Any] = {"final_url":final_url}
    ttl = _rg(r"<title[^>]*>(.*?)</title>", html)
    if ttl: info["titulo"]=re.sub(r"\s+"," ", ttl)
    canon = _rg(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html)
    if canon: info["canonical"]=canon
    desc = _rg(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html)
    if desc: info["descripcion"]=desc
    og_title = _rg(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html)
    og_desc  = _rg(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html)
    og_image = _rg(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
    if og_title: info["og:title"]=og_title
    if og_desc:  info["og:description"]=og_desc
    if og_image: info["og:image"]=og_image

    text_plain = re.sub(r"<[^>]+>"," ", html, flags=re.S)
    text_plain = re.sub(r"\s+"," ", text_plain)

    pats = {
        "seguidores": r"(\d[\d\.,]*\s*(?:k|m|millones|mil)?)(?:\s+)?(?:seguidores|followers)",
        "siguiendo":  r"(\d[\d\.,]*\s*(?:k|m|millones|mil)?)(?:\s+)?(?:siguiendo|following)",
        "publicaciones": r"(\d[\d\.,]*\s*(?:k|m|millones|mil)?)(?:\s+)?(?:publicaciones|posts|pins)",
        "likes": r"(\d[\d\.,]*\s*(?:k|m|millones|mil)?)(?:\s+)?(?:me gusta|likes)"
    }
    for k,pat in pats.items():
        m=_rg(pat, text_plain, flags=re.I)
        if m: info[k]=m

    uname = _rg(r"@([A-Za-z0-9_.-]{3,})", text_plain)
    if uname: info["usuario_detectado"]=uname
    return info

def heuristica_existe(user:str, final_url:str, html:str)->str:
    u=user.lower()
    host = ""
    try:
        host = re.search(r"https?://([^/]+)/", final_url).group(1).lower()
    except Exception:
        pass

    # Normaliza texto
    plain = re.sub(r"<[^>]+>"," ", html, flags=re.S)
    plain = re.sub(r"\s+"," ", plain).lower()

    # TikTok
    if "tiktok.com" in (host or ""):
        # Señales de perfil presente
        if (f"@{u}" in plain) or ('uniqueid":"' in html.lower()) or ("og:url" in html.lower() and f"@{u}" in html.lower()):
            return "Existe"

    # Pinterest
    if "pinterest.com" in (host or ""):
        if 'property="og:type" content="profile"' in html.lower() or "profile" in plain:
            # Si aparece el usuario en la URL final y hay título/OG, lo damos como existe
            if u in final_url.lower() or f"{u}" in plain:
                return "Existe"

    # Genérica: si título, canonical y alguna métrica aparecen junto con el usuario
    ttl = _rg(r"<title[^>]*>(.*?)</title>", html) or ""
    if u in (ttl.lower()+plain):
        if any(k in plain for k in ["followers","seguidores","following","siguiendo","posts","publicaciones","likes","me gusta"]):
            return "Existe"

    return "Indeterminado"

# ===== UI =====
def run_terminal():
    print(f"{BOLD}🔍 Buscador (auto, con outcomes) — Ojo de Zeus 2{RESET}")
    print("=======================================================")
    user=input(f"{BOLD}🧑‍💻 Ingresa el usuario/correo a verificar:{RESET} ").strip()
    if not user:
        print(f"{YELLOW}No ingresaste usuario/correo.{RESET}"); return

    sitios=cargar_sitios()
    if not sitios:
        print(f"{RED}No encontré sitios.json o está vacío.{RESET}"); return

    # Navegador real disponible
    if SELENIUM_OK and has_display():
        name, inst = get_webdriver()
        if inst:
            try: inst.quit()
            except Exception: pass
            use_browser=True
            print(f"{OK} Entorno gráfico con navegador real disponible ({BOLD}{name}{RESET}).")
        else:
            use_browser=False
            print(f"{WARN} No se pudo iniciar Firefox ni Chromium. Usaré {BOLD}HTTP{RESET}.")
    else:
        use_browser=False
        print(f"{WARN} Sin entorno gráfico/Selenium. Usaré {BOLD}HTTP{RESET}.")

    # Agrupar por nombre de sitio
    sitios_por_nombre:Dict[str,List[Dict[str,Any]]]={}
    for s in sitios:
        n=s.get("nombre","general")
        sitios_por_nombre.setdefault(n,[]).append(s)

    extracted_blocks: List[str] = []
    for nombre, metodos in sitios_por_nombre.items():
        print(f"\n{MAG}{BOLD}===============  {nombre}  ==============={RESET}\n")
        if not metodos:
            print(f"{YELLOW}Sin métodos para este sitio.{RESET}")
            continue

        any_exist=False; any_no=False
        resultados=[]
        best_html=""; best_final="-"; best_len=0

        for m in metodos:
            metodo=m.get("metodo","?")
            params=m.get("parametros",{})
            url_base=m.get("url_base","")
            if "{user}" not in url_base and "{usuario}" not in url_base:
                resultados.append(("Indeterminado", metodo, "[URL base sin {user}/{usuario}]", url_base))
                continue
            try:
                outcome, meta, r_http, r_sel = evaluar_metodo(url_base, user, metodo, params, use_browser)
                decision = decidir_por_outcome(outcome, m.get("outcomes_real",[]), m.get("outcomes_fake",[]))
                if decision=="Existe": any_exist=True
                if decision=="No existe": any_no=True
                resultados.append((decision, metodo, outcome, meta.get("final_url","-")))
                cand_html = (r_sel.text if (r_sel and len(r_sel.text)>len(r_http.text)) else r_http.text) or ""
                if (r_sel is not None) or (len(cand_html) > best_len):
                    best_html = cand_html; best_final = meta.get("final_url","-"); best_len = len(cand_html)
            except Exception as e:
                resultados.append(("Indeterminado", metodo, f"[error:{e}]", "-"))

        # Mostrar resultados por método
        for decision, metodo, outcome, final_url in resultados:
            color = GREEN if decision=="Existe" else RED if decision=="No existe" else YELLOW
            print(f"  → {color}{decision}{RESET}  | {metodo:22s} | outcome: {outcome} | final: {final_url}")

        # Decisión agregada por sitio (por outcomes)
        if any_no:
            final = "No existe"
        elif any_exist:
            final = "Existe"
        else:
            final = "Indeterminado"

        # HEURÍSTICA si quedó Indeterminado y tenemos HTML bueno
        heur_used=False
        if final=="Indeterminado" and best_html:
            heur = heuristica_existe(user, best_final, best_html)
            if heur != "Indeterminado":
                final = heur
                heur_used=True

        agg_color = GREEN if final=="Existe" else RED if final=="No existe" else YELLOW
        extra_tag = f" {YELLOW}(heurística){RESET}" if heur_used else ""
        print(f"\n📌 Decisión para {nombre}: {agg_color}{BOLD}{final}{RESET}{extra_tag}")

        # Extracción si existe
        if final=="Existe" and best_html:
            print(f"\n{BLUE}{BOLD}→ Extrayendo información relevante…{RESET}")
            info = extraer_info_relevante(best_html, best_final)
            for k in ["final_url","canonical","titulo","descripcion","og:title","og:description","og:image","usuario_detectado","seguidores","siguiendo","publicaciones","likes"]:
                if k in info:
                    print(f"   {CYAN}{k:18s}{RESET}: {info[k]}")
            block = f"[{nombre}] EXISTE\n" + "\n".join([f"{k}: {v}" for k,v in info.items()])
            extracted_blocks.append(block)

    print("\n🔚 Búsqueda finalizada.")
    ans=input("\n¿Guardar reporte .txt? (s/n): ").strip().lower()
    if ans=="s":
        ts=time.strftime("%Y%m%d_%H%M%S"); fname=f"busqueda_{user}_{ts}.txt"
        with open(fname,"w",encoding="utf-8") as f:
            f.write(f"Reporte de búsqueda — {user}\nFecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            for nombre, metodos in sitios_por_nombre.items():
                f.write(f"\n[{nombre}]\n")
                for i,m in enumerate(metodos, start=1):
                    f.write(f" - {i:02d} {m.get('metodo','?')}\n")
            if extracted_blocks:
                f.write("\n\n=== EXTRACCIONES ===\n")
                for b in extracted_blocks:
                    f.write("\n"+b+"\n")
        print(f"{OK} Reporte guardado: {fname}")

# ===== API =====
def ejecutar_buscador():
    try: run_terminal()
    except KeyboardInterrupt: print("\nInterrumpido por el usuario.")

if __name__=="__main__": ejecutar_buscador()
