import asyncio
from datetime import date, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import SessionLocal, Base, engine
from app.models.professional import Professional, ProfessionalRole, ProfessionalEspecialidade
from app.models.patient import Patient
from app.models.evolution import Evolution

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def run_seed():
    print("Iniciando Seed de Dados do TEO...")
    
    # Em um ambiente de produção real, usaríamos Alembic. Aqui garantimos as tabelas.
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Verificar se já existem dados
        if db.query(Professional).count() > 0:
            print("Banco de dados já contém Profissionais. Ignorando seed para evitar duplicação.")
            return

        print("1. Criando Profissionais...")
        senha_padrao = get_password_hash("123456")
        
        neuropediatra = Professional(
            nome="Dra. Ana Rodrigues",
            email="ana@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.NEUROPEDIATRA,
            especialidade=ProfessionalEspecialidade.NEUROPEDIATRIA,
            registro_conselho="CRM-SP 123456"
        )
        
        recepcao = Professional(
            nome="Julia Recepção",
            email="julia@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.RECEPCAO,
            especialidade=ProfessionalEspecialidade.RECEPCAO_ADM
        )
        
        to = Professional(
            nome="Marcos (Terapia Ocupacional)",
            email="marcos@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.TERAPIA_OCUPACIONAL
        )
        
        fono = Professional(
            nome="Camila (Fonoaudiologia)",
            email="camila@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.FONOAUDIOLOGIA,
        )

        admin = Professional(
            nome="Reyna Admin",
            email="adminReyna@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.ADMIN,
            especialidade=None,
        )

        db.add_all([neuropediatra, recepcao, to, fono, admin])
        db.commit()
        db.refresh(neuropediatra)
        db.refresh(to)
        db.refresh(fono)

        print("2. Criando Pacientes...")
        hoje = date.today()
        
        paciente_mateo = Patient(
            nome="Mateo García",
            data_nascimento=date(2018, 4, 15),
            diagnostico_principal="TEA Nível 1",
            nome_responsavel="Sra. García",
            whatsapp_responsavel="+5511999999999", # Mude para seu número do sandbox para testes
            data_ultimo_laudo=hoje - timedelta(days=155), # Vencido para teste do CRON
            neuropediatra_id=neuropediatra.id
        )
        
        paciente_sofia = Patient(
            nome="Sofia Mendes",
            data_nascimento=date(2020, 8, 20),
            diagnostico_principal="TEA Nível 2",
            nome_responsavel="Sr. Mendes",
            whatsapp_responsavel="+5511888888888",
            data_ultimo_laudo=hoje - timedelta(days=30), # Em dia
            neuropediatra_id=neuropediatra.id
        )

        db.add_all([paciente_mateo, paciente_sofia])
        db.commit()
        db.refresh(paciente_mateo)

        print("3. Criando Histórico de Evoluções (Mateo)...")
        evolucoes = []
        datas = [hoje - timedelta(days=i*7) for i in range(1, 6)] # Últimas 5 semanas
        
        # Evoluções de TO
        for i, d in enumerate(datas[:3]):
            evo = Evolution(
                paciente_id=paciente_mateo.id,
                profissional_id=to.id,
                data_sessao=d,
                tipo_sessao="Integração Sensorial",
                notas_tecnicas=f"Sessão {i+1}: Paciente apresentou boa tolerância a texturas. Realizadas atividades de AVDs.",
                mensagem_whatsapp_gerada="🧩 O que fizemos hoje...\n🌟 Grande conquista...\n🏠 Dica para casa...",
                whatsapp_enviado=True
            )
            evolucoes.append(evo)

        # Evoluções de Fono
        for i, d in enumerate(datas[3:]):
            evo = Evolution(
                paciente_id=paciente_mateo.id,
                profissional_id=fono.id,
                data_sessao=d,
                tipo_sessao="Linguagem Expressiva",
                notas_tecnicas=f"Sessão Fono {i+1}: Foco em imitação de gestos e uso de PECS. Atingiu 5 trocas consistentes.",
                mensagem_whatsapp_gerada="🧩 O que fizemos hoje...\n🌟 Grande conquista...\n🏠 Dica para casa...",
                whatsapp_enviado=True
            )
            evolucoes.append(evo)

        db.add_all(evolucoes)
        db.commit()

        print("Seed concluído com sucesso!")
        print("Usuários criados (senha: 123456):")
        print("- ana@clinica.com (Neuropediatra)")
        print("- julia@clinica.com (Recepção)")
        print("- marcos@clinica.com (Terapeuta TO)")
        print("- camila@clinica.com (Terapeuta Fono)")
        print("="*40)
        
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
