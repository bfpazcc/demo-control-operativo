-- ESQUEMA DE BASE DE DATOS UNIFICADO: TRANSPORTE Y MAQUINARIA PESADA
-- Compatible con SQLite y PostgreSQL (Supabase / Servidor Propio)

CREATE TABLE IF NOT EXISTS equipos (
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

CREATE TABLE IF NOT EXISTS personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    dni TEXT UNIQUE NOT NULL,
    cargo TEXT NOT NULL,                 -- 'Conductor', 'Operador', 'Mecánico', 'Supervisor'
    telefono TEXT,
    licencia TEXT
);

CREATE TABLE IF NOT EXISTS partes_diarios (
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

CREATE TABLE IF NOT EXISTS abastecimientos_combustible (
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

CREATE TABLE IF NOT EXISTS alertas_mantenimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER NOT NULL,
    tipo_mantenimiento TEXT NOT NULL,    -- 'Cambio Aceite Motor', 'Filtro Aire', 'Engrase', 'Llantas'
    lectura_programada REAL NOT NULL,    -- KM o Horas a las que le toca
    estado TEXT DEFAULT 'PENDIENTE',      -- 'PENDIENTE', 'REALIZADO', 'VENCIDO'
    descripcion TEXT,
    FOREIGN KEY(equipo_id) REFERENCES equipos(id)
);
