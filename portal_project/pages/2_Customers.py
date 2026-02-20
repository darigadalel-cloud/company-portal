# pages/2_Customers.py
import streamlit as st
import pandas as pd
from utils import load_data, load_lottieurl
from streamlit_lottie import st_lottie

# --- Функция для исправления дубликатов колонок ---
def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
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
st.set_page_config(layout="wide", page_title="Customers", page_icon=LOGO_URL)


if not st.session_state.get("authenticated", False):
    st.error("Please log in to view this page.")
    if st.button("Go to Login Page"):
        st.switch_page("portal.py")
    st.stop()

if not st.session_state.get("selected_company"):
    st.warning("Please select a company on the main Portal page first.")
    if st.button("Go to Company Selection"):
        st.switch_page("portal.py")
    st.stop()

st.title("Customers List")

# --- 2. ДИНАМИЧЕСКАЯ КОНФИГУРАЦИЯ ---
company_key = st.session_state['selected_company']
company_name = st.secrets.get("companies", {}).get(company_key, company_key.replace('_', ' ').title())
st.subheader(f"Displaying data for: {company_name}")

# Загружаем настройки для страницы 'customers'
page_config = st.secrets.get("page_settings", {}).get("customers", {})
company_config = page_config.get(company_key, {})

if not company_config or not company_config.get("worksheet"):
    st.warning(f"No 'Customers' data or configuration found for {company_name}.")
    st.stop()

# Присваиваем настройки переменным
worksheet_name = company_config.get("worksheet")
sales_col = company_config.get("sales_col")
customer_col = company_config.get("customer_col")
status_col = company_config.get("status_col")
summary_cols_config = company_config.get("summary_cols", [])
filter_col = company_config.get("filter_col")
filter_val = company_config.get("filter_val")
exclude_vals = company_config.get("exclude_vals")

# --- 3. ЗАГРУЗКА И ПРЕДВАРИТЕЛЬНАЯ ФИЛЬТРАЦИЯ ---
# 1. Загружаем саму анимацию
LOTTIE_URL = "https://lottie.host/7e008b8b-3375-4754-8c38-c30454a43a04/Lg9q5pAs7S.json"
lottie_animation = load_lottieurl(LOTTIE_URL)

# 2. Создаем "пустое место" (placeholder)
# 1. Загружаем саму анимацию
LOTTIE_URL = "https://lottie.host/7e008b8b-3375-4754-8c38-c30454a43a04/Lg9q5pAs7S.json"
lottie_animation = load_lottieurl(LOTTIE_URL)

# 2. Создаем "плейсхолдер" (в него вставляем анимацию)
placeholder = st.empty()

