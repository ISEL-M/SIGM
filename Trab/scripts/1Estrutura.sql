-- PostgreSQL 14.5 + PostGIS 3.2

\echo 'A inicializar estrutura...'

/*
Portugal Continental - Sistemas Globais
- EPSG: 4936 (ETRS89/ Coordenadas Geocêntricas)
- EPSG: 4937 (ETRS89/ Coordenadas Geográficas 3D)
- EPSG: 4258 (ETRS89/ Coordenadas Geográficas 2D)
- EPSG: 3763 (ETRS89/ PT-TM06)

 
Portugal Continental - Sistemas Locais
- EPSG: 4274 (Datum 73/ Coordenadas Geográficas 2D)
- EPSG: 27493 (Datum 73/ Hayford-Gauss)
- EPSG: 4207 (Datum Lisboa/ Coordenadas Geográficas 2D)
- EPSG: 5018 (Datum Lisboa/ Hayford-Gauss)
- EPSG: 20790 (Datum Lisboa/ Hayford-Gauss com falsa origem - Coordenadas Militares)
*/

\set db sigm
\set user postgres

DROP DATABASE IF EXISTS :db;
CREATE DATABASE :db;

\connect :db :user

CREATE EXTENSION postgis;

CREATE TYPE t_vector AS (
 x REAL,
 y REAL
);

CREATE TYPE t_vel AS (
	linear t_vector,
	angular REAL
);

CREATE TYPE t_acc AS (
	linear t_vector,
	angular REAL
);

\set srid 3763

CREATE TABLE rio (
    id_rio SERIAL PRIMARY KEY,
    canal GEOMETRY(LINESTRING, :srid) NOT NULL,
    leito REAL NOT NULL
);

CREATE TABLE tipo_terreno (
    designacao VARCHAR(30) PRIMARY KEY,
    profundidade INTEGER UNIQUE
);

CREATE TABLE tipo_objeto (
    designacao VARCHAR(30) PRIMARY KEY,
    fig_geo GEOMETRY(POLYGON, :srid) NOT NULL,
    v_max t_vel NOT NULL,
    a_max t_acc NOT NULL
);

CREATE TABLE terreno (
    id_terreno SERIAL PRIMARY KEY,
    tipo_terreno VARCHAR(30) REFERENCES tipo_terreno(designacao) ON DELETE CASCADE,
    regiao GEOMETRY(POLYGON, :srid) NOT NULL
);

CREATE TABLE objeto_movel (
    id_objeto SERIAL PRIMARY KEY,
    tipo_objeto VARCHAR(30) REFERENCES tipo_objeto(designacao) ON DELETE CASCADE,
    posicao GEOMETRY(POINT, :srid) NOT NULL,
    velocidade t_vel NOT NULL,
    aceleracao t_acc NOT NULL
);

CREATE TABLE perseguicao (
    id_perseguidor INTEGER REFERENCES objeto_movel(id_objeto) ON DELETE CASCADE,
    id_alvo INTEGER REFERENCES objeto_movel(id_objeto) ON DELETE CASCADE,
    fator_mult REAL NOT NULL,
    PRIMARY KEY (id_perseguidor, id_alvo)
);

CREATE TABLE historico_posicao (
    id_objeto INTEGER REFERENCES objeto_movel(id_objeto) ON DELETE CASCADE,
    instante_t REAL NOT NULL, -- TIMESTAMP?
    posicao GEOMETRY(POINT, :srid) NOT NULL,
    orientacao REAL NOT NULL,
    PRIMARY KEY (id_objeto, instante_t)
);

CREATE TABLE cinematica (
    tipo_terreno VARCHAR(30) NOT NULL REFERENCES tipo_terreno(designacao) ON DELETE CASCADE,
    tipo_objeto VARCHAR(30) NOT NULL REFERENCES tipo_terreno(designacao) ON DELETE CASCADE,
    fator_mult REAL NOT NULL DEFAULT 1.0, -- CHECK (fator_mult > 0),
    PRIMARY KEY (tipo_terreno, tipo_objeto)
);