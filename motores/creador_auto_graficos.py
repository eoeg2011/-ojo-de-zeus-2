# -*- coding: utf-8 -*-
"""
Creador de sitios – Ojo de Zeus 2 (DUAL DRIVER)
– Entrada por terminal (con ejemplos claros).
– Navegador real si hay GUI: intenta Firefox → si falla, usa Chromium (fallback).
– HTTP solo si no hay GUI.
– Espera carga completa + estabiliza URL (evita falsos por SPA/redirect).
– Tolerante a fallos; no se cierra.
– Recolecta TODOS los resultados (outcomes) por método para reales y falsos.
– Quita resultados que aparecen en ambos lados.
– Muestra TODOS los métodos (Verde=BUENO, Rojo=MALO) con mini explicación.
– Eliges cuáles guardar (incluye rojos si quieres probar).
"""

import os
import re
import json
import time
import random
import platform
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

# ===================== Colores y estilos =====================
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN; RED = Fore.RED; YELLOW = Fore.YELLOW; CYAN = Fore.CYAN; MAG = Fore.MAGENTA; BLUE = Fore.BLUE
    BOLD = Style.BRIGHT; RESET = Style.RESET_ALL
    OK = GREEN + "✓" + RESET; BAD = RED + "✗" + RESET; WARN = YELLOW + "!" + RESET
except Exception:
    class _NC:
        def __getattr__(self, _): return ""
    GREEN = RED = YELLOW = CYAN = MAG = BLUE = BOLD = RESET = _NC()
    OK = "✓"; BAD = "✗"; WARN = "!"

def log(evento: str, detalle: str):
    print(f"{CYAN}[{evento}]{RESET} {detalle}", flush=True)

def log_exc(prefix: str, e: Exception):
    print(f"{RED}[ERROR]{RESET} {prefix}: {e}", flush=True)

# ===================== HTTP backend =====================
HTTP_BACKEND = "httpx"
try:
    import httpx
except Exception:
    HTTP_BACKEND = "requests"
    import requests  # type: ignore

# ===================== Selenium (opcional) – DUAL DRIVER =====================
SELENIUM_OK = False
try:
    import shutil
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_OK = True
except Exception:
    SELENIUM_OK = False

# Rutas comunes (ajústalas si tu sistema usa otras)
DEFAULT_PATHS = {
    "geckodriver": ["/usr/local/bin/geckodriver", "/usr/bin/geckodriver"],
    "firefox": ["/usr/bin/firefox-esr", "/usr/bin/firefox"],
    "chromedriver": ["/usr/bin/chromedriver"],
    "chromium": ["/usr/bin/chromium", "/usr/bin/chromium-browser"],
}

def which_any(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # prueba PATH
    for p in paths:
        bn = os.path.basename(p)
        w = shutil.which(bn)
        if w:
            return w
    return None

def has_display() -> bool:
    if platform.system().lower() == "linux":
        return bool(os.environ.get("DISPLAY"))
    return True

# ===================== Tiempos (exactitud) =====================
SELENIUM_PAGELOAD_TIMEOUT = 45      # seg. para load del documento
DOM_READY_MAX_WAIT       = 20       # seg. para document.readyState=="complete"
URL_STABILIZE_WINDOW_MS  = 900      # ms de estabilidad continua de URL
URL_STABILIZE_MAX_MS     = 12000    # ms totales para estabilizar
POST_LOAD_SETTLE_MS      = 700      # ms extra para que termine de pintar la SPA

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Mobile Safari/537.36",
]

CAPTCHA_MARKERS = [
    "captcha","cf-challenge","hcaptcha","g-recaptcha","Cloudflare","Attention Required!",
    "/cdn-cgi/challenge-platform","Are you a human","Just a moment..."
]
NOTFOUND_MARKERS = [
    "not found","página no encontrada","404","no existe","doesn't exist","user not found",
    "page not found","usuario no encontrado","no encontrado"
]
JSON_CT = ("application/json","application/ld+json","application/vnd.api+json")

def rand_ua() -> str:
    return random.choice(USER_AGENTS)

def safe_json(text: str) -> Tuple[bool, Any]:
    try:
        import json as _json
        return True, _json.loads(text)
    except Exception:
        return False, None