with placeholder.container():
    st.markdown(
        """
        <style>
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 300px;
            background-color: transparent;
        }

        .lds-spinner {
          display: inline-block;
          position: relative;
          width: 80px;
          height: 80px;
        }

        .lds-spinner div {
          transform-origin: 40px 40px;
          animation: lds-spinner 1.2s linear infinite;
        }

        .lds-spinner div:after {
          content: " ";
          display: block;
          position: absolute;
          top: 3px;
          left: 37px;
          width: 6px;
          height: 18px;
          border-radius: 20%;
          background: #d3d3d3;
        }

        .lds-spinner div:nth-child(1) { transform: rotate(0deg);   animation-delay: -1.1s; }
        .lds-spinner div:nth-child(2) { transform: rotate(30deg);  animation-delay: -1s; }
        .lds-spinner div:nth-child(3) { transform: rotate(60deg);  animation-delay: -0.9s; }
        .lds-spinner div:nth-child(4) { transform: rotate(90deg);  animation-delay: -0.8s; }
        .lds-spinner div:nth-child(5) { transform: rotate(120deg); animation-delay: -0.7s; }
        .lds-spinner div:nth-child(6) { transform: rotate(150deg); animation-delay: -0.6s; }
        .lds-spinner div:nth-child(7) { transform: rotate(180deg); animation-delay: -0.5s; }
        .lds-spinner div:nth-child(8) { transform: rotate(210deg); animation-delay: -0.4s; }
        .lds-spinner div:nth-child(9) { transform: rotate(240deg); animation-delay: -0.3s; }
        .lds-spinner div:nth-child(10){ transform: rotate(270deg); animation-delay: -0.2s; }
        .lds-spinner div:nth-child(11){ transform: rotate(300deg); animation-delay: -0.1s; }
        .lds-spinner div:nth-child(12){ transform: rotate(330deg); animation-delay: 0s; }

        @keyframes lds-spinner {
          0% { opacity: 1; }
          100% { opacity: 0; }
        }

        .loading-text {
            color: #bfbfbf;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            letter-spacing: 2px;
            margin-top: 20px;
        }
        </style>

        <div class="loading-container">
          <div class="lds-spinner">
            <div></div><div></div><div></div><div></div><div></div><div></div>
            <div></div><div></div><div></div><div></div><div></div><div></div>
          </div>
          <div class="loading-text">LOADING ...</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- 3. ЗАГРУЗКА И ПРЕДВАРИТЕЛЬНАЯ ФИЛЬТРАЦИЯ ---
# <-- ВОТ ЗДЕСЬ ПРОИСХОДИТ "ДОЛГАЯ" ОПЕРАЦИЯ

df_original = load_data(worksheet_name=worksheet_name)
placeholder.empty()

if not df_original.empty:
    df_original = sanitize_columns(df_original)

if df_original.empty:
    st.warning(f"No customer info found for {company_name} in the '{worksheet_name}' sheet.")
    st.stop()

# Логика фильтрации по типу (включение/исключение)
if filter_col and filter_val and filter_col in df_original.columns:
    df_original = df_original[df_original[filter_col] == filter_val].copy()
elif filter_col and exclude_vals and filter_col in df_original.columns:
    if isinstance(exclude_vals, list):
        df_original = df_original[~df_original[filter_col].isin(exclude_vals)].copy()

if df_original.empty:
    st.info(f"No data matching the specified filters was found for {company_name}.")
    st.stop()

# --- 4. ФИЛЬТРАЦИЯ ПО ПОЛЬЗОВАТЕЛЮ ---
username = st.session_state.get("username", "").strip().lower()
df_user = pd.DataFrame()

if sales_col and sales_col in df_original.columns:
    if username in ["admin", "dariga","erik", "shelby","operations"]:
        df_user = df_original.copy()
    else:
        simple_name = username.split('@')[0].replace('.', '').replace('-', '')
        df_original['clean_sales'] = df_original[sales_col].astype(str).str.lower().str.replace(' ', '').str.replace('-', '')
        df_user = df_original[df_original['clean_sales'].str.contains(simple_name, na=False)].copy()
        df_user = df_user.drop(columns=['clean_sales'])
else:
    st.error(f"Configuration Error: Sales column '{sales_col}' not found in '{worksheet_name}'.")
    st.stop()

if df_user.empty:
    st.info(f"No clients found for you in {company_name}.")
    st.stop()

# --- 5. UI: ПОИСК И ФИЛЬТРЫ ---
search_col, filter_col_ui = st.columns([2, 1]) 
df_display = df_user.copy()

with search_col:
    if customer_col and customer_col in df_display.columns:
        search_term = st.text_input(f"Search by {customer_col.title()}:", placeholder="Enter client name...").strip().lower()
        if search_term:
            df_display = df_display[df_display[customer_col].astype(str).str.lower().str.contains(search_term, na=False)]

with filter_col_ui:
    if status_col and status_col in df_display.columns:
        status_options = ["All"] + sorted(df_display[status_col].dropna().unique())
        status_filter = st.selectbox(f"Filter by {status_col.title()}:", status_options)
        if status_filter != "All":
            df_display = df_display[df_display[status_col] == status_filter]

# --- 6. ОТОБРАЖЕНИЕ ТАБЛИЦЫ ---
def highlight_status(row):
    if not status_col: return [''] * len(row)
    style = [''] * len(row)
    if status_col in row.index:
        status = str(row[status_col]).strip().lower()
        if status == 'blacklist':
            style = ['background-color: #555555; color: white;'] * len(row)
        elif status in ['on hold', 'claimed']:
            style = ['background-color: #FFCCCB; color: black;'] * len(row)
    return style

st.write("---") 

show_all_columns = st.toggle("Show all columns", value=False)
if show_all_columns:
    st.info("💡 Detailed view is enabled. All columns are shown.")
    # df_display остается как есть
else:
    # Динамически выбираем колонки для краткого вида из конфига
    existing_summary_columns = [col for col in summary_cols_config if col in df_display.columns]
    if existing_summary_columns:
        df_display = df_display[existing_summary_columns]

df_display = df_display.reset_index(drop=True)

st.dataframe(
    df_display.style.apply(highlight_status, axis=1), 
    use_container_width=True, 
    height=800,
    hide_index=True
)