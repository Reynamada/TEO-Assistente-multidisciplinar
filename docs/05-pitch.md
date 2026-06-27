# Pitch (3 minutos)

## ☁️ Deploy Gratuito

Para publicar o TEO no **Streamlit Cloud** (plano gratuito):

1️⃣ Crie uma conta no [Streamlit Cloud](https://share.streamlit.io/).
2️⃣ Conecte seu repositório GitHub contendo o projeto.
3️⃣ No arquivo `streamlit.toml` (ou diretamente nas Secrets), adicione as variáveis de ambiente necessárias:
   - `BACKEND_URL` – URL do backend hospedado no Render ou outro serviço.
   - `GROQ_API_KEY` – chave da API Groq.
   - `TWILIO_ACCOUNT_SID` e `TWILIO_AUTH_TOKEN` – para o sandbox (opcional).
4️⃣ Configure o **branch** (`main`) e clique em **Deploy**.
5️⃣ Após o deploy, verifique se a URL do frontend está funcionando e se comunica com o backend.

> **Dica:** O plano gratuito permite até 3 apps simultâneos e até 1 GB de armazenamento – suficiente para o TEO em ambiente de demonstração.

## Roteiro Sugerido

### 1. O Problema
> Qual dor do cliente o TEO resolve?

Em clínicas de autismo, terapeutas usam linguagem clínica que os pais não entendem.
Ao mesmo tempo, laudos de neurodesenvolvimento vencem silenciosamente a cada 6 meses
— e ninguém avisa. O resultado: famílias ansiosas e desinformadas, consultas perdidas,
e médicos gastando horas compilando relatórios manualmente em vez de atender.

### 2. A Solução
> Como o TEO resolve esse problema?

O TEO é a ponte inteligente entre a clínica e as famílias. Ele age em três frentes:

**Módulo 1 — Tradução Clínica:** O terapeuta escreve suas notas técnicas. O TEO converte automaticamente em mensagens WhatsApp calorosas e acessíveis para os pais — com o formato 🧩 O que fizemos, 🌟 Grande conquista, 🏠 Dica para casa.

**Módulo 2 — Regra dos 5 Meses:** Um CRON job diário monitora silenciosamente todos os pacientes. Quando um laudo está vencendo, o TEO envia automaticamente uma mensagem WhatsApp com opções de horário para o responsável, interpreta a resposta via NLU e agenda a consulta sem intervenção humana.

**Módulo 3 — Relatório Semestral:** Com 1 clique, o neuropediatra recebe um PDF profissional com a síntese das últimas 48 sessões, gerada pela IA com base nas notas dos terapeutas, pronto para assinar e entregar.

### 3. Demonstração
> Mostre o agente funcionando (pode ser gravação de tela)

```
• Dashboard de Login: Mostre os 3 perfis de acesso (Recepção, Terapeuta, Neuropediatra).

• Módulo 1 (Terapeuta): Abra a aba "Nova Evolução". Digite notas técnicas de TO.
  Clique "Prévia da Mensagem" — mostre a tradução em tempo real pelo TEO.
  Clique "Salvar e Enviar WhatsApp" — mensagem enviada para os pais.

• Módulo 2 (Recepção): Vá em "Laudos Vencendo" — lista de pacientes com laudo crítico.
  Clique "Disparar CRON Manualmente" — mostre as mensagens sendo enviadas.

• Módulo 3 (Neuropediatra): Selecione um paciente. Veja os gráficos de progresso (Plotly).
  Preencha os pareceres por área. Clique "Gerar Relatório Semestral".
  Aguarde o processamento e faça o download do PDF profissional.
```

### 4. Diferencial e Impacto
> Por que essa solução é inovadora e qual é o impacto dela na sociedade?

```
"O diferencial do TEO é automatizar o que mais consome tempo e gera ansiedade
nas clínicas de autismo: a comunicação.

Tecnicamente, o TEO usa uma stack 100% baseada em ferramentas gratuitas ou de baixo
custo — Groq (LLM), Twilio Sandbox, PostgreSQL e Streamlit — tornando o sistema
acessível até para pequenas clínicas.

O impacto social é direto: famílias de crianças com TEA recebem informação clara,
empática e consistente sobre o desenvolvimento dos filhos. Terapeutas recuperam
tempo para focar no que importa. Médicos eliminam horas de burocracia.

Em um contexto onde o diagnóstico de autismo no Brasil cresceu 800% na última
década, ferramentas que aumentam a capacidade das clínicas sem aumentar sua equipe
são essenciais para democratizar o acesso ao cuidado especializado."
```

---

## Checklist do Pitch

- [ ] Duração máxima de 3 minutos
- [x] Problema claramente definido
- [x] Solução demonstrada na prática (3 módulos)
- [x] Diferencial explicado
- [ ] Áudio e vídeo com boa qualidade
- [ ] Link do vídeo adicionado

---

## Link do Vídeo

> Cole aqui o link do pitch (YouTube, Loom, Google Drive, etc.)

[Em produção — adicionar após gravação]