# ===================== Tipos =====================
@dataclass
class Resp:
    url: str
    final_url: str
    status: int
    headers: Dict[str, str]
    text: str
    is_json: bool
    json_obj: Any = None
    via: str = "http"
    took_ms: int = 0

@dataclass
class EvalRes:
    usuario: str
    resp_http: Resp
    resp_sel: Optional[Resp] = None
    content_markers: Dict[str, Any] = field(default_factory=dict)

# ===================== HTTP =====================
def fetch_http(url: str, timeout: float = 18.0, follow_redirects: bool = True) -> Resp:
    t0 = int(time.time() * 1000)
    headers = {
        "User-Agent": rand_ua(),
        "Accept": "*/*",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    final_url = url; status = 0; resp_headers: Dict[str, str] = {}; text = ""; is_json = False; jobj = None
    try:
        if HTTP_BACKEND == "httpx":
            with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, verify=True) as c:
                r = c.get(url)
                final_url = str(r.url); status = r.status_code
                resp_headers = {k.lower(): v for k, v in r.headers.items()}
                text = r.text or ""
        else:
            r = requests.get(url, headers=headers, allow_redirects=follow_redirects, timeout=timeout)
            final_url = r.url; status = r.status_code
            resp_headers = {k.lower(): v for k, v in r.headers.items()}
            text = r.text or ""
        ct = resp_headers.get("content-type","").split(";")[0].strip().lower()
        if ct in JSON_CT:
            ok, obj = safe_json(text)
            is_json = ok; jobj = obj
    except Exception as e:
        text = f"[HTTP_ERROR] {e}"; status = -1
        log_exc("fetch_http", e)
    took = int(time.time() * 1000) - t0
    return Resp(url, final_url, status, resp_headers, text, is_json, jobj, "http", took)

# ===================== Selenium helpers =====================
def _wait_dom_complete(driver, max_wait_s: int) -> None:
    WebDriverWait(driver, max_wait_s).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def _stabilize_url(driver, window_ms: int, max_ms: int) -> str:
    start = time.time() * 1000
    last = driver.current_url
    estable_desde = start
    while True:
        time.sleep(0.15)
        cur = driver.current_url
        ahora = time.time() * 1000
        if cur != last:
            last = cur
            estable_desde = ahora
        if (ahora - estable_desde) >= window_ms:
            return cur
        if (ahora - start) >= max_ms:
            return cur

# Devuelve (driver_name, driver_instance) o (None, None)
def get_webdriver() -> Tuple[Optional[str], Optional["webdriver.Remote"]]:
    if not (SELENIUM_OK and has_display()):
        return (None, None)
    # 1) Firefox explícito
    try:
        from selenium.webdriver.firefox.service import Service as FxService
        from selenium.webdriver.firefox.options import Options as FxOptions
        gecko = which_any(DEFAULT_PATHS["geckodriver"])
        fxbin = which_any(DEFAULT_PATHS["firefox"])
        if gecko and fxbin:
            opts = FxOptions()
            # Ventana real si hay DISPLAY (no headless)
            opts.binary_location = fxbin
            svc = FxService(executable_path=gecko)
            drv = webdriver.Firefox(service=svc, options=opts)
            log("NAVEGADOR", f"Usando Firefox real → {fxbin} + {gecko}")
            return ("firefox", drv)
    except Exception as e:
        log("AVISO", f"Firefox no disponible ({e}). Probando Chromium…")

    # 2) Chromium explícito (fallback)
    try:
        from selenium.webdriver.chrome.service import Service as ChService
        from selenium.webdriver.chrome.options import Options as ChOptions
        chd = which_any(DEFAULT_PATHS["chromedriver"])
        chbin = which_any(DEFAULT_PATHS["chromium"])
        if chd and chbin:
            opts = ChOptions()
            opts.binary_location = chbin
            svc = ChService(executable_path=chd)
            drv = webdriver.Chrome(service=svc, options=opts)
            log("NAVEGADOR", f"Usando Chromium real → {chbin} + {chd}")
            return ("chromium", drv)
    except Exception as e:
        log("AVISO", f"Chromium no disponible ({e}).")

    return (None, None)

