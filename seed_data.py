import sqlite3
import os

db_path = "/tmp/control_operativo.db"
schema_path = "/working_dir/c_9c876028e7cab330/demo_control_operativo/schema.sql"

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

with open(schema_path, "r", encoding="utf-8") as f:
    cursor.executescript(f.read())

equipos = [
    ('V1B-890', 'TRANSPORTE', 'Volvo', 'FH 540', 'Trailer Carga Pesada', 0, 245000, 'ACTIVO'),
    ('A7R-912', 'TRANSPORTE', 'Scania', 'R450', 'Tractocamión', 0, 182000, 'ACTIVO'),
    ('EXC-01', 'MAQUINARIA', 'Caterpillar', '320D', 'Excavadora Hidráulica', 4250, 0, 'ACTIVO'),
    ('CF-02', 'MAQUINARIA', 'Komatsu', 'WA380', 'Cargador Frontal', 3100, 0, 'ACTIVO'),
    ('VOL-05', 'TRANSPORTE', 'Volvo', 'FMX 8x4', 'Volquete 15m3', 1200, 95000, 'ACTIVO')
]

cursor.executemany("""
INSERT INTO equipos (codigo, tipo_sector, marca, modelo, categoria, horometro_actual, kilometraje_actual, estado)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", equipos)

personal = [
    ('Juan Carlos Mamani', '42891023', 'Conductor', '958123456', 'A-IIIc'),
    ('Bryan Francis Paz', '45891234', 'Supervisor / Admin', '954987654', 'A-I'),
    ('Manuel Huaman', '29481920', 'Operador', '951234876', 'A-IIIa'),
    ('Roberto Quispe', '41029384', 'Mecánico / Manto', '956789123', 'A-I')
]

cursor.executemany("""
INSERT INTO personal (nombre, dni, cargo, telefono, licencia)
VALUES (?, ?, ?, ?, ?)
""", personal)

partes = [
    ('2026-07-28', 1, 1, 'TRANSPORTE', 'Arequipa (Rio Seco)', 'Lima (Lurín)', 244200, 245000, 800, 'Viaje de carga seca sin novedades'),
    ('2026-07-29', 2, 1, 'TRANSPORTE', 'Matarani (Puerto)', 'Arequipa (Parque Ind)', 181600, 182000, 400, 'Traslado de contenedores'),
    ('2026-07-30', 3, 3, 'MAQUINARIA', 'Obra Yura - Cantera', '-', 4242, 4250, 8, 'Excavación de material clasificado'),
    ('2026-07-31', 4, 3, 'MAQUINARIA', 'Obra Cerro Colorado', '-', 3093, 3100, 7, 'Carga de volquetes en frente 2'),
    ('2026-08-01', 5, 1, 'TRANSPORTE', 'Arequipa', 'Moquegua', 94650, 95000, 350, 'Acarreo de agregados')
]

cursor.executemany("""
INSERT INTO partes_diarios (fecha, equipo_id, personal_id, tipo_sector, obra_origen, destino, lectura_inicial, lectura_final, unidades_trabajadas, observaciones)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", partes)

combustibles = [
    ('2026-07-28', 1, 1, 'Grifo Pecsa Vía Evitamiento', 80.0, 1200.0, 244200, 'comprobante_001.jpg', 10.0),
    ('2026-07-29', 2, 1, 'Grifo Primax Matarani', 45.0, 675.0, 181600, 'comprobante_002.jpg', 8.88),
    ('2026-07-30', 3, 3, 'Cisterna Obra Yura', 56.0, 840.0, 4242, 'comprobante_003.jpg', 0.14),
    ('2026-07-31', 4, 3, 'Cisterna Obra Cerro Colorado', 49.0, 735.0, 3093, 'comprobante_004.jpg', 0.14),
    ('2026-08-01', 5, 1, 'Grifo Coesti Socabaya', 40.0, 600.0, 94650, 'comprobante_005.jpg', 8.75)
]

cursor.executemany("""
INSERT INTO abastecimientos_combustible (fecha, equipo_id, personal_id, grifo_cisterna, galones, costo_total, lectura_momento, foto_comprobante, rendimiento_calculado)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", combustibles)

alertas = [
    (1, 'Cambio de Aceite Motor (10,000 KM)', 250000, 'PENDIENTE', 'Programar para siguiente viaje a Lima'),
    (3, 'Mantenimiento Preventivo (250 HRS)', 4250, 'VENCIDO', 'Cambio de filtro hidráulico y aceite de motor'),
    (4, 'Engrase General y Filtro Aire', 3200, 'PENDIENTE', 'Mantenimiento en 100 horas')
]

cursor.executemany("""
INSERT INTO alertas_mantenimiento (equipo_id, tipo_mantenimiento, lectura_programada, estado, descripcion)
VALUES (?, ?, ?, ?, ?)
""", alertas)

conn.commit()

# Dump backup SQL
with open("/working_dir/c_9c876028e7cab330/demo_control_operativo/backup.sql", "w", encoding="utf-8") as f:
    for line in conn.iterdump():
        f.write(f'{line}\n')

conn.close()

print("Base de datos SQLite en /tmp/control_operativo.db y backup.sql creados con éxito.")
