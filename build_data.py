import json
import os
from collections import Counter, defaultdict
from datetime import datetime

import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_XLSX = r"C:\Users\exjoli16\Downloads\METRICAS DE ORDENS.XLSX"
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)


def norm(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    return s


def parse_date(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def area_from_local(local):
    s = norm(local)
    if not s:
        return "NÃO CLASSIFICADO"
    parts = s.split("-")
    if len(parts) >= 2 and parts[1].strip():
        return parts[1].strip()
    return "NÃO CLASSIFICADO"


def default_status_class(system_status, user_status):
    # Classificação proposta (editável) baseada em códigos SAP observados no campo Status do sistema.
    # Não substitui validação do usuário.
    s = (system_status or "").upper()
    tokens = set(s.split())
    if "ABER" in tokens and "ENTE" not in tokens and "ENCE" not in tokens:
        return "Pendente"
    if "LIB" in tokens and "ENTE" not in tokens and "ENCE" not in tokens and "CONF" not in tokens:
        return "Em Execução"
    if "ENTE" in tokens or "ENCE" in tokens or "CONF" in tokens:
        return "Concluída"
    if "BLOQ" in tokens:
        return "Pendente"
    return "Não Informada"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


wb = openpyxl.load_workbook(SOURCE_XLSX, data_only=True, read_only=True)
ws = wb[wb.sheetnames[0]]
rows = list(ws.iter_rows(values_only=True))
headers = [str(h).strip() if h is not None else "" for h in rows[0]]
idx = {h: i for i, h in enumerate(headers)}

wanted = [
    "Centro trab.respons.",
    "Ordem",
    "Plano de manutenção",
    "Status usuário",
    "Tipo de ordem",
    "Data-base do início",
    "Local de instalação",
    "Texto breve",
    "Status do sistema",
]

records = []
seen_orders = set()
duplicate_orders = 0
for r in rows[1:]:
    def g(name):
        i = idx.get(name)
        return r[i] if i is not None and i < len(r) else None

    ordem_raw = g("Ordem")
    ordem = norm(ordem_raw)
    if not ordem:
        continue
    # Regra: não contar ordens duplicadas mais de uma vez.
    if ordem in seen_orders:
        duplicate_orders += 1
        continue
    seen_orders.add(ordem)

    dt = parse_date(g("Data-base do início"))
    local = norm(g("Local de instalação"))
    area_cod = area_from_local(local)
    rec = {
        "centro_trabalho": norm(g("Centro trab.respons.")),
        "ordem": ordem,
        "plano_manutencao": norm(g("Plano de manutenção")),
        "status_usuario": norm(g("Status usuário")),
        "tipo_ordem": norm(g("Tipo de ordem")),
        "data_inicio": dt.strftime("%Y-%m-%d") if dt else "",
        "ano": dt.year if dt else None,
        "mes": dt.month if dt else None,
        "local_instalacao": local,
        "area_codigo": area_cod,
        "texto_breve": norm(g("Texto breve")),
        "status_sistema": norm(g("Status do sistema")),
    }
    records.append(rec)

wb.close()

# Default area classification (editable). Derived from data (segmento do Local de instalação).
areas_found = sorted(set(r["area_codigo"] for r in records))
area_config_path = os.path.join(CONFIG_DIR, "classificacao_areas.json")
existing_area_cfg = load_json(area_config_path, None)
area_map = {}
if isinstance(existing_area_cfg, dict) and "mapeamento" in existing_area_cfg:
    area_map = existing_area_cfg.get("mapeamento", {}) or {}
# ensure all areas exist
for a in areas_found:
    if a not in area_map:
        if a == "NÃO CLASSIFICADO":
            area_map[a] = "NÃO CLASSIFICADO"
        else:
            area_map[a] = a
area_cfg = {
    "descricao": "Tabela de classificação de áreas editável. Chave: código derivado do Local de instalação. Valor: nome da área para exibição.",
    "origem": "Gerada a partir dos dados reais de METRICAS DE ORDENS.XLSX. Ajuste os nomes conforme necessário.",
    "mapeamento": dict(sorted(area_map.items())),
}
save_json(area_config_path, area_cfg)

# Default status classification (editable, proposta)
status_pairs = sorted(set((r["status_sistema"], r["status_usuario"]) for r in records))
status_sys_unique = sorted(set(r["status_sistema"] for r in records))
status_cfg_path = os.path.join(CONFIG_DIR, "classificacao_status.json")
existing_status_cfg = load_json(status_cfg_path, None)
sys_map = {}
if isinstance(existing_status_cfg, dict) and "status_sistema" in existing_status_cfg:
    sys_map = existing_status_cfg.get("status_sistema", {}) or {}
for s in status_sys_unique:
    if s not in sys_map:
        sys_map[s] = {
            "situacao": default_status_class(s, ""),
            "observacao": "Classificação proposta automaticamente com base nos códigos SAP observados. Validar e ajustar se necessário.",
        }
status_cfg = {
    "descricao": "Dicionário de classificação dos status das ordens. Situações utilizadas nos KPIs: Concluída, Pendente, Em Execução. Edite para validar.",
    "regra": "Os indicadores de ordens concluídas/pendentes/em execução são calculados somente conforme esta classificação.",
    "status_sistema": dict(sorted(sys_map.items())),
    "status_usuario_observados": sorted(set(r["status_usuario"] for r in records)),
}
save_json(status_cfg_path, status_cfg)

# Metas (não informadas na base)
metas_path = os.path.join(CONFIG_DIR, "metas.json")
if not os.path.exists(metas_path):
    metas_cfg = {
        "descricao": "Metas mensais por área. Informação não existente na base original; cadastrar conforme necessidade.",
        "meta_global_mensal": None,
        "metas_por_area_mes": {},
        "exemplo": {
            "AD1": {"2026-01": 100, "2026-02": 100}
        }
    }
    save_json(metas_path, metas_cfg)

# Apply current classification to records for convenience
for r in records:
    r["area"] = area_cfg["mapeamento"].get(r["area_codigo"], r["area_codigo"] or "NÃO CLASSIFICADO")
    st = status_cfg["status_sistema"].get(r["status_sistema"], {})
    r["situacao"] = st.get("situacao", "Não Informada") if isinstance(st, dict) else "Não Informada"

# Summary/metadata
anos = sorted(set(r["ano"] for r in records if r["ano"] is not None))
meses_presentes = sorted(set((r["ano"], r["mes"]) for r in records if r["ano"] is not None and r["mes"] is not None))

metadata = {
    "fonte": os.path.basename(SOURCE_XLSX),
    "caminho_fonte": SOURCE_XLSX,
    "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_registros_base": len(rows) - 1,
    "total_ordens_unicas": len(records),
    "ordens_duplicadas_desconsideradas": duplicate_orders,
    "anos": anos,
    "periodos": [{"ano": a, "mes": m} for a, m in meses_presentes],
    "campos_utilizados": wanted,
    "observacoes": [
        "Contagem baseada em ordens únicas (campo Ordem).",
        "Mês e ano derivados de Data-base do início.",
        "Área derivada do Local de instalação com classificação editável em config/classificacao_areas.json.",
        "Situação calculada conforme config/classificacao_status.json (proposta, validar).",
        "Metas não informadas na base original; configurar em config/metas.json."
    ]
}

save_json(os.path.join(DATA_DIR, "ordens.json"), {"metadata": metadata, "records": records})
save_json(os.path.join(DATA_DIR, "metadata.json"), metadata)

print("OK")
print("Registros base:", len(rows)-1)
print("Ordens únicas:", len(records))
print("Duplicadas desconsideradas:", duplicate_orders)
print("Anos:", anos)
print("Áreas:", len(areas_found))
print("Status sistema únicos:", len(status_sys_unique))