def selenium_fetch(url: str) -> Optional[Resp]:
    """Abre navegador real (Firefox o Chromium). Si no hay, retorna None."""
    name, drv = get_webdriver()
    if not drv:
        return None
    try:
        print(f"{MAG}{BOLD}→ Abriendo navegador real ({name}) para: {url}{RESET}")
        try:
            # Tiempo de carga y estabilización
            drv.set_page_load_timeout(SELENIUM_PAGELOAD_TIMEOUT)
        except Exception:
            pass
        t0 = int(time.time() * 1000)

        drv.get(url)
        # Espera DOM completo (sin bloquear infinito)
        try:
            _wait_dom_complete(drv, DOM_READY_MAX_WAIT)
        except Exception:
            log("AVISO", "La página no llegó a 'complete' a tiempo. Continuamos para capturar estado final.")

        # Estabiliza URL (importante para detectar perfiles inexistentes)
        final_estable = _stabilize_url(drv, URL_STABILIZE_WINDOW_MS, URL_STABILIZE_MAX_MS)
        time.sleep(POST_LOAD_SETTLE_MS / 1000.0)

        html = drv.page_source or ""
        took = int(time.time() * 1000) - t0

        return Resp(url=url, final_url=final_estable, status=200,
                    headers={"via": name}, text=html, is_json=False,
                    json_obj=None, via=name, took_ms=took)
    except Exception as e:
        log_exc("selenium_fetch", e)
        return None
    finally:
        try:
            drv.quit()
        except Exception:
            pass

# ===================== Detección básica =====================
def detect_captcha(text: str) -> bool:
    t = text.lower()
    return any(m.lower() in t for m in CAPTCHA_MARKERS)

def detect_notfound(text: str) -> bool:
    t = text.lower()
    return any(m.lower() in t for m in NOTFOUND_MARKERS)

# ===================== Firmas (outcomes) =====================
def _final_url_from_eval(e: EvalRes) -> str:
    if e and e.resp_sel and e.resp_sel.final_url:
        return e.resp_sel.final_url
    return e.resp_http.final_url

def _content_text_from_eval(e: EvalRes) -> str:
    return (e.resp_sel.text if (e and e.resp_sel and len(e.resp_sel.text) > len(e.resp_http.text))
            else (e.resp_http.text if e else ""))

def method_outcome_signature(metodo: str, params: Dict[str, Any], e: EvalRes) -> Optional[str]:
    """
    Devuelve un texto corto con el “resultado” observado para ese método/usuario.
    Eso se guarda y luego el Buscador decide por coincidencia exacta.
    """
    try:
        if metodo == "status_code":
            return f"status={e.resp_http.status}"

        elif metodo in ("url_check", "redirect_check"):
            return f"final_url={_final_url_from_eval(e)}"

        elif metodo == "status_code_y_texto":
            code = params.get("codigo")
            keys = [k.lower() for k in params.get("debe_contener", [])]
            txt = _content_text_from_eval(e).lower()
            hit = (e.resp_http.status == code) and all(k in txt for k in keys[:5])
            return f"status_text_hit={bool(hit)}"

        elif metodo == "html_contains":
            keys = [k.lower() for k in params.get("claves", [])]
            txt = _content_text_from_eval(e).lower()
            hit = all(k in txt for k in keys[:5]) if keys else False
            return f"html_hit={bool(hit)}"

        elif metodo == "json_response_check":
            if e.resp_http.is_json and isinstance(e.resp_http.json_obj, dict):
                keys = params.get("claves_presentes", [])
                hit = all(k in e.resp_http.json_obj for k in keys[:5])
                return f"json_hit={bool(hit)}"
            return "json_hit=False"

        elif metodo == "captcha_detect":
            txt = _content_text_from_eval(e)
            return f"captcha={detect_captcha(txt)}"

        elif metodo == "palabras_clave":
            keys = [k.lower() for k in params.get("claves", [])]
            txt = _content_text_from_eval(e).lower()
            hit = any(k in txt for k in keys)
            return f"kw_hit={bool(hit)}"

        elif metodo == "custom_selector_check":
            return f"dom_loaded={bool(e.resp_sel)}"
    except Exception as ex:
        log_exc(f"method_outcome_signature({metodo})", ex)
        return None
    return None

