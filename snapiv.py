import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]
# ===========================================================

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("SNAP-IV").sheet1  # PLANILHA "SNAP-IV" NO DRIVE

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()
# =============================================================

def enviar_email_resultados(nome_pac, cpf, nome_resp, vinculo, contagem_desatencao, res_desatencao, contagem_hiper, res_hiper):
    assunto = f"Resultados Escala SNAP-IV - Paciente: {nome_pac}"
    
    corpo = f"Avaliação Escala SNAP-IV concluída.\n\n"
    corpo += f"=== DADOS DO PACIENTE ===\n"
    corpo += f"Nome: {nome_pac}\n"
    corpo += f"CPF (Login): {cpf}\n\n"
    
    corpo += f"=== DADOS DO RESPONDENTE ===\n"
    corpo += f"Nome: {nome_resp}\n"
    corpo += f"Vínculo: {vinculo}\n\n"
    
    corpo += "================ RESULTADOS DA CORREÇÃO ================\n\n"
    
    corpo += "► FATOR: DESATENÇÃO (Questões 1 a 9)\n"
    corpo += f"Sintomas marcados como 'Bastante' ou 'Demais': {contagem_desatencao} de 9\n"
    corpo += f"Resultado Clínico: {res_desatencao}\n\n"

    corpo += "► FATOR: HIPERATIVIDADE / IMPULSIVIDADE (Questões 10 a 18)\n"
    corpo += f"Sintomas marcados como 'Bastante' ou 'Demais': {contagem_hiper} de 9\n"
    corpo += f"Resultado Clínico: {res_hiper}\n\n"
    
    corpo += "--------------------------------------------------------\n"
    corpo += "* Regra aplicada:\n"
    corpo += "- Se ≥ 6 em Desatenção = Clínico (senão, Não Clínico).\n"
    corpo += "- Se ≥ 6 em Hiperatividade/Impulsividade = Clínico (senão, Não Clínico).\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return False

# 1. Perguntas e Opções
perguntas = [
    "Não consegue prestar muita atenção a detalhes ou comete erros por descuido nos trabalhos da escola ou tarefas.",
    "Tem dificuldade de manter a atenção em tarefas ou atividades de lazer.",
    "Parece não estar ouvindo quando se fala diretamente com ele.",
    "Não segue instruções até o fim e não termina deveres de escola, tarefas ou obrigações.",
    "Tem dificuldade para organizar tarefas e atividades.",
    "Evita, não gosta ou se envolve contra a vontade em tarefas que exigem esforço mental prolongado.",
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
                    
                # NOVA REGRA: Conta quantas vezes o CPF aparece. Só bloqueia se for 4 ou mais.
                if cpfs_registrados.count(cpf_input) >= 4:
                    st.error("Acesso bloqueado. Este CPF já atingiu o limite máximo de 4 avaliações cadastradas.")
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
            # CÁLCULOS SNAP-IV
            # =====================================================================
            contagem_desatencao = 0
            contagem_hiper = 0
            respostas_alvo = ["Bastante.", "Demais."]
            
            for num_q, valor_resposta in respostas_coletadas.items():
                if valor_resposta in respostas_alvo:
                    if 1 <= num_q <= 9:
                        contagem_desatencao += 1
                    elif 10 <= num_q <= 18:
                        contagem_hiper += 1
            
            if contagem_desatencao >= 6:
                res_desatencao = "Clínico"
            else:
                res_desatencao = "Não Clínico"
                
            if contagem_hiper >= 6:
                res_hiper = "Clínico"
            else:
                res_hiper = "Não Clínico"
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
