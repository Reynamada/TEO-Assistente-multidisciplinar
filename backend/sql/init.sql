-- TEO — Script de inicialização do PostgreSQL
-- Executado automaticamente pelo Docker ao criar o container

-- Extensão para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Comentário no banco
COMMENT ON DATABASE teo_db IS 'TEO — Tu Enlace Organizador | Sistema de IA para Clínicas de Neurodesenvolvimento';