# ===================== Text mining auxiliar =====================
def extract_words(text: str, min_len: int = 4, max_words: int = 80) -> List[str]:
    text = re.sub(r"<[^>]+>", " ", text)
    tokens = re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9_]{%d,}" % min_len, text)
    freq: Dict[str,int] = {}
    for w in tokens:
        wl = w.lower()
        freq[wl] = freq.get(wl, 0) + 1
    top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:max_words]
    return [w for w,_ in top]

def common_intersection(list_of_lists: List[List[str]]) -> List[str]:
    if not list_of_lists: return []
    inter = set(list_of_lists[0])
    for lst in list_of_lists[1:]:
        inter &= set(lst)
    return list(inter)

def stable_contains(all_texts: List[str]) -> List[str]:
    bags = [extract_words(t) for t in all_texts]
    inter = common_intersection(bags)
    basura = {"home","login","about","contact","cookies","terms","policy","help","explore","search"}
    inter = [w for w in inter if w not in basura]
    return sorted(inter)[:30]

# ===================== Plantillas de métodos =====================
def derive_method_templates(site_name: str,
                            url_base: str,
                            reales: List[EvalRes],
                            falsos: List[EvalRes],
                            palabras_usuario: List[str]) -> List[Dict[str, Any]]:
    methods: List[Dict[str, Any]] = []

    # 1) status_code — los códigos pueden variar por estado/cuenta
    methods.append({"nombre": site_name, "url_base": url_base, "metodo": "status_code",
                    "parametros": {}, "evidencia": {"nota": "Código HTTP puede cambiar por estado de la cuenta."}})

    # 2) url_check / redirect_check — importante en sitios que cambian URL al final
    methods.append({"nombre": site_name, "url_base": url_base, "metodo": "url_check",
                    "parametros": {}, "evidencia": {"nota": "Compara la URL final estabilizada."}})
    methods.append({"nombre": site_name, "url_base": url_base, "metodo": "redirect_check",
                    "parametros": {}, "evidencia": {"nota": "Detecta diferencia de destino final."}})

    # 3) html_contains / status_code_y_texto — claves del DOM real
    real_texts = [_content_text_from_eval(e) for e in reales]
    fake_texts = [_content_text_from_eval(e) for e in falsos]
    real_stable = set(stable_contains(real_texts))
    fake_stable = set(stable_contains(fake_texts))
    html_keys = list(real_stable - fake_stable)
    if html_keys:
        methods.append({"nombre": site_name, "url_base": url_base, "metodo": "html_contains",
                        "parametros": {"claves": sorted(html_keys)[:25]},
                        "evidencia": {"claves": sorted(html_keys)[:25]}})
        real_codes = [e.resp_http.status for e in reales]
        if real_codes:
            code = max(set(real_codes), key=real_codes.count)
            methods.append({"nombre": site_name, "url_base": url_base, "metodo": "status_code_y_texto",
                            "parametros": {"codigo": code, "debe_contener": sorted(html_keys)[:10]},
                            "evidencia": {"codigo": code}})

    # 4) json_response_check — si hubo JSON
    if any(e.resp_http.is_json for e in reales + falsos):
        sets = []
        for e in reales:
            if e.resp_http.is_json and isinstance(e.resp_http.json_obj, dict):
                sets.append(set(e.resp_http.json_obj.keys()))
        if sets:
            inter = set.intersection(*sets) if len(sets) > 1 else sets[0]
            if inter:
                keys = sorted(list(inter))[:20]
                methods.append({"nombre": site_name, "url_base": url_base, "metodo": "json_response_check",
                                "parametros": {"claves_presentes": keys},
                                "evidencia": {"claves": keys}})

    # 5) captcha_detect — si vimos marcadores
    if any(e.content_markers.get("captcha") for e in reales + falsos):
        methods.append({"nombre": site_name, "url_base": url_base, "metodo": "captcha_detect",
                        "parametros": {"marcadores": CAPTCHA_MARKERS[:10]},
                        "evidencia": {"nota": "Se detectaron señales de captcha."}})

    # 6) palabras_clave — aportadas por el usuario (filtradas contra falsos)
    if palabras_usuario:
        falsos_text = " ".join([_content_text_from_eval(e).lower() for e in falsos])
        claves = [k for k in palabras_usuario if k.lower() not in falsos_text]
        if claves:
            methods.append({"nombre": site_name, "url_base": url_base, "metodo": "palabras_clave",
                            "parametros": {"claves": claves[:20]},
                            "evidencia": {"claves": claves[:20]}})

    # 7) custom_selector_check — si hubo Selenium (DOM real)
    if any(e.resp_sel for e in reales + falsos):
        methods.append({"nombre": site_name, "url_base": url_base, "metodo": "custom_selector_check",
                        "parametros": {"css_selectors": ["title","h1",'[role="main"]']},
                        "evidencia": {"nota": "Requiere DOM real (Selenium)."}})

    return methods

