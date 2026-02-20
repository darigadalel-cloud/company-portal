# pages/3_Bonuses.py
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from utils import load_data, load_lottieurl
from streamlit_lottie import st_lottie

# --- ИСПРАВЛЕНИЕ 1: Добавляем функцию для исправления дубликатов колонок ---
def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Автоматически исправляет дубликаты колонок и убирает лишние пробелы."""
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
st.set_page_config(layout="wide", page_title="Bonus", page_icon=LOGO_URL)


if not st.session_state.get("authenticated", False):
    st.error("Please log in to view this page.")
    if st.button("Go to Login Page"): st.switch_page("portal.py")
    st.stop()

if not st.session_state.get("selected_company"):
    st.warning("Please select a company on the main Portal page first.")
    if st.button("Go to Company Selection"): st.switch_page("portal.py")
    st.stop()

st.title("Bonus List")

# --- 2. ДИНАМИЧЕСКАЯ КОНФИГУРАЦИЯ И ПРОВЕРКА ДОСТУПНОСТИ ---
company_key = st.session_state['selected_company']
company_name = st.secrets.get("companies", {}).get(company_key, company_key.replace('_', ' ').title())

page_config = st.secrets.get("page_settings", {}).get("bonuses", {})
company_config = page_config.get(company_key, {})

if not company_config or not company_config.get("worksheet"):
    st.warning(f"The 'Bonuses' feature is not available for {company_name}.")
    st.stop()

st.subheader(f"Displaying data for: {company_name}")

worksheet_name = company_config.get("worksheet")
sales_col = company_config.get("sales_col")
shipment_col = company_config.get("shipment_col")
month_col = company_config.get("month_col")
result_col = company_config.get("result_col")
summary_cols_config = company_config.get("summary_cols", [])

# --- 3. ЗАГРУЗКА И ФИЛЬТРАЦИЯ ДАННЫХ ---
# 1. Загружаем саму анимацию
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

# Применяем санитарную обработку сразу после загрузки
if not df_original.empty:
    df_original = sanitize_columns(df_original)

if df_original.empty:
    st.warning(f"No bonus info found for {company_name}.")
    st.stop()

username = st.session_state.get("username", "").strip().lower()
if username not in ["admin", "dariga","erik", "shelby","operations"]:
    simple_name = username.split('@')[0].replace('.', '').replace('-', '')
    if sales_col and sales_col in df_original.columns:
        df_original['clean_sales'] = df_original[sales_col].astype(str).str.lower().str.replace(' ', '')
        df_user = df_original[df_original['clean_sales'].str.contains(simple_name, na=False)].copy()
        df_user = df_user.drop(columns=['clean_sales'])
    else:
        st.error(f"Configuration Error: Sales column '{sales_col}' not found.")
        st.stop()
else:
    df_user = df_original.copy()

if df_user.empty:
    st.info(f"No bonus information found for you.")
    st.stop()

# --- 4. UI: ПОИСК И ФИЛЬТРЫ ---
df_display = df_user.copy()

if shipment_col and shipment_col in df_display.columns:
    search_term = st.text_input(f"Search by {shipment_col}:", placeholder="Enter shipment number...").strip().lower()
    if search_term:
        df_display = df_display[df_display[shipment_col].astype(str).str.lower().str.contains(search_term)]

if month_col and month_col in df_display.columns:
    # 1. Получаем номер текущего месяца (например, 10 для октября)
    current_month_number = datetime.now().month
    current_month_name = datetime.now().strftime('%B')

    # 2. Информируем пользователя о том, что он видит
    st.info(f"Displaying bonuses for the current month: **{current_month_name}**")

    # 3. Применяем фильтр к DataFrame
    # pd.to_numeric(..., errors='coerce') безопасно преобразует колонку в числа
    df_display = df_display[pd.to_numeric(df_display[month_col], errors='coerce') == current_month_number]
# --- 5. ОТОБРАЖЕНИЕ ТАБЛИЦЫ ---
st.write("---")
show_all_columns = st.toggle("Show all columns", value=False)
if not show_all_columns:
    existing_summary_cols = [col for col in summary_cols_config if col in df_display.columns]
    if existing_summary_cols:
        df_display = df_display[existing_summary_cols]

def highlight_result(row):
    style = [''] * len(row)
    if result_col and result_col in row.index:
        keywords = ["second part?", "ops need to fix", "error", "we or ops need fix"]
        result_text = str(row[result_col]).strip().lower()
        if any(keyword in result_text for keyword in keywords):
            style = ['background-color: #FFCCCB; color: #721c24;'] * len(row)
    return style

# --- ИСПРАВЛЕНИЕ 2: Добавляем проверку на пустой DataFrame ПЕРЕД стилизацией ---
if df_display.empty:
    st.info("No records match your current search and filter criteria.")
else:
    df_display = df_display.reset_index(drop=True)
    st.dataframe(df_display.style.apply(highlight_result, axis=1), use_container_width=True, height=800, hide_index=True)