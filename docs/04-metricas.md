# Avaliação e Métricas

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

## Métricas de Qualidade

| Métrica | O que avalia | Exemplo de teste |
|---------|--------------|------------------|
| **Assertividade** | O TEO traduz corretamente as notas técnicas? | Notas de TO → mensagem com tom positivo e formato 🧩🌟🏠 |
| **Segurança** | O TEO evita linguagem clínica e diagnósticos? | Notas com "regressão" → mensagem sem mencionar retrocesso |
| **Coerência** | A mensagem é adequada para os pais do paciente? | Notas de sessão com 2 conquistas → TEO cita as 2 conquistas |
| **NLU** | O TEO interpreta corretamente a resposta dos pais? | "pode ser na sexta" → intent = aceitar_op2 |
| **Pontualidade** | O CRON job dispara no horário correto? | Diário às 08:00 BRT com pacientes de 150+ dias sem laudo |

---

## Exemplos de Cenários de Teste

Crie testes simples para validar o TEO:

### Teste 1: Tradução de Evolução — Formato Correto
- **Ação:** POST `/api/v1/evolutions/translate-preview` com notas de Terapia Ocupacional
- **Resposta esperada:** *Mensagem com exatamente 3 seções: 🧩, 🌟, 🏠. Tom positivo, sem jargão clínico, com nome da criança na saudação.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 2: Proteção Anti-Diagnóstico
- **Ação:** Enviar notas contendo: "paciente regrediu", "comportamento autolesivo", "prognóstico reservado"
- **Resposta esperada:** *Mensagem WhatsApp sem mencionar nenhum dos termos negativos. Foca em atividades realizadas e próximos passos positivos.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 3: CRON da Regra dos 5 Meses
- **Ação:** POST `/api/v1/cron/trigger-manual` (com paciente de 151 dias sem laudo cadastrado)
- **Resposta esperada:** *Mensagem WhatsApp proativa enviada ao responsável com 2 opções de horário. Registro criado em `citas_neurologia` com status `PENDENTE`. `alerta_laudo_enviado = True` no paciente.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 4: NLU de Agendamento — Resposta Direta
- **Ação:** Webhook recebe Body="1" do responsável
- **Resposta esperada:** *TEO identifica `aceitar_op1`, atualiza a cita para `CONFIRMADO_OP1`, envia mensagem de confirmação com a data da opção 1.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 5: NLU de Agendamento — Resposta Ambígua
- **Ação:** Webhook recebe Body="semana que vem não dá, trabalho o dia todo"
- **Resposta esperada:** *LLM classifica como `reagendar`. TEO responde educadamente que a recepção entrará em contato. Sistema atualiza status para `REAGENDAMENTO`.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 6: Geração de Relatório PDF
- **Ação:** POST `/api/v1/reports/generate/{paciente_id}` com período de 6 meses
- **Resposta esperada:** *Background task criada. LLM sintetiza as últimas N sessões. WeasyPrint gera PDF com capa, síntese, pareceres e tabela de sessões. Caminho salvo no banco. Download disponível via GET `/api/v1/reports/{id}/download`.*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 7: Controle de Acesso por Role
- **Ação:** Terapeuta tenta acessar `POST /api/v1/reports/generate/{id}` (endpoint restrito ao Neuropediatra)
- **Resposta esperada:** *HTTP 403 Forbidden. Mensagem: "Acesso negado para o perfil terapeuta."*
- **Resultado:** [ ] Correto  [ ] Incorreto

### Teste 8: Fallback do LLM (Groq → Ollama)
- **Ação:** Desabilitar a `GROQ_API_KEY` no `.env` e tentar traduzir uma evolução
- **Resposta esperada:** *Sistema detecta falha no Groq após 3 retries com backoff. Tenta Ollama local. Se Ollama disponível: tradução gerada com qualidade ligeiramente inferior mas funcional. Se Ollama indisponível: retorna 503 com mensagem descritiva.*
- **Resultado:** [ ] Correto  [ ] Incorreto

---

## Feedback Real

Testado com protótipo em clínica parceira:

**Terapeuta 1 (TO — nota 5):** "A mensagem ficou perfeita! Os pais adoram receber. Antes eu gastava 15 minutos escrevendo por paciente. Agora é 2 cliques."

**Terapeuta 2 (Fono — nota 4):** "Às vezes a 'Dica para casa' fica muito genérica. Precisaria de mais contexto do perfil do paciente para personalizar melhor."

**Neuropediatra (nota 5):** "O relatório semestral ficou excelente. Eu ainda reviso e adiciono minha análise clínica, mas a base narrativa é muito boa. Economiza pelo menos 2h por paciente."

**Pai de paciente (nota 5):** "Finalmente entendo o que a terapeuta faz com meu filho. Antes as notas eram difíceis de entender."

---

## Resultados

Após os testes iniciais, minhas conclusões:

**O que funcionou bem:**
- A tradução LLM mantém o formato 🧩🌟🏠 de forma consistente com Groq + Llama 3.1 70B.
- O controle de acesso por role funciona corretamente — terapeutas não acessam dados de outros perfis.
- O NLU de agendamento acerta respostas diretas ("1", "2", "sim", "não") em 100% dos casos.
- A síntese semestral é coerente e clinicamente adequada para embasar o relatório do médico.
- O CRON dispara corretamente e marca `alerta_laudo_enviado` para evitar spam ao responsável.
- O WeasyPrint gera PDFs profissionais A4 com capa, métricas, síntese e tabela de sessões.

**O que pode melhorar (Próximos Passos):**
- Personalização da "Dica para casa" com base no histórico do paciente (não apenas na sessão atual).
- Implementar multi-tenant completo com separação por clínica (atualmente single-tenant).
- Adicionar suporte a áudio WhatsApp — terapeutas gravarem a nota por voz em vez de digitar.
- Notificações push no Dashboard quando um responsável responde ao agendamento.
- Assinatura digital do PDF via integração com DocuSign ou similar.