# ===================== Outcomes por método =====================
def compute_outcomes_for_method(m: Dict[str, Any],
                                reales: List[EvalRes],
                                falsos: List[EvalRes]) -> Tuple[Set[str], Set[str]]:
    metodo = m.get("metodo","?")
    params = m.get("parametros",{})
    real_out: Set[str] = set()
    fake_out: Set[str] = set()

    for e in reales:
        try:
            sig = method_outcome_signature(metodo, params, e)
            if sig is not None:
                real_out.add(sig)
        except Exception as ex:
            log_exc(f"compute_outcomes(real,{metodo})", ex)

    for e in falsos:
        try:
            sig = method_outcome_signature(metodo, params, e)
            if sig is not None:
                fake_out.add(sig)
        except Exception as ex:
            log_exc(f"compute_outcomes(fake,{metodo})", ex)

    return real_out, fake_out

def build_methods_with_outcomes(site_name: str,
                                url_base: str,
                                templates: List[Dict[str, Any]],
                                reales: List[EvalRes],
                                falsos: List[EvalRes]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for m in templates:
        ro, fo = compute_outcomes_for_method(m, reales, falsos)
        inter = ro & fo
        ro_clean = sorted(list(ro - inter))
        fo_clean = sorted(list(fo - inter))
        status = "GOOD" if (ro_clean or fo_clean) else "BAD"

        # Mini explicación breve, sin tecnicismos
        if status == "GOOD":
            if ro_clean and not fo_clean:
                razon = "Tiene resultados que solo vimos en cuentas reales."
            elif fo_clean and not ro_clean:
                razon = "Tiene resultados que solo vimos cuando NO existe."
            else:
                razon = "Tiene algunos resultados exclusivos (reales o falsos)."
        else:
            if inter:
                razon = "Todos los resultados aparecen en reales y falsos (no discrimina)."
            else:
                razon = "No encontramos resultados claros (insuficiente)."

        m2 = {
            **m,
            "signature_type": m.get("metodo"),
            "outcomes_real": ro_clean,
            "outcomes_fake": fo_clean,
            "outcomes_overlap": sorted(list(inter)),
            "status": status,
            "razon": razon
        }
        # Métricas simples
        m2.setdefault("evidencia", {})
        m2["evidencia"].update({
            "real_outcomes_count": len(ro_clean),
            "fake_outcomes_count": len(fo_clean),
            "overlap_count": len(inter),
        })
        enriched.append(m2)
    return enriched

# ===================== sitios.json helpers =====================
def load_sitios(path: str = "sitios.json") -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, list): return d
    except Exception as e:
        log_exc("load_sitios", e)
    return []

def save_sitios(items: List[Dict[str, Any]], path: str = "sitios.json") -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_exc("save_sitios", e)

def append_sitios(nuevos: List[Dict[str, Any]], path: str = "sitios.json") -> None:
    try:
        data = load_sitios(path)
        base = len(data)
        for i, m in enumerate(nuevos, start=1):
            m["metodo_id"] = base + i
        data.extend(nuevos)
        save_sitios(data, path)
    except Exception as e:
        log_exc("append_sitios", e)

