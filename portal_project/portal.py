# portal.py
import streamlit as st
from utils import create_username_to_fullname_map

# --- Конфигурация страницы ---
LOGO_URL = "https://i.ibb.co/Qvy4G6DR/images.png"
st.set_page_config(page_title="Sales Portal", page_icon=LOGO_URL, layout="centered")

# --- Инициализация состояний сессии ---
if "authenticated" not in st.session_state: st.session_state['authenticated'] = False
if "selected_company" not in st.session_state: st.session_state['selected_company'] = None
if "username" not in st.session_state: st.session_state['username'] = None

# --- CSS ---
hide_sidebar_nav_style = """
            <style>
            [data-testid="stSidebarNav"] { display: none; }
            #MainMenu, footer, header {visibility: hidden;}
            </style>
            """

# --- Функции ---

def show_login_form():
    """Отображает форму входа и обрабатывает логин."""
    st.markdown(hide_sidebar_nav_style, unsafe_allow_html=True)
    st.title("Sales Portal")
    st.write("Please log in to continue")
    
    users_data = st.secrets.get("users", {})
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user_info = users_data.get(username)
            if user_info and user_info.get("password") == password_input:
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                user_company_config = user_info.get("company")
                
                # Устанавливаем выбранную компанию только для пользователей с ОДНОЙ компанией
                if isinstance(user_company_config, str) and user_company_config != "admin":
                    st.session_state['selected_company'] = user_company_config
                
                st.rerun()
            else:
                st.error("Incorrect username or password")

def show_admin_company_selection():
    """Показывает администратору панель выбора из ВСЕХ компаний."""
    st.title("Admin Dashboard")
    st.header("Please select a company to manage")
    st.write("---")
    try:
        companies = st.secrets["companies"]
        for key, name in companies.items():
            if st.button(name, use_container_width=True, key=f"btn_{key}"):
                st.session_state['selected_company'] = key
                st.rerun()
    except Exception as e:
        st.error(f"Could not load companies. Check `[companies]` in secrets.toml: {e}")

# --- НОВАЯ ФУНКЦИЯ ---
def show_user_company_selection(user_companies):
    """Показывает экран выбора для пользователей с доступом к нескольким компаниям."""
    username = st.session_state.get("username", "User")
    name_map = create_username_to_fullname_map()
    display_name = name_map.get(username, username.capitalize())

    st.title(f"Welcome, {display_name}!")
    st.header("Please select a company to continue")
    st.write("---")
    try:
        all_companies = st.secrets["companies"]
        for key in user_companies:
            name = all_companies.get(key, key) 
            if st.button(name, use_container_width=True, key=f"user_btn_{key}"):
                st.session_state['selected_company'] = key
                st.rerun()
    except Exception as e:
        st.error(f"Could not load your companies: {e}")

def show_main_page():
    """Отображает основную страницу приложения."""
    username = st.session_state['username']
    user_info = st.secrets["users"][username]
    selected_company_key = st.session_state['selected_company']
    
    company_name = st.secrets["companies"].get(selected_company_key, "Selected Company")
    
    name_map = create_username_to_fullname_map()
    display_name = name_map.get(username, username.capitalize())

    st.title(f"Welcome, {display_name}!")
    st.success(f"You are working with: **{company_name}**")
    
    # Кнопка "Назад" для админа или пользователя с несколькими компаниями
    if user_info.get("company") == "admin" or isinstance(user_info.get("company"), list):
        st.write("---")
        if st.button("‹ Back to Company Selection"):
            st.session_state['selected_company'] = None
            st.rerun()

# --- ИЗМЕНЕННАЯ ФУНКЦИЯ ---
def setup_sidebar():
    """Настраивает боковую панель с корректным отображением компании."""
    name_map = create_username_to_fullname_map()
    
    with st.sidebar:
        username = st.session_state.get("username", "Guest")
        display_name = name_map.get(username, username.capitalize())
        
        st.write(f"Logged in as: **{display_name}**")

        user_company_config = st.secrets["users"].get(username, {}).get("company")

        if user_company_config == "admin":
             st.write("Role: **Administrator**")
        elif isinstance(user_company_config, list):
            # Для пользователей с несколькими компаниями
            all_companies = st.secrets.get("companies", {})
            company_names = [all_companies.get(key, key) for key in user_company_config]
            st.write(f"Companies: **{', '.join(company_names)}**")
        else:
            # Для пользователей с одной компанией
            company_name = st.secrets["companies"].get(user_company_config, "")
            st.write(f"Company: **{company_name}**")

        st.write("---")
        if st.button("Log out", key="logout_button"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

# --- ОБНОВЛЕННАЯ ГЛАВНАЯ ЛОГИКА ---
if not st.session_state.get('authenticated'):
    show_login_form()
else:
    setup_sidebar()
    username = st.session_state['username']
    user_company_config = st.secrets["users"][username]["company"]
    
    # Случай 1: Администратор
    if user_company_config == "admin":
        if st.session_state.get('selected_company'):
            show_main_page()
        else:
            show_admin_company_selection()
            
    # Случай 2: Пользователь с несколькими компаниями
    elif isinstance(user_company_config, list):
        if st.session_state.get('selected_company'):
            show_main_page()
        else:
            show_user_company_selection(user_company_config)
            
    # Случай 3: Пользователь с одной компанией
    else:
        show_main_page()