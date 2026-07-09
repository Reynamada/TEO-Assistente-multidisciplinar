"""
TEO — Script de Seed para o Banco de Dados.
Popula a base de dados com profissionais de todas as especialidades,
pacientes de teste (incluindo um vencido há mais de 150 dias) e evoluções clínicas completas.
"""
import sys
import os
from datetime import date, datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Ajusta sys.path para garantir que o pacote app seja encontrado
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models.professional import Professional, ProfessionalRole, ProfessionalEspecialidade
from app.models.patient import Patient
from app.models.evolution import Evolution
from app.models.appointment import Appointment, AppointmentStatus
from app.models.report import Report

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def run_seed():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("🧩 TEO — Iniciando Seed Completo de Dados...")
    
    # Garante que as tabelas estejam criadas no banco de dados
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        print("🧹 Limpando dados antigos do banco de dados (respeitando FKs)...")
        db.query(Report).delete()
        db.query(Appointment).delete()
        db.query(Evolution).delete()
        db.query(Patient).delete()
        db.query(Professional).delete()
        db.commit()
        print("✅ Banco de dados limpo com sucesso!")

        # ──────────────────────────────────────────────────────────────────────
        # 1. CRIANDO PROFISSIONAIS
        # ──────────────────────────────────────────────────────────────────────
        print("👤 Criando Profissionais da Clínica...")
        senha_padrao = get_password_hash("123456")
        
        admin = Professional(
            nome="Reyna Admin",
            email="adminReyna@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.ADMIN,
            especialidade=None
        )
        
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
        
        terapeuta_to = Professional(
            nome="Marcos (Terapia Ocupacional)",
            email="marcos@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.TERAPIA_OCUPACIONAL,
            registro_conselho="CREFITO-3 9876-TO"
        )
        
        terapeuta_fono = Professional(
            nome="Camila (Fonoaudiologia)",
            email="camila@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.FONOAUDIOLOGIA,
            registro_conselho="CRFa-2 5432"
        )
        
        terapeuta_psicologia = Professional(
            nome="Patrícia (Psicologia)",
            email="patricia@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.PSICOLOGIA,
            registro_conselho="CRP-06/98765"
        )
        
        terapeuta_psicopedagogia = Professional(
            nome="Sandra (Psicopedagogia)",
            email="sandra@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.PSICOPEDAGOGIA,
            registro_conselho="ABPp-SP 1234"
        )
        
        terapeuta_fisioterapia = Professional(
            nome="Fábio (Fisioterapia)",
            email="fabio@clinica.com",
            hashed_password=senha_padrao,
            role=ProfessionalRole.TERAPEUTA,
            especialidade=ProfessionalEspecialidade.FISIOTERAPIA,
            registro_conselho="CREFITO-3 11223-F"
        )
        
        db.add_all([
            admin, neuropediatra, recepcao,
            terapeuta_to, terapeuta_fono,
            terapeuta_psicologia, terapeuta_psicopedagogia, terapeuta_fisioterapia
        ])
        db.commit()
        
        # Recarrega as IDs dos profissionais
        db.refresh(admin)
        db.refresh(neuropediatra)
        db.refresh(terapeuta_to)
        db.refresh(terapeuta_fono)
        db.refresh(terapeuta_psicologia)
        db.refresh(terapeuta_psicopedagogia)
        db.refresh(terapeuta_fisioterapia)
        print("✅ 8 Profissionais criados!")

        # ──────────────────────────────────────────────────────────────────────
        # 2. CRIANDO PACIENTES
        # ──────────────────────────────────────────────────────────────────────
        print("👶 Criando Pacientes...")
        hoje = date.today()
        
        # Paciente 1: Mateo García - Laudo vencido para simulação (regra dos 5 meses / 150 dias)
        paciente_mateo = Patient(
            nome="Mateo García",
            data_nascimento=date(2018, 4, 15),
            diagnostico_principal="TEA Nível 2",
            nome_responsavel="Sra. García (Mãe)",
            whatsapp_responsavel="+5511999999999", # Sandbox ou número real para testes
            email_responsavel="garcia.mae@email.com",
            data_ultimo_laudo=hoje - timedelta(days=155), # Vencido (>150 dias) para simular alerta de laudo
            neuropediatra_id=neuropediatra.id,
            ativo=True,
            observacoes="Apresenta sensibilidade auditiva a ruídos agudos e interesse restrito em dinossauros."
        )
        
        # Paciente 2: Sofia Mendes - Laudo recente (em dia)
        paciente_sofia = Patient(
            nome="Sofia Mendes",
            data_nascimento=date(2020, 8, 20),
            diagnostico_principal="TEA Nível 1",
            nome_responsavel="Sr. Mendes (Pai)",
            whatsapp_responsavel="+5511888888888",
            email_responsavel="mendes.pai@email.com",
            data_ultimo_laudo=hoje - timedelta(days=30), # Em dia
            neuropediatra_id=neuropediatra.id,
            ativo=True,
            observacoes="Foco em flexibilidade cognitiva, turnos sociais e desorganização emocional diante de quebras de rotina."
        )
        
        # Paciente 3: Lucas Silva - Laudo recente (em dia)
        paciente_lucas = Patient(
            nome="Lucas Silva",
            data_nascimento=date(2019, 11, 10),
            diagnostico_principal="TEA Nível 3",
            nome_responsavel="Sra. Silva (Mãe)",
            whatsapp_responsavel="+5511777777777",
            email_responsavel="silva.mae@email.com",
            data_ultimo_laudo=hoje - timedelta(days=45), # Em dia
            neuropediatra_id=neuropediatra.id,
            ativo=True,
            observacoes="Apresenta hipotonia muscular generalizada, atraso motor grosso e dispraxia orofacial."
        )
        
        db.add_all([paciente_mateo, paciente_sofia, paciente_lucas])
        db.commit()
        
        # Recarrega as IDs dos pacientes
        db.refresh(paciente_mateo)
        db.refresh(paciente_sofia)
        db.refresh(paciente_lucas)
        print("✅ 3 Pacientes criados (Mateo García está VENCIDO para testes)!")

        # ──────────────────────────────────────────────────────────────────────
        # 3. CRIANDO LAUDOS INICIAIS DO NEUROPEDIATRA
        # ──────────────────────────────────────────────────────────────────────
        print("📄 Criando Laudos Iniciais de Neuropediatria...")
        
        laudo_mateo = Report(
            paciente_id=paciente_mateo.id,
            assinado_por=neuropediatra.id,
            periodo_inicio=hoje - timedelta(days=180),
            periodo_fim=hoje,
            sintese_global=(
                "[SÍNTESE GLOBAL]\n"
                "Paciente Mateo García, 6 anos, avaliado nesta clínica. Apresenta diagnóstico clínico compatível com "
                "Transtorno do Espectro Autista (TEA Nível 2). Identificou-se atraso significativo no desenvolvimento "
                "da linguagem expressiva (ecolalias imediatas) e disfunção de integração sensorial de padrão tátil e vestibular.\n\n"
                "[EVOLUÇÃO POR ÁREA]\n"
                "Em Terapia Ocupacional, o paciente demonstrou excelente ganho de modulação sensorial tátil, tolerando brincadeiras em texturas secas e circuitos corporais por até 15 minutos sem sinais de aversão ou desorganização. "
                "Em Fonoaudiologia, apresentou melhora expressiva na atenção compartilhada e persistência no uso de comunicação alternativa (PECS Nível 2), buscando a pasta em outros ambientes de forma autônoma.\n\n"
                "[LAUDO CONCLUSIVO E RECOMENDAÇÕES]\n"
                "Diante da evolução apresentada e das necessidades terapêuticas contínuas, ratifica-se a indicação de acompanhamento multidisciplinar especializado:\n"
                "- Terapia Ocupacional com foco em Integração Sensorial: 2x/semana (sugere-se estimulação vestibular e treino de AVDs de alimentação);\n"
                "- Fonoaudiologia com foco em comunicação alternativa e ampliação de vocabulário funcional: 2x/semana (sugere-se avanço para PECS Nível 3);\n"
                "Recomenda-se ambiente escolar estruturado com apoio visual e pausas sensoriais. Retorno agendado com a Neuropediatria em 5 meses para reavaliação de laudo."
            ),
            num_evolucoes_analisadas="8",
            pdf_path=None,
            pdf_gerado_em=None,
            pareceres_json=(
                '{"Terapia Ocupacional": "Estimular modulação sensorial de estímulos táteis e proprioceptivos. Foco em AVDs de alimentação.", '
                '"Fonoaudiologia": "Foco em atenção compartilhada e pareamento visual no PECS (transição para Nível 3)."}'
            )
        )
        
        laudo_sofia = Report(
            paciente_id=paciente_sofia.id,
            assinado_por=neuropediatra.id,
            periodo_inicio=hoje - timedelta(days=60),
            periodo_fim=hoje,
            sintese_global=(
                "[SÍNTESE GLOBAL]\n"
                "Paciente Sofia Mendes, 5 anos. Diagnóstico de TEA Nível 1. Apresenta rigidez cognitiva, resistência a "
                "mudanças de atividades e baixa tolerância à frustração acadêmica.\n\n"
                "[EVOLUÇÃO POR ÁREA]\n"
                "Em Psicologia, obteve grande avanço na regulação das emoções básicas e no manejo de frustrações, conseguindo verbalizar 'estou brava' em vez de emitir comportamentos disruptivos durante jogos com turnos. "
                "Em Psicopedagogia, o tempo de atenção focada em atividades de mesa expandiu para 10 minutos, completando quebra-cabeças e identificando vogais com autonomia.\n\n"
                "[LAUDO CONCLUSIVO E RECOMENDAÇÕES]\n"
                "Prescrito acompanhamento contínuo em Psicologia Analítico-Comportamental (2x/semana) com foco em flexibilização cognitiva e autorregulação, "
                "e Psicopedagogia (1x/semana) para estimulação das funções executivas e pré-requisitos de alfabetização. Orienta-se à escola o uso de rotina visual e antecipação das mudanças de tarefas."
            ),
            num_evolucoes_analisadas="8",
            pdf_path=None,
            pdf_gerado_em=None,
            pareceres_json=(
                '{"Psicologia": "Flexibilização de rotina e redução de comportamentos disruptivos baseados em esquiva. Estimulação de mando/tacto de emoções.", '
                '"Psicopedagogia": "Estimulação de memória de trabalho e raciocínio lógico-matemático (atenção sustentada)."}'
            )
        )
        
        laudo_lucas = Report(
            paciente_id=paciente_lucas.id,
            assinado_por=neuropediatra.id,
            periodo_inicio=hoje - timedelta(days=75),
            periodo_fim=hoje,
            sintese_global=(
                "[SÍNTESE GLOBAL]\n"
                "Paciente Lucas Silva, 6 anos. Diagnóstico de TEA Nível 3. Apresenta atraso motor severo com hipotonia "
                "de tronco e dispraxia orofacial com escape salivar (sialorréia) constante.\n\n"
                "[EVOLUÇÃO POR ÁREA]\n"
                "Em Fisioterapia Motora, alcançou excelente ganho de força e equilíbrio dinâmico, sendo capaz de caminhar 20 metros em solo estável sem suporte físico. "
                "Em Fonoaudiologia, aumentou a tonicidade labial e reduziu significativamente o escape salivar através de exercícios orofaciais e uso de canudos de grosso calibre.\n\n"
                "[LAUDO CONCLUSIVO E RECOMENDAÇÕES]\n"
                "Mantém-se indicação de Fisioterapia Motora Global (2x/semana) para fortalecimento de tronco e equilíbrio monopodal, "
                "e Fonoaudiologia com foco em motricidade orofacial, deglutição e praxias não-verbais (2x/semana). Recomendado uso de copo adaptado e supervisão em deslocamentos no ambiente domiciliar/escolar."
            ),
            num_evolucoes_analisadas="8",
            pdf_path=None,
            pdf_gerado_em=None,
            pareceres_json=(
                '{"Fisioterapia": "Treino de equilíbrio estático/dinâmico e fortalecimento de cadeia posterior. Marcha autônoma.", '
                '"Fonoaudiologia": "Estimulação de tonicidade labial e vedamento orofacial contra escape de saliva."}'
            )
        )
        
        db.add_all([laudo_mateo, laudo_sofia, laudo_lucas])
        db.commit()
        print("✅ 3 Laudos Iniciais de Neuropediatria inseridos!")

        # ──────────────────────────────────────────────────────────────────────
        # 4. CRIANDO HISTÓRICO DE EVOLUÇÕES CLÍNICAS
        # ──────────────────────────────────────────────────────────────────────
        print("📝 Criando Histórico de Evoluções Semanais...")
        evolucoes = []
        
        # Datas das últimas 4 semanas (uma sessão por semana por terapeuta)
        datas = [hoje - timedelta(days=i*7) for i in range(1, 5)]
        
        # ── 4.1 Evoluções de Mateo García (Marcos de TO e Camila de Fono) ──────
        notas_to_mateo = [
            "Sessão 1: Paciente apresentou desorganização sensorial tátil frente a estímulo com tinta guache. Necessitou de regulação com propriocepção (compressão articular e tração). Ao final, tolerou brincadeira de encaixe por 5 minutos.",
            "Sessão 2: Trabalhado treino de AVDs (alimentação). Apresentou melhora no manuseio da colher, porém com padrão de preensão palmar imaturo. Realizada facilitação neuromuscular. Apresentou boa resposta a estímulos vestibulares.",
            "Sessão 3: Sessão focada em planejamento motor e práxis global. Paciente realizou circuito motor (rampa, túnel e cama elástica) com mediação verbal mínima. Apresentou aumento de engajamento social.",
            "Sessão 4: Paciente demonstrou grande evolução na modulação sensorial. Tolerou estímulo de texturas diversas (feijão, arroz e areia) por 15 minutos sem sinais de aversão. Excelente ganho de autorregulação."
        ]
        
        notas_fono_mateo = [
            "Sessão 1: Avaliação da comunicação expressiva. Paciente utiliza gestos instrumentalizados e ecolalias imediatas para solicitar objetos de interesse. Iniciado pareamento de estímulo sonoro com apoio visual.",
            "Sessão 2: Sessão focada em contato visual sustentado e atenção compartilhada. Paciente manteve contato visual por até 4 segundos durante brincadeira de sopro de bolhas de sabão. Uso consistente do PECS nível 1.",
            "Sessão 3: Trabalhado turno comunicativo e imitação vocal. Paciente conseguiu realizar 3 trocas de turno em brincadeira simbólica com carrinhos. Emitiu fonemas bilabiais /p/ e /b/ de forma funcional.",
            "Sessão 4: Excelente evolução no uso do PECS nível 2 (distância e persistência). Paciente buscou a pasta de comunicação em outro ambiente para solicitar água. Redução significativa das ecolalias."
        ]

        for i, data_s in enumerate(datas):
            # TO Marcos
            evolucoes.append(Evolution(
                paciente_id=paciente_mateo.id,
                profissional_id=terapeuta_to.id,
                data_sessao=data_s,
                tipo_sessao="Terapia Ocupacional",
                duracao_minutos="50",
                notas_tecnicas=notas_to_mateo[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Trabalhamos a regulação tátil e corporal com circuitos e estímulos táteis.\n"
                    "🌟 Grande conquista: O Mateo conseguiu brincar na caixa de texturas de feijão e arroz por 15 minutos muito focado!\n"
                    "🏠 Dica para casa: Deixem-no brincar de colocar as mãos em potes de grãos secos para continuar a regulação."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))
            # Fono Camila
            evolucoes.append(Evolution(
                paciente_id=paciente_mateo.id,
                profissional_id=terapeuta_fono.id,
                data_sessao=data_s,
                tipo_sessao="Fonoaudiologia",
                duracao_minutos="50",
                notas_tecnicas=notas_fono_mateo[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Focamos no contato visual e no uso do álbum de comunicação PECS.\n"
                    "🌟 Grande conquista: Mateo buscou o álbum de forma autônoma em outro cômodo para pedir água. Excelente!\n"
                    "🏠 Dica para casa: Estimulem o Mateo a apontar ou usar a pasta de figuras antes de entregar o que ele quer."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))

        # ── 4.2 Evoluções de Sofia Mendes (Patrícia de Psico e Sandra de Psicoped) ──
        notas_psico_sofia = [
            "Sessão 1: Avaliação do comportamento social e autorregulação emocional. Paciente apresentou rigidez cognitiva diante da mudança de rotina na sala (retirada de brinquedo favorito), resultando em crise de choro auto-limitada de 5 minutos.",
            "Sessão 2: Trabalhada flexibilidade cognitiva através de jogos de regras simples com turnos alternados. Paciente tolerou perder sem desregulação, utilizando estratégias de respiração treinadas.",
            "Sessão 3: Foco em identificação de emoções básicas (alegria, tristeza, raiva) usando cartões ilustrados. Paciente nomeou as emoções corretamente e associou a situações do seu cotidiano.",
            "Sessão 4: Paciente demonstrou excelente avanço na regulação emocional. Conseguiu expressar frustração verbalmente ('estou brava') in vez de apresentar comportamento disruptivo. Ótimo ganho de repertório."
        ]
        
        notas_psicoped_sofia = [
            "Sessão 1: Avaliação de habilidades acadêmicas e atenção focada. Paciente apresenta dificuldade em manter a atenção por mais de 3 minutos in atividades de mesa. Iniciado uso de cronômetro visual.",
            "Sessão 2: Trabalhado pareamento de cores, formas geométricas e pareamento de letras do próprio nome. Paciente manteve atenção focada por 6 minutos utilizando reforço positivo intermitente.",
            "Sessão 3: Sessão de estimulação cognitiva (memória de trabalho e sequenciamento). Paciente completou quebra-cabeça de 12 peças de forma autônoma e seguiu sequência de 3 comandos verbais.",
            "Sessão 4: Grande avanço acadêmico: paciente identificou todas as vogais e realizou contagem numérica de 1 a 10 com apoio concreto. Tempo de atenção focada expandido para 10 minutos."
        ]

        for i, data_s in enumerate(datas):
            # Psico Patrícia
            evolucoes.append(Evolution(
                paciente_id=paciente_sofia.id,
                profissional_id=terapeuta_psicologia.id,
                data_sessao=data_s,
                tipo_sessao="Psicologia",
                duracao_minutos="50",
                notas_tecnicas=notas_psico_sofia[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Trabalhamos a flexibilidade cognitiva e a regulação das emoções básicas.\n"
                    "🌟 Grande conquista: A Sofia conseguiu usar as palavras para dizer que estava chateada ao invés de chorar.\n"
                    "🏠 Dica para casa: Reforcem positivamente sempre que ela expressar suas vontades verbalmente de forma calma."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))
            # Psicoped Sandra
            evolucoes.append(Evolution(
                paciente_id=paciente_sofia.id,
                profissional_id=terapeuta_psicopedagogia.id,
                data_sessao=data_s,
                tipo_sessao="Psicopedagogia",
                duracao_minutos="50",
                notas_tecnicas=notas_psicoped_sofia[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Estimulamos a atenção sustentada in atividades de mesa e pareamento de letras.\n"
                    "🌟 Grande conquista: Sofia montou um quebra-cabeça de 12 peças sozinha e focada do início ao fim.\n"
                    "🏠 Dica para casa: Incentivem pequenos jogos de encaixe ou quebra-cabeças em casa para manter o foco ativo."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))

        # ── 4.3 Evoluções de Lucas Silva (Fábio de Fisio e Camila de Fono) ──────
        notas_fisio_lucas = [
            "Sessão 1: Avaliação motora global. Paciente apresenta hipotonia muscular leve generalizada, padrão de marcha com base alargada e encurtamento de cadeia posterior. Iniciado alongamento passivo.",
            "Sessão 2: Trabalhado equilíbrio dinâmico e fortalecimento de membros inferiores. Paciente realizou exercícios de subir e descer degraus com apoio bilateral. Boa tolerância ao esforço físico.",
            "Sessão 3: Sessão focada em coordenação motora grossa e propriocepção. Paciente realizou saltos bipodais em mini-cama elástica e marcha sobre linha sinuosa no solo com auxílio físico leve.",
            "Sessão 4: Excelente ganho de força muscular em tronco e membros inferiores. Paciente já realiza marcha estável sem apoio por 20 metros. Equilíbrio estático monopodal melhorado de forma visível."
        ]
        
        notas_fono_lucas = [
            "Sessão 1: Avaliação de motricidade orofacial e sucção. Paciente apresenta escape de saliva (sialorréia) e hipotonia labial. Realizadas massagens extra e intra-orais para estimulação sensorial.",
            "Sessão 2: Trabalhado vedamento labial e sopro. Paciente utilizou canudo de calibre largo para sugar líquido espesso, demonstrando melhora na força de sucção labial. Escape salivar reduzido.",
            "Sessão 3: Foco em fonoarticulação e praxias não-verbais (bico, sorriso, estalar de língua). Paciente imitou os movimentos faciais do terapeuta com assistência visual de espelho.",
            "Sessão 4: Paciente apresentou melhora significativa na tonicidade orofacial. Salivação sob controle durante a sessão. Iniciou vocalizações direcionadas para pedir objetos."
        ]

        for i, data_s in enumerate(datas):
            # Fisio Fábio
            evolucoes.append(Evolution(
                paciente_id=paciente_lucas.id,
                profissional_id=terapeuta_fisioterapia.id,
                data_sessao=data_s,
                tipo_sessao="Fisioterapia",
                duracao_minutos="50",
                notas_tecnicas=notas_fisio_lucas[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Focamos em alongamentos de cadeia posterior e equilíbrio dinâmico global.\n"
                    "🌟 Grande conquista: O Lucas conseguiu caminhar 20 metros de forma estável e sem apoio físico hoje!\n"
                    "🏠 Dica para casa: Estimulem o Lucas a caminhar curtas distâncias sem dar as mãos, supervisionando de perto."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))
            # Fono Camila
            evolucoes.append(Evolution(
                paciente_id=paciente_lucas.id,
                profissional_id=terapeuta_fono.id,
                data_sessao=data_s,
                tipo_sessao="Fonoaudiologia",
                duracao_minutos="50",
                notas_tecnicas=notas_fono_lucas[i],
                mensagem_pais=(
                    "🧩 O que fizemos hoje: Trabalhamos a musculatura da boca e vedamento labial para evitar a salivação.\n"
                    "🌟 Grande conquista: O Lucas bebeu suco no canudo grosso vedando os lábios e controlando a saliva.\n"
                    "🏠 Dica para casa: Usem copos com canudos grossos para sucos consistentes (vitamina) para forçar o fechamento labial."
                ),
                whatsapp_enviado=True,
                whatsapp_enviado_em=datetime.now() - timedelta(days=i*7)
            ))

        db.add_all(evolucoes)
        db.commit()
        print(f"✅ {len(evolucoes)} Evoluções Clínicas adicionadas ao histórico!")

        print("="*60)
        print("🎯 Seed concluído com sucesso total na base de dados Neon!")
        print("Usuários criados para a equipe (senha padrão: 123456):")
        print("  - adminReyna@clinica.com (Administrador)")
        print("  - ana@clinica.com (Neuropediatra)")
        print("  - julia@clinica.com (Recepção)")
        print("  - marcos@clinica.com (Terapia Ocupacional)")
        print("  - camila@clinica.com (Fonoaudiologia)")
        print("  - patricia@clinica.com (Psicologia)")
        print("  - sandra@clinica.com (Psicopedagogia)")
        print("  - fabio@clinica.com (Fisioterapia)")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao rodar seed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
