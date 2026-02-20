# pages/4_Team.py
import streamlit as st
import pandas as pd
from utils import (
    load_data, 
    create_username_to_fullname_map, 
    load_lottieurl
)
from streamlit_lottie import st_lottie

def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Автоматически исправляет дубликаты колонок."""
    cols = list(df.columns)
    new_cols = []
    col_counts = {}
    for col in cols:
        clean_col = col.strip() if isinstance(col, str) else col
        if clean_col in col_counts:
            col_counts[clean_col] += 1
            new_cols.append(f"{clean_col}_{col_counts[clean_col]}")
        else:
            col_counts[clean_col] = 0
            new_cols.append(clean_col)
    df.columns = new_cols
    return df

# --- 1. НАСТРОЙКА СТРАНИЦЫ И ПРОВЕРКА ДОСТУПА ---
LOGO_URL = "https://i.ibb.co/Qvy4G6DR/images.png"
st.set_page_config(layout="wide", page_title="Team Dashboard", page_icon=LOGO_URL)


if not st.session_state.get("authenticated", False): st.error("Please log in."); st.stop()
if not st.session_state.get("selected_company"): st.warning("Please select a company first."); st.stop()

# --- ИСПРАВЛЕНИЕ 1: Полностью заменяем старую неисправную функцию ---
def get_viewable_logins(username, company_key):
    """
    Правильно определяет, каких сотрудников может видеть пользователь
    СТРОГО НА ОСНОВЕ ВЫБРАННОЙ КОМПАНИИ.
    """
    # Особые права для администраторов
    if username in ["admin", "dariga","erik", "shelby","operations"]:
        return "SEE_ALL"
    
    # Сначала проверяем, является ли пользователь директором В ЭТОЙ КОМПАНИИ
    director_config = st.secrets.get("directors", {}).get(company_key, {})
    if username in director_config:
        assigned_teams = director_config[username]
        # Превращаем в список, если это одна команда (строка)
        if isinstance(assigned_teams, str):
            assigned_teams = [assigned_teams]
        
        all_members = set()
        team_config_for_company = st.secrets.get("teams", {}).get(company_key, {})
        for team_name in assigned_teams:
            members = team_config_for_company.get(team_name, [])
            all_members.update(members)
        return sorted(list(all_members))

    # Если не директор, проверяем, является ли он тимлидом В ЭТОЙ КОМПАНИИ
    team_config = st.secrets.get("teams", {}).get(company_key, {})
    if username in team_config:
        return team_config[username]

    # Если ни то, ни другое - пользователь видит только себя
    return [username]

username = st.session_state.get("username", "").strip().lower()
company_key = st.session_state.get('selected_company')

# Проверка авторизации на основе НОВОЙ, правильной логики
allowed_logins_check = get_viewable_logins(username, company_key)
if not allowed_logins_check: # Если функция вернула пустой список
     st.error("Access Denied: You do not have a role in this company."); st.stop()

st.title("Team Leader & Director Dashboard")
company_name = st.secrets.get("companies", {}).get(company_key, company_key)
st.subheader(f"Displaying data for: {company_name}")

# --- 2. ДИНАМИЧЕСКАЯ ЗАГРУЗКА ДАННЫХ ---

placeholder = st.empty()
with placeholder.container():
    st.markdown(
        """
        <style> .loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; background-color: transparent; } .lds-spinner { display: inline-block; position: relative; width: 80px; height: 80px; } .lds-spinner div { transform-origin: 40px 40px; animation: lds-spinner 1.2s linear infinite; } .lds-spinner div:after { content: " "; display: block; position: absolute; top: 3px; left: 37px; width: 6px; height: 18px; border-radius: 20%; background: #d3d3d3; } .lds-spinner div:nth-child(1) { transform: rotate(0deg);   animation-delay: -1.1s; } .lds-spinner div:nth-child(2) { transform: rotate(30deg);  animation-delay: -1s; } .lds-spinner div:nth-child(3) { transform: rotate(60deg);  animation-delay: -0.9s; } .lds-spinner div:nth-child(4) { transform: rotate(90deg);  animation-delay: -0.8s; } .lds-spinner div:nth-child(5) { transform: rotate(120deg); animation-delay: -0.7s; } .lds-spinner div:nth-child(6) { transform: rotate(150deg); animation-delay: -0.6s; } .lds-spinner div:nth-child(7) { transform: rotate(180deg); animation-delay: -0.5s; } .lds-spinner div:nth-child(8) { transform: rotate(210deg); animation-delay: -0.4s; } .lds-spinner div:nth-child(9) { transform: rotate(240deg); animation-delay: -0.3s; } .lds-spinner div:nth-child(10){ transform: rotate(270deg); animation-delay: -0.2s; } .lds-spinner div:nth-child(11){ transform: rotate(300deg); animation-delay: -0.1s; } .lds-spinner div:nth-child(12){ transform: rotate(330deg); animation-delay: 0s; } @keyframes lds-spinner { 0% { opacity: 1; } 100% { opacity: 0; } } .loading-text { color: #bfbfbf; font-family: 'Segoe UI', sans-serif; font-size: 14px; letter-spacing: 2px; margin-top: 20px; } </style>
        <div class="loading-container"> <div class="lds-spinner"> <div></div><div></div><div></div><div></div><div></div><div></div> <div></div><div></div><div></div><div></div><div></div><div></div> </div> <div class="loading-text">LOADING ...</div> </div>
        """, unsafe_allow_html=True
    )

name_map = create_username_to_fullname_map()

def load_and_prepare_data(page_name):
    config = st.secrets.get("page_settings", {}).get(page_name, {}).get(company_key, {})
    if not config or not config.get("worksheet"): return pd.DataFrame(), {}
    
    df = load_data(worksheet_name=config["worksheet"])
    if df.empty: return pd.DataFrame(), config

    df = df.reset_index(drop=True)
    df = sanitize_columns(df)

    filter_col, filter_val = config.get("filter_col"), config.get("filter_val")
    exclude_vals = config.get("exclude_vals")
    if filter_col and filter_col in df.columns:
        # Вариант А: Оставляем только конкретное значение
        if filter_val is not None:
            df = df[df[filter_col] == filter_val].copy()
        
        # Вариант Б: Исключаем список значений (здесь была ошибка)
        elif exclude_vals and isinstance(exclude_vals, list):
            df = df[~df[filter_col].isin(exclude_vals)].copy()
    else:
        # Если колонка в secrets указана, но в таблице её нет — выводим предупреждение для отладки
        if filter_col:
            st.warning(f"Column '{filter_col}' not found in {config['worksheet']}. Check secrets or sheet headers.")
        
    return df, config

df_customers, cfg_customers = load_and_prepare_data("customers")
df_overdue, cfg_overdue = load_and_prepare_data("overdue")
df_bonuses, cfg_bonuses = load_and_prepare_data("bonuses")

placeholder.empty()

# --- 3. ЛОГИКА ФИЛЬТРАЦИИ ПО КОМАНДАМ (УПРОЩЕННАЯ И ИСПРАВЛЕННАЯ) ---

# --- ИСПРАВЛЕНИЕ 2: Вызываем новую правильную функцию ---
allowed_users_logins = get_viewable_logins(username, company_key)

fullname_map = {v: k for k, v in name_map.items()}
selected_member_login = None
member_logins_options = set()

if allowed_users_logins == "SEE_ALL":
    company_teams = st.secrets.get("teams", {}).get(company_key, {})
    if company_teams:
        team_names = list(company_teams.keys())
        selected_team = st.selectbox("Filter by Team:", ["All Teams"] + team_names)
        
        if selected_team == "All Teams":
            for members in company_teams.values(): member_logins_options.update(members)
        else:
            member_logins_options.update(company_teams.get(selected_team, []))
        
        if member_logins_options:
            member_display_options = ["All Team Members"] + sorted([name_map.get(u, u.capitalize()) for u in member_logins_options])
            selected_member_display = st.selectbox("Filter by Team Member:", member_display_options)
            if selected_member_display != "All Team Members":
                selected_member_login = fullname_map.get(selected_member_display, selected_member_display.lower())
    else:
        st.info(f"No teams configured for {company_name}.")
else:
    member_logins_options = set(allowed_users_logins)
    if len(allowed_users_logins) > 1:
        member_display_options = ["All Team Members"] + sorted([name_map.get(u, u.capitalize()) for u in allowed_users_logins])
        selected_member_display = st.selectbox("Filter by Team Member:", member_display_options)
        if selected_member_display != "All Team Members":
            selected_member_login = fullname_map.get(selected_member_display, selected_member_display.lower())

final_logins_to_filter = []
if selected_member_login:
    final_logins_to_filter = [selected_member_login.split('@')[0].lower()]
elif member_logins_options:
    final_logins_to_filter = [name.split('@')[0].lower() for name in member_logins_options]

def filter_df_by_sales(df, sales_col_name):
    if not final_logins_to_filter:
        return df if allowed_users_logins == "SEE_ALL" else pd.DataFrame(columns=df.columns)
        
    if not sales_col_name or sales_col_name not in df.columns:
        return pd.DataFrame(columns=df.columns)

    df['clean_sales'] = df[sales_col_name].astype(str).str.lower().str.replace(r'[\s-]', '', regex=True)
    filter_regex = '|'.join(final_logins_to_filter)
    mask = df['clean_sales'].str.contains(filter_regex, na=False)
    
    return df[mask].drop(columns=['clean_sales'])

df_customers = filter_df_by_sales(df_customers, cfg_customers.get("sales_col"))
df_overdue = filter_df_by_sales(df_overdue, cfg_overdue.get("sales_col"))
df_bonuses = filter_df_by_sales(df_bonuses, cfg_bonuses.get("sales_col"))

# --- 4. ОТОБРАЖЕНИЕ ВКЛАДОК ---
st.write("---")
customers_tab, overdue_tab, bonuses_tab = st.tabs(["Customers", "Overdue", "Bonuses"])

with customers_tab:
    st.header("Team's Customers")
    if df_customers.empty: st.info("No customer data available for the current selection.")
    else:
        summary_cols = cfg_customers.get("summary_cols", list(df_customers.columns))
        display_cols = [col for col in summary_cols if col in df_customers.columns]
        st.dataframe(df_customers[display_cols].reset_index(drop=True), use_container_width=True, height=600, hide_index=True)

with overdue_tab:
    st.header("Team's Overdue Payments")
    if df_overdue.empty: st.info("No overdue payment data available for the current selection.")
    else:
        total_col = cfg_overdue.get("total_col")
        if total_col and total_col in df_overdue.columns:
            cleaned_total = df_overdue[total_col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            numeric_total = pd.to_numeric(cleaned_total, errors='coerce')
            st.metric(label="Total Overdue Amount", value=f"${numeric_total.dropna().sum():,.2f}")
            st.write("---")
        st.dataframe(df_overdue.reset_index(drop=True), use_container_width=True, height=600, hide_index=True)

with bonuses_tab:
    st.header("Team's Bonuses")
    if df_bonuses.empty: st.info("No bonus data available for the current selection.")
    else:
        st.dataframe(df_bonuses.reset_index(drop=True), use_container_width=True, height=600, hide_index=True)