# ===================== UI: lista y selección =====================
def prompt_select_methods(methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    print(f"\n{BOLD}{MAG}===== Revisión de métodos hallados ====={RESET}")
    for i, m in enumerate(methods, start=1):
        status = m.get("status","BAD")
        color = GREEN if status == "GOOD" else RED
        rcount = len(m.get("outcomes_real", []))
        fcount = len(m.get("outcomes_fake", []))
        overc  = len(m.get("outcomes_overlap", []))
        razon  = m.get("razon","")
        nombre = m.get("metodo","?")
        print(f"{color}{i:02d}{RESET} {BOLD}{nombre}{RESET}  "
              f"{color}[{status}]{RESET}  "
              f"{CYAN}R:{rcount}{RESET}  {CYAN}F:{fcount}{RESET}  {YELLOW}Solapa:{overc}{RESET}")
        if razon:
            print(f"   {YELLOW}• {razon}{RESET}")
        # Muestra hasta 2 outcomes por lado como muestra
        ro = m.get("outcomes_real", [])
        fo = m.get("outcomes_fake", [])
        ov = m.get("outcomes_overlap", [])
        if ro:
            print(f"   {GREEN}↳ Real:{RESET} {', '.join(ro[:2])}" + (" ..." if len(ro) > 2 else ""))
        if fo:
            print(f"   {RED}↳ Fake:{RESET} {', '.join(fo[:2])}" + (" ..." if len(fo) > 2 else ""))
        if ov:
            print(f"   {YELLOW}↳ Solapa:{RESET} {', '.join(ov[:2])}" + (" ..." if len(ov) > 2 else ""))

    print(f"\n{BOLD}Elige cuáles guardar:{RESET} ids separados por coma (1,3,7), rangos (2-5), 'all' para todos o Enter para ninguno.")
    sel = input("Selecciona métodos a guardar: ").strip().lower()

    keep: Set[int] = set()
    if sel == "all":
        keep = set(range(1, len(methods)+1))
    elif sel in ("","none"):
        keep = set()
    else:
        partes = [p.strip() for p in sel.split(",") if p.strip()]
        for p in partes:
            if "-" in p:
                a, b = p.split("-", 1)
                try:
                    ai, bi = int(a), int(b)
                    for x in range(min(ai,bi), max(ai,bi)+1):
                        if 1 <= x <= len(methods): keep.add(x)
                except: pass
            else:
                try:
                    idx = int(p)
                    if 1 <= idx <= len(methods): keep.add(idx)
                except: pass

    elegidos = [m for i, m in enumerate(methods, start=1) if i in keep]
    print(f"{OK} {len(elegidos)} método(s) seleccionados.")
    return elegidos

# ===================== Evaluación de usuarios =====================
def evaluate_user(url_base: str, usuario: str, use_browser: bool) -> Optional[EvalRes]:
    try:
        url = url_base.replace("{user}", usuario).replace("{usuario}", usuario)
        r_sel = selenium_fetch(url) if use_browser else None
        r_http = fetch_http(url)
        content = r_sel.text if (r_sel and len(r_sel.text) > len(r_http.text)) else r_http.text
        markers = {
            "captcha": detect_captcha(content),
            "notfound": detect_notfound(content),
            "has_json": r_http.is_json,
            "len": len(content),
            "final_url_http": r_http.final_url,
            "final_url_sel": r_sel.final_url if r_sel else "",
            "status_http": r_http.status,
        }
        return EvalRes(usuario, r_http, r_sel, markers)
    except Exception as e:
        log_exc(f"evaluate_user({usuario})", e)
        return None

# ===================== Núcleo principal =====================
def ejecutar_core(site_name: str,
                  url_base: str,
                  reales_users: List[str],
                  falsos_users: List[str],
                  palabras_usuario: List[str],
                  use_browser: bool) -> str:
    log("INFO", "Haciendo pruebas con usuarios reales…")
    eval_reales: List[EvalRes] = []
    eval_falsos: List[EvalRes] = []

    for u in reales_users:
        try:
            log("REAL", f"Evaluando {u}")
            e = evaluate_user(url_base, u, use_browser)
            if e: eval_reales.append(e)
            else: log("AVISO", f"No se pudo evaluar {u} (omitido).")
        except Exception as ex:
            log_exc(f"eval_real({u})", ex)
        time.sleep(0.3)

    for u in falsos_users:
        try:
            log("FALSO", f"Evaluando {u}")
            e = evaluate_user(url_base, u, use_browser)
            if e: eval_falsos.append(e)
            else: log("AVISO", f"No se pudo evaluar {u} (omitido).")
        except Exception as ex:
            log_exc(f"eval_falso({u})", ex)
        time.sleep(0.3)

    if not eval_reales:
        return "⚠️  No se logró evaluar ningún usuario REAL."

    log("INFO", "Generando plantillas de métodos…")
    templates = derive_method_templates(site_name, url_base, eval_reales, eval_falsos, palabras_usuario)

    log("INFO", "Calculando resultados (outcomes) por método…")
    methods = build_methods_with_outcomes(site_name, url_base, templates, eval_reales, eval_falsos)

    if not methods:
        return "⚠️  No se generaron métodos."

    seleccion = prompt_select_methods(methods)
    if not seleccion:
        return "ℹ️  No se guardó ningún método."

    append_sitios(seleccion, path="sitios.json")
    return f"✅ Guardados {len(seleccion)} método(s) en sitios.json."

# ===================== Entrada por terminal (con ejemplos) =====================
def run_terminal():
    print(f"{BOLD}🔱  Creador de sitios — Ojo de Zeus 2 by eoeg2011 (DUAL DRIVER){RESET}")
    print("============================================================")
    print(f"{YELLOW}Tips rápidos:{RESET}")
    print(f"  • {BOLD}URL base{RESET} debe tener {{user}} o {{usuario}} donde va el nombre.")
    print(f"    Ejemplos: {CYAN}https://www.pinterest.com/{{user}}/{RESET}  |  {CYAN}https://www.instagram.com/{{usuario}}{RESET}")
    print(f"  • {BOLD}Usuarios reales/falsos:{RESET}ingrasa uno o varios, {BOLD}separados por coma{RESET}.")
    print(f"    Ej.: reales → {CYAN}luis.perez, pepe345{RESET}  |  falsos → {CYAN}no_existe_123, xxyyzz_000{RESET}")
    print(f"  • {BOLD}Palabras clave (opcional):{RESET}ingresa una o varias, separadas por coma en ingles o español si asi esta en la pagina Ej.: {CYAN}followers, boards, posts{RESET}\n")

    site = input(f"{BOLD}📛 Nombre del sitio (ej. pinterest, instagram): {RESET}").strip()
    urlb = input(f"{BOLD}🔗 URL base con {{user}}/{{usuario}} (ver ejemplos arriba): {RESET}").strip()
    reales_str = input(f"{BOLD}👤 Usuarios REALES (uno o varios, separados por coma): {RESET}").strip()
    falsos_str = input(f"{BOLD}👻 Usuarios FALSOS (uno o varios, separados por coma, Enter para omitir): {RESET}").strip()
    palabras_str = input(f"{BOLD}📝 Palabras clave (opcional, separadas por coma): {RESET}").strip()

    # Validaciones amigables
    if "{user}" not in urlb and "{usuario}" not in urlb:
        print(f"{RED}La URL base debe incluir {{user}} o {{usuario}}. Ej.: https://www.tiktok.com/@{{user}}{RESET}")
        return

    reales = [u.strip() for u in reales_str.split(",") if u.strip()]
    falsos = [u.strip() for u in falsos_str.split(",") if u.strip()]
    palabras = [p.strip() for p in palabras_str.split(",") if p.strip()]

    if not site or not urlb or not reales:
        print(f"{YELLOW}Faltan datos obligatorios (sitio, URL base y al menos 1 real).{RESET}")
        return

    # Decidir navegador real: DUAL DRIVER (Firefox → Chromium). HTTP si no hay GUI.
    if has_display() and SELENIUM_OK:
        drv_name, drv_inst = get_webdriver()
        if drv_inst:
            # cerramos de inmediato; solo probamos disponibilidad
            try: drv_inst.quit()
            except Exception: pass
            use_browser = True
            print(f"{OK} Entorno gráfico con navegador real disponible ({BOLD}{drv_name}{RESET}).")
        else:
            print(f"{WARN} No se pudo iniciar Firefox ni Chromium. Se usará {BOLD}modo HTTP{RESET}.")
            use_browser = False
    else:
        print(f"{WARN} No hay entorno gráfico o Selenium no está disponible: se usará {BOLD}modo HTTP{RESET}.")
        use_browser = False

    res = ejecutar_core(site, urlb, reales, falsos, palabras, use_browser)
    print(res)

# ===================== API =====================
def ejecutar_creador():
    print(f"{BOLD}🔧 Creador de sitios (terminal; navegador real DUAL si hay GUI).{RESET}")
    try:
        run_terminal()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario (CTRL+C).")

def creador_auto_graficos():
    ejecutar_creador()

if __name__ == "__main__":
    ejecutar_creador()
