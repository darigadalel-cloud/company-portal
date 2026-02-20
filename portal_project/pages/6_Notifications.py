# pages/3_Notification_History.py
import streamlit as st
import pandas as pd
import gspread
from utils import load_data, get_spreadsheet
from urllib.parse import quote
from utils import load_data, load_lottieurl
from streamlit_lottie import st_lottie
# --- 1. НАСТРОЙКА СТРАНИЦЫ И ПРОВЕРКА ДОСТУПА ---
LOGO_URL = "https://i.ibb.co/Qvy4G6DR/images.png"
st.set_page_config(layout="wide", page_title="Notifications", page_icon=LOGO_URL)


if not st.session_state.get("authenticated", False):
    st.error("Please log in to view this page.")
    if st.button("Go to Login Page"): st.switch_page("portal.py")
    st.stop()

if not st.session_state.get("selected_company"):
    st.warning("Please select a company on the main Portal page first.")
    if st.button("Go to Company Selection"): st.switch_page("portal.py")
    st.stop()

st.title("📜 Expiration Notifications (30 Days)")

# --- 2. ДИНАМИЧЕСКАЯ КОНФИГУРАЦИЯ ---
company_key = st.session_state['selected_company']
company_name = st.secrets.get("companies", {}).get(company_key, company_key.replace('_', ' ').title())
st.subheader(f"Displaying data for: {company_name}")

page_config = st.secrets.get("page_settings", {}).get("notifications", {})
company_config = page_config.get(company_key, {})

if not company_config or not company_config.get("worksheet"):
    st.warning(f"No 'Notifications' data or configuration found for {company_name}.")
    st.stop()

# Присваиваем настройки переменным
worksheet_name = company_config.get("worksheet")
sales_col = company_config.get("sales_col")
client_col = company_config.get("client_col")
portal_col = company_config.get("portal_col")
days_left_col = company_config.get("days_left_col")
expiry_date_col = company_config.get("expiry_date_col")
id_col = company_config.get("id_col")
noted_by_col = company_config.get("noted_by_col")
filter_col = company_config.get("filter_col")
filter_val = company_config.get("filter_val")
exclude_vals = company_config.get("exclude_vals")

# --- 3. ФУНКЦИЯ ОБНОВЛЕНИЯ GOOGLE SHEET ---
def update_notification_status(sheet_name, id_to_update, username_to_add, id_col_name, noted_by_col_name):
    """Находит уведомление по ID и добавляет пользователя в список 'отметивших'."""
    try:
        sh = get_spreadsheet()
        if not sh: return False
        sheet = sh.worksheet(sheet_name)
        
        cell = sheet.find(str(id_to_update), in_column=sheet.find(id_col_name).col)
        if not cell: return False
        
        headers = sheet.row_values(1)
        noted_by_col_index = headers.index(noted_by_col_name) + 1
        
        current_noted_by_str = sheet.cell(cell.row, noted_by_col_index).value or ""
        noted_by_list = [name.strip() for name in current_noted_by_str.split(',') if name.strip()]
        
        if username_to_add not in noted_by_list:
            noted_by_list.append(username_to_add)
            new_noted_by_str = ', '.join(noted_by_list)
            sheet.update_cell(cell.row, noted_by_col_index, new_noted_by_str)
            st.cache_data.clear() # Очищаем кэш для обновления страницы
        return True
    except Exception:
        return False

# --- 4. ЗАГРУЗКА И ФИЛЬТРАЦИЯ ДАННЫХ ---
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

if df_original.empty:
    st.info(f"No upcoming 30-day expirations were found for {company_name}.")
    st.stop()

# Проверка наличия всех необходимых колонок
required_cols = [sales_col, client_col, portal_col, days_left_col, expiry_date_col, id_col, noted_by_col]
if not all(col and col in df_original.columns for col in required_cols):
    st.error(f"The '{worksheet_name}' sheet is missing one or more required columns defined in secrets.toml.")
    st.stop()

# Фильтрация (включение/исключение)
if filter_col and filter_val and filter_col in df_original.columns:
    df_original = df_original[df_original[filter_col] == filter_val].copy()
elif filter_col and exclude_vals and isinstance(exclude_vals, list):
    df_original = df_original[~df_original[filter_col].isin(exclude_vals)].copy()

# Фильтрация по пользователю
username = st.session_state.get("username", "").strip().lower()
simple_name = username.split('@')[0].replace('.', '').replace('-', '')

if username not in ["admin", "dariga","erik", "shelby","operations"]:
    mask = df_original[sales_col].str.strip().str.lower().str.contains(simple_name, na=False)
    df_display = df_original[mask].copy()
else:
    df_display = df_original.copy()

# --- 5. ОТОБРАЖЕНИЕ УВЕДОМЛЕНИЙ ---
st.write("---")
    
if df_display.empty:
    st.success(f"No expiration notifications found for you in {company_name}.")
else:
    df_display[noted_by_col] = df_display[noted_by_col].fillna('')
    df_display['is_noted_by_user'] = df_display[noted_by_col].apply(lambda x: simple_name in x.lower().split(','))
    df_display['SortableDate'] = pd.to_datetime(df_display[expiry_date_col], errors='coerce')
    df_display = df_display.sort_values(by=['is_noted_by_user', 'SortableDate'], ascending=[True, True])

    st.write(f"#### Showing {len(df_display)} notifications:")
    
    for _, row in df_display.iterrows():
        client_name_val = row[client_col]
        trans_id_val = str(row[id_col]).strip()
        noted_by_val = row[noted_by_col]
        is_noted_by_me = simple_name in [name.strip().lower() for name in noted_by_val.split(',')]
        
        # Ссылка для перехода на страницу Customers
        link = f"Customers?search={quote(client_name_val)}"
        
        container = st.container(border=True)
        if is_noted_by_me:
            container.markdown(f"""
            <div style="opacity: 0.6;">
                <p>
                    <b>Client:</b> <a href="{link}" target="_self">{client_name_val}</a> <i>(You noted this)</i><br>
                    <b>Expires in:</b> {row[days_left_col]} days on {row[expiry_date_col]}<br>
                    <small><i>Noted by: {noted_by_val}</i></small>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            col1, col2 = container.columns([4, 1.2])
            col1.markdown(f"#### Client: [{client_name_val}]({link})")
            col1.markdown(f"**Portal:** {row[portal_col]}")
            
            col2.error(f"Expires in {row[days_left_col]} days")
            col2.caption(f"**Sales Rep:** {row[sales_col]}")
            
            container.button(
                "✅ Noted", 
                key=f"noted_{trans_id_val}",
                on_click=update_notification_status,
                args=(worksheet_name, trans_id_val, simple_name, id_col, noted_by_col)
            )