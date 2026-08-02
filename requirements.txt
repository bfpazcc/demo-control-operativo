import sqlite3
import os
import io
import traceback
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import openpyxl
import seed_data

app = FastAPI(title="Control Operativo Demo B2B")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/tmp/control_operativo.db"

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Helper seguro para renderizar plantillas sin depender de la firma cambiante de Starlette TemplateResponse
def render_template(name: str, request: Request, context: dict = None):
    if context is None:
        context = {}
    ctx = {"request": request, **context}
    # Obtener la plantilla Jinja2 directamente y renderizarla a HTML
    tmpl = templates.get_template(name)
    content = tmpl.render(ctx)
    return HTMLResponse(content)

# Capturador Global de Excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = traceback.format_exc()
    print("DETALLE DEL ERROR EN SERVIDOR:\n", error_msg)
    return PlainTextResponse(f"ERROR DETALLADO EN EL SERVIDOR:\n\n{error_msg}", status_code=500)

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipos'")
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            seed_data.create_seed_data(DB_PATH)
    except Exception as e:
        print("Error al inicializar DB:", e)
        seed_data.create_seed_data(DB_PATH)

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

    return render_template("index.html", request, {
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

    return render_template("parte_diario.html", request, {
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

    return render_template("combustible.html", request, {
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

    return render_template("mantenimiento.html", request, {
        "alertas": alertas
    })

@app.get("/portabilidad", response_class=HTMLResponse)
def get_portabilidad(request: Request):
    return render_template("portabilidad.html", request)

@app.get("/exportar-excel")
def exportar_excel():
    conn = get_db()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sheets_queries = [
        ('Equipos y Flota', 'SELECT * FROM equipos'),
        ('Partes Diarios', 'SELECT * FROM partes_diarios'),
        ('Combustible', 'SELECT * FROM abastecimientos_combustible'),
        ('Alertas Mantenimiento', 'SELECT * FROM alertas_mantenimiento')
    ]

    for title, query in sheets_queries:
        ws = wb.create_sheet(title=title)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        ws.append(columns)
        for row in cursor.fetchall():
            ws.append(list(row))

    conn.close()

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="Reporte_Control_Operativo_Demo.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
