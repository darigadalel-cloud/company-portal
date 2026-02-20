# utils.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

import requests
from streamlit_lottie import st_lottie

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- Блок 1: Подключение к Google (без изменений) ---
@st.cache_resource(ttl=3600, show_spinner=False)
def get_gspread_client():
    """Подключается к Google API с использованием учетных данных из Streamlit Secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Ошибка авторизации в Google: Проверьте ваш secrets.toml. Детали: {e}")
        return None

@st.cache_resource(ttl=600, show_spinner=False)
def get_spreadsheet():
    """Открывает Google-таблицу по ее ID из Streamlit Secrets."""
    try:
        client = get_gspread_client()
        if client is None: return None
        spreadsheet_id = st.secrets["connections"]["spreadsheet_id"]
        spreadsheet = client.open_by_key(spreadsheet_id)
        return spreadsheet
    except Exception as e:
        st.error(f"Не удалось открыть Google-таблицу. Проверьте spreadsheet_id и права доступа для робота. Ошибка: {e}")
        return None

# --- Блок 2: Загрузка данных (без изменений) ---
@st.cache_data(ttl=60, show_spinner=False)
def _internal_load_data(_spreadsheet, worksheet_name):
    """Внутренняя функция для загрузки данных с конкретного листа."""
    try:
        if _spreadsheet is None:
            return pd.DataFrame() 
        worksheet = _spreadsheet.worksheet(worksheet_name)
        all_values = worksheet.get_all_values()
        if not all_values or len(all_values) < 1:
            st.warning(f"Лист '{worksheet_name}' пуст или содержит только заголовок.")
            return pd.DataFrame()
        df = pd.DataFrame(all_values[1:], columns=all_values[0])
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Лист с именем '{worksheet_name}' не найден в Google-таблице.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка при чтении данных с листа '{worksheet_name}': {e}")
        return pd.DataFrame()

# --- Блок 3: Функция-диспетчер (без изменений) ---
def load_data(*args, **kwargs):
    """Универсальная функция-диспетчер для загрузки данных."""
    if len(args) == 2:
        spreadsheet_obj, worksheet_name = args
        return _internal_load_data(spreadsheet_obj, worksheet_name)
    elif 'worksheet_name' in kwargs and not args:
        worksheet_name = kwargs['worksheet_name']
        spreadsheet_obj = get_spreadsheet()
        return _internal_load_data(spreadsheet_obj, worksheet_name)
    elif len(args) == 1 and not kwargs:
        worksheet_name = args[0]
        spreadsheet_obj = get_spreadsheet()
        return _internal_load_data(spreadsheet_obj, worksheet_name)
    elif len(args) == 1 and 'worksheet_name' in kwargs:
        spreadsheet_obj = args[0]
        worksheet_name = kwargs['worksheet_name']
        return _internal_load_data(spreadsheet_obj, worksheet_name)
    else:
        st.error("Неверные аргументы для функции load_data.")
        return pd.DataFrame()

# --- Блок 4: Подсчет уведомлений (без изменений) ---
@st.cache_data(ttl=60, show_spinner=False)
def get_unread_notifications_count(_spreadsheet, username):
    """Безопасно считает непрочитанные уведомления."""
    if _spreadsheet is None or not username:
        return 0
    notifications_df = _internal_load_data(_spreadsheet, "Notifications")
    if notifications_df.empty:
        return 0
    simple_name = username.split('@')[0].lower()
    user_column = 'Username' 
    status_column = 'Status'
    if user_column not in notifications_df.columns or status_column not in notifications_df.columns:
        st.warning(f"На листе 'Notifications' не найдены колонки '{user_column}' и/или '{status_column}'.")
        return 0
    user_notifications = notifications_df[
        (notifications_df[user_column].str.strip().str.lower() == simple_name) & 
        (notifications_df[status_column].str.strip().str.lower() == 'unread')
    ]
    return len(user_notifications)

# --- ИСПРАВЛЕНИЕ: Полностью переписанная функция для создания карты имен ---
@st.cache_data(ttl=3600, show_spinner=False)
def create_username_to_fullname_map():
    """
    Создает словарь для сопоставления логинов с полными именами.
    Просматривает списки клиентов ВСЕХ компаний для сбора имен.
    """
    name_map = {}
    
    try:
        all_usernames = st.secrets.get("users", {}).keys()
        all_customers_configs = st.secrets.get("page_settings", {}).get("customers", {})
    except Exception:
        return {} # Возвращаем пустую карту, если секреты недоступны

    if not all_customers_configs:
        return {} # Возвращаем пустую карту, если нет настроек для страницы Customers

    # Проходим по каждой компании, чтобы собрать полные имена
    for company_key, customers_config in all_customers_configs.items():
        worksheet_name = customers_config.get("worksheet")
        sales_col = customers_config.get("sales_col")

        if not worksheet_name or not sales_col:
            continue # Пропускаем компанию, если для нее не настроена страница Customers

        df_customers = _internal_load_data(get_spreadsheet(), worksheet_name)

        if df_customers.empty or sales_col not in df_customers.columns:
            continue

        unique_full_names = df_customers[sales_col].dropna().unique()

        for full_name in unique_full_names:
            clean_full_name = str(full_name).lower().replace(' ', '').replace('-', '')
            
            # Создаем копию списка логинов, чтобы безопасно итерировать
            for username in list(all_usernames):
                # Если для этого пользователя уже найдено имя, не перезаписываем его
                if username in name_map:
                    continue
                
                simple_username = username.split('@')[0].replace('.', '').replace('-', '')
                if simple_username in clean_full_name:
                    name_map[username] = full_name.strip()
                    break # Переходим к следующему полному имени, так как логин уже нашли
                    
    return name_map


# --- ИСПРАВЛЕНИЕ: НОВАЯ ФУНКЦИЯ ДЛЯ СТРОГОГО РАЗДЕЛЕНИЯ КОМАНД ---
def get_director_team_members(username, selected_company):
    """
    Правильно определяет список членов команды для директора на основе ВЫБРАННОЙ компании.
    """
    director_config = st.secrets.get("directors", {}).get(selected_company, {})
    all_teams_config = st.secrets.get("teams", {})
    
    assigned_teams = director_config.get(username)
    
    user_is_admin = st.secrets.get("users", {}).get(username, {}).get("company") == "admin"
    if not assigned_teams and user_is_admin:
        assigned_teams = director_config.get("admin")

    if not assigned_teams:
        return []

    if isinstance(assigned_teams, str):
        assigned_teams = [assigned_teams]

    team_members = set()
    
    for team_ref in assigned_teams:
        company_key = selected_company
        team_name = team_ref
        
        members = all_teams_config.get(company_key, {}).get(team_name, [])
        team_members.update(members)
        
    return sorted(list(team_members))