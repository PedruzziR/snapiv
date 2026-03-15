"Perde coisas necessárias para atividades (brinquedos, deveres da escola, lápis ou livros).",
    "Distrai-se com estímulos externos.",
    "É esquecido em atividades do dia a dia.",
    "Mexe com as mãos ou os pés ou se remexe na cadeira.",
    "Sai do lugar na sala de aula ou em outras situações em que se espera que fique sentado.",
    "Corre de um lado para o outro ou sobe demais nas coisas em situações em que isto é inapropriado.",
    "Tem dificuldade em brincar ou envolver-se em atividades de lazer de forma calma.",
    "Não para ou frequentemente está a “mil por hora”.",
    "Fala em excesso.",
    "Responde perguntas de forma precipitada antes que elas tenham sido terminadas.",
    "Tem dificuldade em esperar sua vez.",
    "Interrompe os outros ou se intromete (nas conversas, jogos, etc.)."
]

opcoes_respostas = [
    "Nem um pouco.",
    "Só um pouco.",
    "Bastante.",
    "Demais."
]

# 2. Interface Visual
st.set_page_config(page_title="Escala SNAP-IV", layout="centered")

if "logado" not in st.session_state:
    st.session_state.logado = False
if "cpf_paciente" not in st.session_state:
    st.session_state.cpf_paciente = ""
if "avaliacao_concluida" not in st.session_state:
    st.session_state.avaliacao_concluida = False

st.title("Clínica de Psicologia e Psicanálise Bruna Ligoski")

# ================= TELA DE LOGIN =================
if not st.session_state.logado:
    st.write("Bem-vindo(a) à Avaliação Escala SNAP-IV.")
    
    with st.form("form_login"):
        cpf_input = st.text_input("CPF do Paciente (Login de Acesso - Apenas números)")
        senha_input = st.text_input("Senha de Acesso", type="password")
        botao_entrar = st.form_submit_button("Acessar Avaliação")
        
        if botao_entrar:
            if not cpf_input:
                st.error("Por favor, preencha o CPF do paciente.")
            elif senha_input != st.secrets["SENHA_MESTRA"]:
                st.error("Senha incorreta.")
            else:
                try:
                    cpfs_registrados = planilha.col_values(1)
                except:
                    cpfs_registrados = []
                    
                if cpf_input in cpfs_registrados:
                    st.error("Acesso bloqueado. Este CPF já consta em nossa base de dados para o SNAP-IV.")
                else:
                    st.session_state.logado = True
                    st.session_state.cpf_paciente = cpf_input
                    st.session_state.avaliacao_concluida = False
                    st.rerun()

# ================= TELA FINAL =================
elif st.session_state.avaliacao_concluida:
    st.success("Avaliação concluída e enviada com sucesso! Muito obrigado pela sua colaboração.")

# ================= QUESTIONÁRIO SNAP-IV =================
else:
    st.write("### Escala SNAP-IV")
    st.write("Selecione a opção que melhor descreve o comportamento da criança ou adolescente.")
    st.divider()

    with st.form("formulario_avaliacao"):
        st.subheader("Dados de Identificação")
        nome_paciente = st.text_input("Nome completo do paciente *")
        cpf_paciente_form = st.text_input("CPF do paciente *", value=st.session_state.cpf_paciente, disabled=True)
        
        nome_respondente = st.text_input("Nome do Respondente *")
        vinculo_respondente = st.text_input("Vínculo (ex.: mãe, pai, professor(a), etc.) *")
        st.divider()

        respostas_coletadas = {}

        # Mapeando e exibindo as 18 perguntas na tela
        for index, texto_pergunta in enumerate(perguntas):
            num_q = index + 1
            st.write(f"**{num_q}. {texto_pergunta}**")
            resposta = st.radio(f"Oculto {num_q}", opcoes_respostas, index=None, label_visibility="collapsed", key=f"q_{num_q}")

            if resposta is not None:
                respostas_coletadas[num_q] = resposta
            else:
                respostas_coletadas[num_q] = None
            st.write("---")

        botao_enviar = st.form_submit_button("Finalizar Avaliação")

    # 3. Processamento e Envio
    if botao_enviar:
        questoes_em_branco = [q for q, r in respostas_coletadas.items() if r is None]

        if not nome_paciente or not nome_respondente or not vinculo_respondente:
            st.error("Por favor, preencha todos os dados de identificação (Nome do Paciente, Seu Nome e Vínculo).")
        elif questoes_em_branco:
            st.error(f"Por favor, responda todas as perguntas. Falta responder {len(questoes_em_branco)} questão(ões).")
        else:
            
            # =====================================================================
            # ⬇️ ESPAÇO PARA OS SEUS CÁLCULOS! ⬇️
            # =====================================================================
            
            # Variáveis iniciais sugeridas para você usar na sua regra
            contagem_desatencao = 0
            contagem_hiper = 0
            
            # Exemplo de laço para você iterar sobre as respostas (de 1 a 18)
            for num_q, valor_resposta in respostas_coletadas.items():
                
                # SEU CÁLCULO AQUI! 
                # Dica: valor_resposta será "Nem um pouco.", "Só um pouco.", "Bastante." ou "Demais."
                pass
            
            # Defina os resultados finais para o e-mail:
            res_desatencao = "SEU RESULTADO AQUI"
            res_hiper = "SEU RESULTADO AQUI"
            
            # =====================================================================
            # ⬆️ FIM DO ESPAÇO DE CÁLCULOS ⬆️
            # =====================================================================

            with st.spinner('Processando os resultados e enviando e-mail...'):
                sucesso = enviar_email_resultados(
                    nome_paciente, 
                    st.session_state.cpf_paciente, 
                    nome_respondente, 
                    vinculo_respondente, 
                    contagem_desatencao, 
                    res_desatencao, 
                    contagem_hiper, 
                    res_hiper
                )
                
                if sucesso:
                    try:
                        planilha.append_row([st.session_state.cpf_paciente])
                    except:
                        pass
                    st.session_state.avaliacao_concluida = True
                    st.rerun()
                else:
                    st.error("Houve um erro no envio. Avise a profissional responsável.")
