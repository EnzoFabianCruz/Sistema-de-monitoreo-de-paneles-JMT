import requests
import os
import time
from django.core.cache import cache
from dotenv import load_dotenv
load_dotenv()

JMT_URL   = os.getenv("JMT_API_URL")
JMT_TOKEN = os.getenv("JMT_API_TOKEN")
HEADERS   = {"x-token": JMT_TOKEN}

def get_ubigeo():
    datos = cache.get("jmt_ubigeo")
    if datos is None:
        t0 = time.time()
        response = requests.get(f"{JMT_URL}/ubigeo", headers=HEADERS)
        response.raise_for_status()
        datos = response.json()
        cache.set("jmt_ubigeo", datos, timeout=60*60*24)  # 24 horas
        print(f"DEBUG TIEMPO get_ubigeo (sin cache): {time.time() - t0:.2f}s")
    return datos

def get_ubicaciones(dep=None, prov=None, dist=None):
    clave = f"jmt_ubicaciones_{dep}_{prov}_{dist}"
    datos = cache.get(clave)
    if datos is None:
        t0 = time.time()
        params = {}
        if dep:  params["dep"]  = dep
        if prov: params["prov"] = prov
        if dist: params["dist"] = dist
        response = requests.get(f"{JMT_URL}/ubicaciones", headers=HEADERS, params=params)
        response.raise_for_status()
        datos = response.json()
        cache.set(clave, datos, timeout=60*10)  # 10 minutos
        print(f"DEBUG TIEMPO get_ubicaciones (sin cache) dep={dep} prov={prov} dist={dist}: {time.time() - t0:.2f}s")
    return datos

def get_ubicaciones_dict(dep=None, prov=None):
    data = get_ubicaciones(dep=dep, prov=prov)
    return {u["CodigoUbicacion"].strip(): u for u in data}

def get_departamentos():
    data = get_ubigeo()
    vistos = set()
    result = []
    for item in data:
        dep = item["CodigoDepartamento"].strip()
        if item["CodigoProvincia"].strip() == "00" and item["CodigoDistrito"].strip() == "00" and dep != "00":
            if dep not in vistos:
                vistos.add(dep)
                result.append({"CodigoDepartamento": dep, "Nombre": item["Nombre"]})
    return sorted(result, key=lambda x: x["Nombre"])