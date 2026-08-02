BEGIN TRANSACTION;
CREATE TABLE abastecimientos_combustible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    equipo_id INTEGER NOT NULL,
    personal_id INTEGER NOT NULL,
    grifo_cisterna TEXT NOT NULL,        -- Nombre de grifo o cisterna en obra
    galones REAL NOT NULL,
    costo_total REAL NOT NULL,
    lectura_momento REAL NOT NULL,       -- KM o Horómetro al momento de abastecer
    foto_comprobante TEXT,                -- URL o ruta de foto
    rendimiento_calculado REAL,          -- KM/Galón o Horas/Galón
    FOREIGN KEY(equipo_id) REFERENCES equipos(id),
    FOREIGN KEY(personal_id) REFERENCES personal(id)
);
INSERT INTO "abastecimientos_combustible" VALUES(1,'2026-07-28',1,1,'Grifo Pecsa Vía Evitamiento',80.0,1200.0,244200.0,'comprobante_001.jpg',10.0);
INSERT INTO "abastecimientos_combustible" VALUES(2,'2026-07-29',2,1,'Grifo Primax Matarani',45.0,675.0,181600.0,'comprobante_002.jpg',8.88);
INSERT INTO "abastecimientos_combustible" VALUES(3,'2026-07-30',3,3,'Cisterna Obra Yura',56.0,840.0,4242.0,'comprobante_003.jpg',0.14);
INSERT INTO "abastecimientos_combustible" VALUES(4,'2026-07-31',4,3,'Cisterna Obra Cerro Colorado',49.0,735.0,3093.0,'comprobante_004.jpg',0.14);
INSERT INTO "abastecimientos_combustible" VALUES(5,'2026-08-01',5,1,'Grifo Coesti Socabaya',40.0,600.0,94650.0,'comprobante_005.jpg',8.75);
CREATE TABLE alertas_mantenimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER NOT NULL,
    tipo_mantenimiento TEXT NOT NULL,    -- 'Cambio Aceite Motor', 'Filtro Aire', 'Engrase', 'Llantas'
    lectura_programada REAL NOT NULL,    -- KM o Horas a las que le toca
    estado TEXT DEFAULT 'PENDIENTE',      -- 'PENDIENTE', 'REALIZADO', 'VENCIDO'
    descripcion TEXT,
    FOREIGN KEY(equipo_id) REFERENCES equipos(id)
);
INSERT INTO "alertas_mantenimiento" VALUES(1,1,'Cambio de Aceite Motor (10,000 KM)',250000.0,'PENDIENTE','Programar para siguiente viaje a Lima');
INSERT INTO "alertas_mantenimiento" VALUES(2,3,'Mantenimiento Preventivo (250 HRS)',4250.0,'VENCIDO','Cambio de filtro hidráulico y aceite de motor');
INSERT INTO "alertas_mantenimiento" VALUES(3,4,'Engrase General y Filtro Aire',3200.0,'PENDIENTE','Mantenimiento en 100 horas');
CREATE TABLE equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,          -- Placa o Código de Máquina (ej: V1B-890, EXC-01)
    tipo_sector TEXT NOT NULL,           -- 'TRANSPORTE' o 'MAQUINARIA'
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    categoria TEXT NOT NULL,             -- 'Trailer', 'Volquete', 'Excavadora', 'Cargador Frontal'
    horometro_actual REAL DEFAULT 0,     -- Horas acumuladas (para maquinaria)
    kilometraje_actual REAL DEFAULT 0,   -- KM acumulados (para transporte)
    estado TEXT DEFAULT 'ACTIVO'         -- 'ACTIVO', 'MANTENIMIENTO', 'INACTIVO'
);
INSERT INTO "equipos" VALUES(1,'V1B-890','TRANSPORTE','Volvo','FH 540','Trailer Carga Pesada',0.0,245000.0,'ACTIVO');
INSERT INTO "equipos" VALUES(2,'A7R-912','TRANSPORTE','Scania','R450','Tractocamión',0.0,182000.0,'ACTIVO');
INSERT INTO "equipos" VALUES(3,'EXC-01','MAQUINARIA','Caterpillar','320D','Excavadora Hidráulica',4250.0,0.0,'ACTIVO');
INSERT INTO "equipos" VALUES(4,'CF-02','MAQUINARIA','Komatsu','WA380','Cargador Frontal',3100.0,0.0,'ACTIVO');
INSERT INTO "equipos" VALUES(5,'VOL-05','TRANSPORTE','Volvo','FMX 8x4','Volquete 15m3',1200.0,95000.0,'ACTIVO');
CREATE TABLE partes_diarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    equipo_id INTEGER NOT NULL,
    personal_id INTEGER NOT NULL,
    tipo_sector TEXT NOT NULL,
    obra_origen TEXT NOT NULL,            -- Frente de trabajo u Origen del viaje
    destino TEXT,                         -- Destino (para transporte)
    lectura_inicial REAL NOT NULL,        -- KM o Horómetro Inicial
    lectura_final REAL NOT NULL,          -- KM o Horómetro Final
    unidades_trabajadas REAL NOT NULL,    -- KM recorridos u Horas trabajadas
    observaciones TEXT,
    FOREIGN KEY(equipo_id) REFERENCES equipos(id),
    FOREIGN KEY(personal_id) REFERENCES personal(id)
);
INSERT INTO "partes_diarios" VALUES(1,'2026-07-28',1,1,'TRANSPORTE','Arequipa (Rio Seco)','Lima (Lurín)',244200.0,245000.0,800.0,'Viaje de carga seca sin novedades');
INSERT INTO "partes_diarios" VALUES(2,'2026-07-29',2,1,'TRANSPORTE','Matarani (Puerto)','Arequipa (Parque Ind)',181600.0,182000.0,400.0,'Traslado de contenedores');
INSERT INTO "partes_diarios" VALUES(3,'2026-07-30',3,3,'MAQUINARIA','Obra Yura - Cantera','-',4242.0,4250.0,8.0,'Excavación de material clasificado');
INSERT INTO "partes_diarios" VALUES(4,'2026-07-31',4,3,'MAQUINARIA','Obra Cerro Colorado','-',3093.0,3100.0,7.0,'Carga de volquetes en frente 2');
INSERT INTO "partes_diarios" VALUES(5,'2026-08-01',5,1,'TRANSPORTE','Arequipa','Moquegua',94650.0,95000.0,350.0,'Acarreo de agregados');
CREATE TABLE personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    dni TEXT UNIQUE NOT NULL,
    cargo TEXT NOT NULL,                 -- 'Conductor', 'Operador', 'Mecánico', 'Supervisor'
    telefono TEXT,
    licencia TEXT
);
INSERT INTO "personal" VALUES(1,'Juan Carlos Mamani','42891023','Conductor','958123456','A-IIIc');
INSERT INTO "personal" VALUES(2,'Bryan Francis Paz','45891234','Supervisor / Admin','954987654','A-I');
INSERT INTO "personal" VALUES(3,'Manuel Huaman','29481920','Operador','951234876','A-IIIa');
INSERT INTO "personal" VALUES(4,'Roberto Quispe','41029384','Mecánico / Manto','956789123','A-I');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('equipos',5);
INSERT INTO "sqlite_sequence" VALUES('personal',4);
INSERT INTO "sqlite_sequence" VALUES('partes_diarios',5);
INSERT INTO "sqlite_sequence" VALUES('abastecimientos_combustible',5);
INSERT INTO "sqlite_sequence" VALUES('alertas_mantenimiento',3);
COMMIT;
