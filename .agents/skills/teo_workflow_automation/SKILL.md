---
name: teo_workflow_automation
description: Automação de fluxos de agendamento, envio de relatórios, notificações via WhatsApp/E-mail e rotinas clínicas no sistema TEO.
---

# TEO — Automação de Fluxos de Trabalho e Rotinas Clínicas

Esta skill gerencia a automação inteligente de rotinas, notificações e sincronização entre os atores do ecossistema TEO (Terapeutas, Neuropediatra, Recepção, Administração e Famílias).

## 1. Fluxo de Evolução Diária e Resumo Semanal

```
[Terapeuta registra sessão] 
       │
       ▼
(IA TEO traduz em 🧩🌟🏠) ──► [Disponível no painel/WhatsApp]
       │
       ▼ (A cada semana - Sexta-feira / Sábado)
[TEO compila Resumo Semanal] ──► [Envio automático ao WhatsApp do Representante]
```

- **Registro Diário:** Em cada sessão realizada, o terapeuta registra as atividades, evolução e recomendações.
- **Resumo Semanal (Terapeutas → Representante):** Semanalmente, o TEO agrupa as evoluções registradas na semana por todas as especialidades e gera um resumo executivo encorajador, enviado ao representante para mantê-lo alinhado com o progresso contínuo.

---

## 2. Ciclo de Laudo Semestral (Regra dos 5 Meses)

A cada 5 meses de acompanhamento contínuo de um paciente, o sistema ativa o fluxo preparatório para a consulta semestral de renovação de laudo do Neuropediatra:

1. **Alerta de 5 Meses:** O sistema notifica os terapeutas vinculados para enviarem seus relatórios/laudos de especialidade sobre as evoluções, atividades realizadas e recomendações dos últimos 5 meses.
2. **Síntese LLM Multidisciplinar:** O TEO consolida os relatórios das especialidades em um documento estruturado ([SÍNTESE GLOBAL], [EVOLUÇÃO POR ÁREA], [LAUDO CONCLUSIVO E RECOMENDAÇÕES]).
3. **Entrega ao Neuropediatra:** O relatório consolidado é enviado ao painel do Neuropediatra antes da consulta do paciente.

---

## 3. Fluxo de Agendamento de Consulta e Confirmação (Recepção)

```
[Laudo/Indicação Neuropediatra] ──► [Recepção notificada]
       │
       ▼
[Recepção envia opções de horário via WhatsApp/E-mail]
       │
       ▼ (Pais respondem "1" ou "2")
[TEO NLU processa resposta] ──► [Recepção agenda consulta no sistema]
       │
       ▼
[Envio de Mensagem de Confirmação com Sugestões]
```

- **Modelo de Mensagem de Confirmação (Recepção → Pais):**
  ```markdown
  Olá! ✅ A consulta está confirmada!

  👶 *Paciente:* [Nome da Criança]
  🩺 *Neuropediatra:* [Nome do Neuropediatra]
  📅 *Data e Horário:* [Data] às [Horário]

  💡 *Sugestões importantes para o dia:*
  • Por favor, chegue com **30 minutos de antecedência** para acolhimento na recepção e tranquilidade da criança.
  • Traga os exames anteriores e relatórios da escola (se houver).
  • Em caso de imprevisto, avise-nos por aqui com 24h de antecedência.

  Estamos ansiosos para recebê-los! 💙
  ```

---

## 4. Fluxo de Atribuição de Terapeutas e Horários (Administrador)

1. **Recepção de Indicações:** O Neuropediatra registra no laudo da consulta quais especialidades e terapeutas são indicados para o paciente.
2. **Designação pelo Admin:** O Administrador acessa o painel, visualiza as indicações do Neuropediatra e atribui formalmente os terapeutas ao paciente.
3. **Marcação de Grade Horária:** O Administrador concilia a disponibilidade geral dos especialistas e fixa os horários de atendimento do paciente.
4. **Notificação em Massa:**
   - A grade horária fixa é disponibilizada instantaneamente para a **Recepção**.
   - O Administrador (ou sistema via disparo automático) envia a grade horária completa dos terapeutas para o **Representante do Paciente** (via WhatsApp/E-mail).
