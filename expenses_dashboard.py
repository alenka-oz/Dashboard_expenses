import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(page_title="Дашборд расходов", layout="wide")
st.title("📊 Дашборд расходов")

# URL Google Sheets (CSV экспорт)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTwJ9I4ekS5M7N30T8__ygyRsjrg2U_30IyM8Xc8QVXtZSd52PpAysNwhSNSH7fmagfy5ZOu_EJayAz/pub?gid=0&single=true&output=csv"

# Закрепленные цвета для категорий
CATEGORY_COLORS = {
    'ФОТ (исполнители)': '#FF6B6B',
    'ФОТ (офис)': '#4ECDC4',
    'Налоги': '#45B7D1',
    'Логистика и транспорт': '#FFA07A',
    'Аренда жилья': '#96CEB4',
    'Питание на смене': '#FFEAA7',
    'Форма и обувь': '#DDA0DD',
    'Штрафы (КС, Ошибки, Акты)': '#FF6348',
    'Связь': '#74B9FF',
    'Реклама': '#FD79A8',
    'Прочее': '#A29BFE',
    'Билеты': '#FDCB6E',
    'Документы': '#6C5CE7',
    'Бонусы сотрудникам (акция приведи друга или перевахтовка)': '#00B894',
    'Комиссия банка': '#E17055'
}

# Инициализация session state для дат
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None

# Функция загрузки данных
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        df['Дата'] = pd.to_datetime(df['Дата'], dayfirst=True, errors='coerce')
        df['Сумма'] = pd.to_numeric(df['Сумма'], errors='coerce')
        df = df.dropna(subset=['Сумма'])
        return df
    except Exception as e:
        st.error(f"❌ Ошибка загрузки: {e}")
        return None

# Загрузка данных
df = load_data()

if df is None or df.empty:
    st.stop()

if df['Дата'].isnull().all():
    st.error("❌ Не удалось прочитать даты.")
    st.stop()

# === БОКОВАЯ ПАНЕЛЬ И ФИЛЬТРЫ ===
st.sidebar.header("🔍 Фильтры")

# Быстрый выбор периода
st.sidebar.subheader("Быстрый выбор:")

col1, col2, col3 = st.sidebar.columns(3)

with col1:
    if st.button("День", use_container_width=True):
        last_date = df['Дата'].max().date()
        st.session_state.start_date = last_date
        st.session_state.end_date = last_date

with col2:
    if st.button("Неделя", use_container_width=True):
        last_date = df['Дата'].max().date()
        st.session_state.start_date = last_date - timedelta(days=6)
        st.session_state.end_date = last_date

with col3:
    if st.button("Всё время", use_container_width=True):
        st.session_state.start_date = df['Дата'].min().date()
        st.session_state.end_date = df['Дата'].max().date()

# Установка начальных значений, если еще не выбраны
if st.session_state.start_date is None:
    st.session_state.start_date = df['Дата'].min().date()
if st.session_state.end_date is None:
    st.session_state.end_date = df['Дата'].max().date()

# Ручной выбор дат
st.sidebar.subheader("Диапазон дат:")

min_date = df['Дата'].min().date()
max_date = df['Дата'].max().date()

start_date = st.sidebar.date_input(
    "",
    value=st.session_state.start_date,
    min_value=min_date,
    max_value=max_date,
    key="start_date_input"
)

end_date = st.sidebar.date_input(
    "",
    value=st.session_state.end_date,
    min_value=min_date,
    max_value=max_date,
    key="end_date_input"
)

# Обновляем session state при ручном изменении
st.session_state.start_date = start_date
st.session_state.end_date = end_date

# Фильтры категорий и источников
categories = sorted(df['Категория расходов'].dropna().unique())
selected_categories = st.sidebar.multiselect("Категории расходов", options=categories, default=categories)

sources = sorted(df['Источник данных'].dropna().unique())
selected_sources = st.sidebar.multiselect("Источник данных", options=sources, default=sources)

# Применение фильтров
start_ts = pd.Timestamp(st.session_state.start_date)
end_ts = pd.Timestamp(st.session_state.end_date) + pd.Timedelta(days=1)

mask = (
    (df['Дата'] >= start_ts) & 
    (df['Дата'] < end_ts) &
    (df['Категория расходов'].isin(selected_categories)) &
    (df['Источник данных'].isin(selected_sources))
)
df_filtered = df[mask].copy()

if df_filtered.empty:
    st.warning(f"⚠️ Нет данных за период {st.session_state.start_date} - {st.session_state.end_date} с выбранными фильтрами.")
    st.stop()

# === БАЗОВЫЕ МЕТРИКИ ===
st.header("📈 Ключевые показатели")

total_expenses = df_filtered['Сумма'].sum()
avg_daily = df_filtered.groupby(df_filtered['Дата'].dt.date)['Сумма'].sum().mean()
num_trans = len(df_filtered)
period_days = (end_ts - start_ts).days
avg_check = total_expenses / num_trans if num_trans > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("💰 Общие расходы", f"{total_expenses:,.0f} ₽")
with col2: st.metric("📅 Среднее в день", f"{avg_daily:,.0f} ₽")
with col3: st.metric("📝 Транзакций", num_trans)
with col4: st.metric("💳 Средний чек", f"{avg_check:,.0f} ₽")

# === ВИЗУАЛИЗАЦИИ ===
st.header("📊 Анализ расходов")

# 1. Структура (Pie Chart)
st.subheader("🥧 Структура расходов")
cat_sum = df_filtered.groupby('Категория расходов')['Сумма'].sum().reset_index().sort_values('Сумма', ascending=False)
colors_list = [CATEGORY_COLORS.get(c, '#CCCCCC') for c in cat_sum['Категория расходов']]

fig_pie = px.pie(cat_sum, values='Сумма', names='Категория расходов', hole=0.4, color_discrete_sequence=colors_list)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig_pie, use_container_width=True)

# 2. Динамика (Line Chart)
st.subheader("📈 Динамика расходов")
daily = df_filtered.groupby('Дата')['Сумма'].sum().reset_index()
fig_line = px.line(daily, x='Дата', y='Сумма', markers=True, color_discrete_sequence=['#FF6B6B'])
fig_line.update_layout(hovermode='x unified')
st.plotly_chart(fig_line, use_container_width=True)

# 3. По категориям (Bar Chart)
st.subheader("📊 Расходы по категориям")
fig_bar = px.bar(cat_sum, x='Категория расходов', y='Сумма', color='Категория расходов', 
                 color_discrete_map=CATEGORY_COLORS, text='Сумма')
fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
st.plotly_chart(fig_bar, use_container_width=True)

# 4. Топ расходов
st.subheader("🔝 Топ-10 крупнейших трат")
top = df_filtered.nlargest(10, 'Сумма')[['Дата', 'Категория расходов', 'Сумма', 'Описание']].copy()
top['Дата'] = top['Дата'].dt.strftime('%d.%m.%Y')
top['Сумма'] = top['Сумма'].apply(lambda x: f"{x:,.0f} ₽")
st.dataframe(top, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"🔄 Обновлено: {datetime.now().strftime('%H:%M')} | Всего записей в базе: {len(df)}")
