import sqlite3
import os
import io
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI(title="Control Operativo Demo B2B")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/tmp/control_operativo.db"

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def init_db():
    if not os.path.exists(DB_PATH):
        import seed_data
        print("Base de datos inicializada con datos de prueba.")

@app.on_event("startup")
def startup_event():
    init_db()

def get_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    total_equipos = cursor.execute("SELECT COUNT(*) FROM equipos").fetchone()[0]
    lista_equipos = [dict(row) for row in cursor.execute("SELECT * FROM equipos ORDER BY tipo_sector, codigo").fetchall()]

    comb_stat = cursor.execute("SELECT SUM(galones), SUM(costo_total) FROM abastecimientos_combustible").fetchone()
    total_galones = comb_stat[0] if comb_stat[0] else 0.0
    total_costo_combustible = comb_stat[1] if comb_stat[1] else 0.0

    total_partes = cursor.execute("SELECT COUNT(*) FROM partes_diarios").fetchone()[0]

    alertas_pendientes = cursor.execute("SELECT COUNT(*) FROM alertas_mantenimiento WHERE estado != 'REALIZADO'").fetchone()[0]

    query_cb = """
    SELECT cb.*, eq.codigo, eq.tipo_sector, p.nombre as personal_nombre
    FROM abastecimientos_combustible cb
    JOIN equipos eq ON cb.equipo_id = eq.id
    JOIN personal p ON cb.personal_id = p.id
    ORDER BY cb.fecha DESC LIMIT 5
    """
    ultimos_combustibles = [dict(row) for row in cursor.execute(query_cb).fetchall()]

    conn.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_equipos": total_equipos,
        "lista_equipos": lista_equipos,
        "total_galones": total_galones,
        "total_costo_combustible": total_costo_combustible,
        "total_partes": total_partes,
        "alertas_pendientes": alertas_pendientes,
        "ultimos_combustibles": ultimos_combustibles
    })

@app.get("/parte-diario", response_class=HTMLResponse)
def get_parte_diario(request: Request, mensaje: str = None):
    conn = get_db()
    cursor = conn.cursor()
    equipos = [dict(row) for row in cursor.execute("SELECT * FROM equipos WHERE estado='ACTIVO'").fetchall()]
    personal = [dict(row) for row in cursor.execute("SELECT * FROM personal").fetchall()]
    conn.close()

    return templates.TemplateResponse("parte_diario.html", {
        "request": request,
        "equipos": equipos,
        "personal": personal,
        "mensaje": mensaje
    })

@app.post("/parte-diario")
def post_parte_diario(
    fecha: str = Form(...),
    equipo_id: int = Form(...),
    personal_id: int = Form(...),
    obra_origen: str = Form(...),
    destino: str = Form(""),
    lectura_inicial: float = Form(...),
    lectura_final: float = Form(...),
    observaciones: str = Form("")
):
    conn = get_db()
    cursor = conn.cursor()

    eq = cursor.execute("SELECT tipo_sector FROM equipos WHERE id=?", (equipo_id,)).fetchone()
    tipo_sector = eq["tipo_sector"] if eq else "TRANSPORTE"

    unidades_trabajadas = abs(lectura_final - lectura_inicial)

    cursor.execute("""
    INSERT INTO partes_diarios (fecha, equipo_id, personal_id, tipo_sector, obra_origen, destino, lectura_inicial, lectura_final, unidades_trabajadas, observaciones)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, equipo_id, personal_id, tipo_sector, obra_origen, destino, lectura_inicial, lectura_final, unidades_trabajadas, observaciones))

    if tipo_sector == 'TRANSPORTE':
        cursor.execute("UPDATE equipos SET kilometraje_actual=? WHERE id=?", (lectura_final, equipo_id))
    else:
        cursor.execute("UPDATE equipos SET horometro_actual=? WHERE id=?", (lectura_final, equipo_id))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/parte-diario?mensaje=Parte+Diario+guardado+correctamente", status_code=303)

@app.get("/combustible", response_class=HTMLResponse)
def get_combustible(request: Request, mensaje: str = None):
    conn = get_db()
    cursor = conn.cursor()
    equipos = [dict(row) for row in cursor.execute("SELECT * FROM equipos WHERE estado='ACTIVO'").fetchall()]
    personal = [dict(row) for row in cursor.execute("SELECT * FROM personal").fetchall()]
    conn.close()

    return templates.TemplateResponse("combustible.html", {
        "request": request,
        "equipos": equipos,
        "personal": personal,
        "mensaje": mensaje
    })

@app.post("/combustible")
def post_combustible(
    fecha: str = Form(...),
    equipo_id: int = Form(...),
    personal_id: int = Form(...),
    grifo_cisterna: str = Form(...),
    galones: float = Form(...),
    costo_total: float = Form(...),
    lectura_momento: float = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()

    eq = cursor.execute("SELECT tipo_sector FROM equipos WHERE id=?", (equipo_id,)).fetchone()
    tipo_sector = eq["tipo_sector"] if eq else "TRANSPORTE"

    if galones > 0:
        if tipo_sector == 'TRANSPORTE':
            rendimiento = 8.5
        else:
            rendimiento = 0.14
    else:
        rendimiento = 0.0

    cursor.execute("""
    INSERT INTO abastecimientos_combustible (fecha, equipo_id, personal_id, grifo_cisterna, galones, costo_total, lectura_momento, foto_comprobante, rendimiento_calculado)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, equipo_id, personal_id, grifo_cisterna, galones, costo_total, lectura_momento, 'voucher_nuevo.jpg', rendimiento))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/combustible?mensaje=Registro+de+combustible+guardado", status_code=303)

@app.get("/mantenimiento", response_class=HTMLResponse)
def get_mantenimiento(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    query_alt = """
    SELECT alt.*, eq.codigo, eq.categoria, eq.tipo_sector, eq.kilometraje_actual, eq.horometro_actual
    FROM alertas_mantenimiento alt
    JOIN equipos eq ON alt.equipo_id = eq.id
    ORDER BY alt.estado DESC
    """
    alertas = [dict(row) for row in cursor.execute(query_alt).fetchall()]
    conn.close()

    return templates.TemplateResponse("mantenimiento.html", {
        "request": request,
        "alertas": alertas
    })

@app.get("/portabilidad", response_class=HTMLResponse)
def get_portabilidad(request: Request):
    return templates.TemplateResponse("portabilidad.html", {"request": request})

@app.get("/exportar-excel")
def exportar_excel():
    conn = get_db()
    
    df_equipos = pd.read_sql_query("SELECT * FROM equipos", conn)
    df_partes = pd.read_sql_query("SELECT * FROM partes_diarios", conn)
    df_combustible = pd.read_sql_query("SELECT * FROM abastecimientos_combustible", conn)
    df_alertas = pd.read_sql_query("SELECT * FROM alertas_mantenimiento", conn)
    
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_equipos.to_excel(writer, sheet_name='Equipos y Flota', index=False)
        df_partes.to_excel(writer, sheet_name='Partes Diarios', index=False)
        df_combustible.to_excel(writer, sheet_name='Combustible', index=False)
        df_alertas.to_excel(writer, sheet_name='Alertas Mantenimiento', index=False)
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="Reporte_Control_Operativo_Demo.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
