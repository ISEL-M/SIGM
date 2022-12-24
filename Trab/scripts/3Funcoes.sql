\set db sigm
\set user postgres
\connect :db :user

\echo 'A definir funções e operadores...'

CREATE OPERATOR * (
leftarg = t_vector,
rightarg = REAL,
procedure = produto_vector_por_escalar_SQL,
commutator = *
);

CREATE OPERATOR + (
leftarg = t_vector,
rightarg = t_vector,
procedure = soma_vector_vector,
commutator = +
);

CREATE OR REPLACE FUNCTION produto_vector_por_escalar( vec t_vector, v REAL )
RETURNS t_vector
AS $$
new_x = vec[ "x" ] * float( v )
new_y = vec[ "y" ] * float( v )
return { "x": new_x, "y": new_y }
$$ LANGUAGE plpython3u;


----------------------------------------------------
CREATE OR REPLACE FUNCTION normalizar( vec t_vector )
RETURNS t_vector
AS $$
from math import sqrt
norma = sqrt(vec[ "x" ]**2 + vec[ "y" ]**2)
res_x = vec[ "x" ] / norma
res_y = vec[ "y" ] / norma
return { "x": res_x, "y": res_y }
$$ LANGUAGE plpython3u;


----------------------------------------------------
CREATE OR REPLACE FUNCTION soma_vector_vector( vec_a t_vector, vec_b t_vector )
RETURNS t_vector
AS $$
res_x = vec_a[ "x" ] + vec_b[ "x" ]
res_y = vec_a[ "y" ] + vec_b[ "y" ]
return { "x": res_x, "y": res_y }
$$ LANGUAGE plpython3u;


----------------------------------------------------
CREATE OR REPLACE FUNCTION nova_aceleracao_linear( g_posicao_perseguidor GEOMETRY, g_posicao_alvo GEOMETRY, velocidade_a_perseguir REAL )
RETURNS t_vector
AS $$
SELECT ( 
	SELECT normalizar( (ST_X($2)-ST_X($1), ST_Y($2)-ST_Y($1))::t_vector )
	) * $3
$$ LANGUAGE 'sql';


----------------------------------------------------
CREATE OR REPLACE FUNCTION obter_aceleracao_perseguidor( id_perseguidor INTEGER, id_alvo INTEGER, velocidade_a_perseguir REAL )
RETURNS t_aceleracao
AS $$
SELECT nova_aceleracao_linear( c_perseguidor.g_posicao, c_alvo.g_posicao, $3 ), (c_perseguidor.aceleracao).angular
FROM cinematica c_perseguidor, cinematica c_alvo
WHERE c_perseguidor.id = $1 and c_alvo.id = $2;
$$ LANGUAGE 'sql';


----------------------------------------------------
-- Obter a nova posicao do objecto no instante 'tempo'
-- Formulacao: return g_posicao + velocidade.linear * tempo

CREATE OR REPLACE FUNCTION nova_posicao( g_posicao GEOMETRY, velocidade t_velocidade, tempo REAL )
RETURNS GEOMETRY
AS $$
SELECT
ST_Translate( $1,
              (($2).linear * $3 ).x,
              (($2).linear * $3 ).y )
$$ LANGUAGE 'sql';


----------------------------------------------------
-- Obter a nova orientacao do objecto no instante 'tempo'
-- Formulacao: return orientacao + velocidade.angular * tempo

CREATE OR REPLACE FUNCTION nova_orientacao( orientacao REAL, velocidade t_velocidade, tempo REAL )
RETURNS REAL
AS $$
new_orientacao = orientacao + velocidade[ "angular" ] * tempo
return new_orientacao
$$ LANGUAGE plpython3u;


----------------------------------------------------
--Obter a nova velocidade do objecto no instante 'tempo'
-- Formulacao:
-- velocidade.linear + aceleracao.linear * tempo
-- velocidade.angular + aceleracao.angular * tempo

CREATE OR REPLACE FUNCTION nova_velocidade( velocidade t_velocidade, aceleracao t_aceleracao, tempo REAL )
RETURNS t_velocidade
AS $$
SELECT ( ($1).linear + (($2).linear * ($3)), ($1).angular + ($2).angular * ($3) )::t_velocidade;
$$ LANGUAGE 'sql';


----------------------------------------------------
-- Obter a nova aceleracao linear do objecto para REALizar uma perseguicao
-- Formulacao: aceleracao = normalizar( g_posicao_alvo - g_posicao_perseguidor ) * velocidade_a_perseguir

CREATE OR REPLACE FUNCTION nova_aceleracao_linear( g_posicao_perseguidor GEOMETRY, g_posicao_alvo GEOMETRY, velocidade_a_perseguir REAL )
RETURNS t_vector
AS $$
SELECT ( 
	SELECT normalizar( (ST_X($2)-ST_X($1), ST_Y($2)-ST_Y($1))::t_vector )
	) * $3
$$ LANGUAGE 'sql';


----------------------------------------------------
-- Obter a nova aceleracao (linear e angular) do 'id_perseguidor' a perseguir 'id_alvo'
-- (invocar nova_aceleracao_linear e manter a aceleracao angular do 'id_alvo'

CREATE OR REPLACE FUNCTION obter_aceleracao_perseguidor( id_perseguidor INTEGER, id_alvo INTEGER, velocidade_a_perseguir REAL )
RETURNS t_aceleracao
AS $$
SELECT nova_aceleracao_linear( c_perseguidor.g_posicao, c_alvo.g_posicao, $3 ), (c_perseguidor.aceleracao).angular
FROM cinematica c_perseguidor, cinematica c_alvo
WHERE c_perseguidor.id = $1 and c_alvo.id = $2;
$$ LANGUAGE 'sql';
