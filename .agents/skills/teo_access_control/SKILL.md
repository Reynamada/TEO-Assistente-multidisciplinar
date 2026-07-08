---
name: teo_access_control
description: Regras de controle de acesso (RBAC), visibilidade e fluxos de trabalho por perfil no sistema TEO (Terapeuta, Neuropediatra, Recepção e Administrador).
---

# TEO — Controle de Acesso, Visibilidade e Regras de Segurança (RBAC)

Esta skill define as fronteiras de visibilidade, permissões de interface e regras de negócio para cada perfil de usuário no sistema TEO (Tu Enlace Organizador). Ao implementar novas funcionalidades ou auditar o código, garanta conformidade estrita com estas regras.

## 1. Visão Geral por Perfil de Usuário

| Perfil | Acesso a Pacientes | Acesso a Evoluções | Agendamentos/Horários | Laudos Neuropediatra |
|---|---|---|---|---|
| **Terapeuta** | Apenas vinculados | Apenas próprias sessões | Apenas sua própria agenda | Sim (leitura) |
| **Neuropediatra**| Todos | Todas (de todos) | Sua agenda e de todos | Sim (criação/edição) |
| **Recepção** | Todos (cadastro) | Não (acesso negado) | Gestão de marcações | Sim (leitura) |
| **Administrador**| Todos (total) | Todas (total) | Gestão total (todas) | Sim (leitura/gestão)|

---

## 2. Detalhamento de Permissões e Regras de Negócio

### 👨‍⚕️ Terapeutas (TO, Fono, Psicologia, Psicopedagogia, Fisioterapia)
- **Visibilidade Permitida:** Visualizam EXCLUSIVAMENTE seus pacientes designados, seus próprios horários/agenda, os registros das sessões de terapia realizadas POR ELES e o laudo final emitido pelo neuropediatra.
- **Restrição Rigorosa:** É TERMINANTEMENTE PROIBIDO que um terapeuta visualize registros de sessões, notas clínicas ou evoluções redigidas por outros terapeutas, bem como dados de pacientes que não estejam sob seus cuidados.
- **Barra Lateral:** Exibir apenas módulos: *Dashboard*, *Meus Pacientes*, *Minhas Evoluções*, *Minha Agenda*.

### 🧠 Neuropediatra
- **Visibilidade Permitida:** Acesso integral e irrestrito ao histórico de todos os pacientes e aos registros de sessões de TODOS os terapeutas da clínica.
- **Obrigações de Consulta:** Em cada consulta realizada, o neuropediatra deve emitir um laudo completo e enviá-lo por e-mail/WhatsApp ao representante do paciente.
- **Formulário de Indicação e Consulta:** Deve possuir acesso a um formulário específico para:
  1. Selecionar/indicar os terapeutas e especialidades recomendados para o tratamento da criança.
  2. Um campo (box) dedicado ao registro da consulta, contendo recomendações clínicas, sugestões, evolução observada (se houver) e diagnóstico formal.
- **Compartilhamento de Laudos:** O laudo emitido e as indicações de terapeutas devem ser disponibilizados automaticamente para visualização da Recepção e do Administrador.
- **Barra Lateral:** Exibir módulos: *Dashboard*, *Pacientes*, *Progresso Multidisciplinar*, *Todas Evoluções*, *Relatórios*, *Agenda*.

### 💁‍♀️ Recepção
- **Visibilidade Permitida:** Acesso aos dados cadastrais dos pacientes, agenda geral de consultas e exclusivamente ao laudo emitido pelo neuropediatra. NÃO tem acesso às notas de evolução terapêutica diária.
- **Edição:** Permissão para editar dados cadastrais de pacientes, atualizar nomes de terapeutas e especialidades no cadastro, e gerenciar horários de sessões.
- **Fluxo de Agendamento do Neuropediatra:**
  1. Envia via WhatsApp/e-mail opções de horários disponíveis ao representante da criança.
  2. Após confirmação do responsável, realiza o agendamento no sistema.
  3. Dispara mensagem de confirmação contendo: Nome do Neuropediatra, Horário confirmado e Sugestões/Instruções práticas (ex: "Chegar 30 minutos antes da consulta para acolhimento na recepção").
- **Barra Lateral:** Exibir módulos: *Dashboard*, *Pacientes (Cadastro)*, *Agendamentos*.

### ⚙️ Administrador
- **Visibilidade Permitida:** Acesso irrestrito a todo o ecossistema TEO (usuários, especialistas, pacientes, agendas, relatórios e auditoria).
- **Atribuição de Terapeutas:** Responsável por designar e vincular os terapeutas sugeridos pelo neuropediatra a cada paciente, além de marcar os horários iniciais das sessões.
- **Coordenação de Horários:** Tem acesso a todas as agendas dos especialistas. Deve disponibilizar e enviar esses horários para a Recepção e coordenar o envio da grade horária dos terapeutas ao representante de cada paciente.
- **Barra Lateral:** Exibir módulos: *Dashboard*, *Pacientes*, *Evoluções*, *Agendamentos*, *Relatórios*, *Admin/Configurações*.
