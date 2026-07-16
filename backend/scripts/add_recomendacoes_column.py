#!/usr/bin/env python
"""
Migração simples: adiciona coluna recomendacoes_terapeuta à tabela evolucoes
"""
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine
from sqlalchemy import text

def migrate():
    """Adiciona a coluna recomendacoes_terapeuta se não existir"""
    with engine.connect() as conn:
        # Verifica se a coluna já existe
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evolucoes' AND column_name = 'recomendacoes_terapeuta'
        """))
        
        if result.fetchone():
            print("✅ Coluna 'recomendacoes_terapeuta' já existe")
            return
        
        # Adiciona a coluna
        conn.execute(text("""
            ALTER TABLE evolucoes 
            ADD COLUMN recomendacoes_terapeuta TEXT
        """))
        conn.commit()
        print("✅ Coluna 'recomendacoes_terapeuta' adicionada com sucesso!")

if __name__ == "__main__":
    migrate()