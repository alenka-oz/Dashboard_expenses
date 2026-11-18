import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Дашборд расходов", layout="wide")
st.title("📊 Дашборд расходов")

# URL Google Sheets (CSV экспорт)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTwJ9I4ekS5M7N30T8__ygyRsjrg2U_30IyM8Xc8QVXtZSd52PpAysNwhSNSH7fmagfy5ZOu_EJayAz/pub?gid=0&single=true&output=csv"

# Закрепленные цвета для категорий
CATEGORY_COLORS = {
    'ФОТ (исполнители)': '#FF6B6B',      # Красный
    'ФОТ (офис)': '#4ECDC4',              # Бирюзовый
    'Налоги': '#45B7D1',                  # Голубой
    'Логистика и транспорт': '#FFA07A',   # Лососевый
    'Аренда жилья': '#96CEB4',            # Мятный
    'Питание на смене': '#FFEAA7',        # Желтый
    'Форма и обувь': '#DDA0DD',           # Сливовый
    'Штрафы (КС, Ошибки, Акты)': '#FF6348',  # Оранжево-красный
    'Связь': '#74B9FF',                   # Светло-голубой
    'Реклама': '#FD79A8',                 # Розовый
    'Прочее': '#A29BFE',                  # Лавандовый
    'Билеты': '#FDCB6E',                  # Золотистый
    'Документы': '#6C5CE7',               # Фиолетовый
    'Бонусы сотрудникам (акция приведи друга или перевахтовка)': '#00B894',  # Зеленый
    'Комиссия банка': '#E17055'           # Терракотовый
}

# Функция загрузки данных
@st.cache_data(ttl=300)  # 5 минут = 300 секунд
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # Преобразование типов данных
        df['Дата'] = pd.to_datetime(df['Дата'], dayfirst=True)
        df['Сумма'] = pd.to_numeric(df['Сумма'], errors='coerce')
        
        # Удаление строк с пустыми значениями суммы
        df = df.dropna(subset=['Сумма'])
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

# Загрузка данных
df = load_data()

if df is None or df.empty:
    st.stop()

# Боковая панель с фильтрами
st.sidebar.header("🔍 Фильтры")

# Фильтр по дате
min_date = df['Дата'].min().date()
max_date = df['Дата'].max().date()

start_date = st.sidebar.date_input(
    "Дата начала",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "Дата окончания",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Фильтр по категории
categories = sorted(df['Категория расходов'].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Категории расходов",
    options=categories,
    default=categories
)

# Фильтр по источнику данных
sources = sorted(df['Источник данных'].dropna().unique())
selected_sources = st.sidebar.multiselect(
    "Источник данных",
    options=sources,
    default=sources
)

# Применение фильтров
df_filtered = df[
    (df['Дата'].dt.date >= start_date) & 
    (df['Дата'].dt.date <= end_date) &
    (df['Категория расходов'].isin(selected_categories)) &
    (df['Источник данных'].isin(selected_sources))
].copy()

# Проверка наличия данных после фильтрации
if df_filtered.empty:
    st.warning("⚠️ Нет данных за выбранный период с примененными фильтрами")
    st.stop()

# === БАЗОВЫЕ МЕТРИКИ ===

st.header("📈 Ключевые показатели")

# Расчет метрик
total_expenses = df_filtered['Сумма'].sum()
avg_daily_expenses = df_filtered.groupby('Дата')['Сумма'].sum().mean()
num_transactions = len(df_filtered)
period_days = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days + 1
avg_transaction = total_expenses / num_transactions if num_transactions > 0 else 0

# Отображение метрик в колонках
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 Общие расходы",
        value=f"{total_expenses:,.0f} ₽"
    )

with col2:
    st.metric(
        label="📅 Средние расходы в день",
        value=f"{avg_daily_expenses:,.0f} ₽"
    )

with col3:
    st.metric(
        label="📝 Количество транзакций",
        value=num_transactions
    )

with col4:
    st.metric(
        label="💳 Средний расход",
        value=f"{avg_transaction:,.0f} ₽"
    )

# === ВИЗУАЛИЗАЦИИ ===

st.header("📊 Анализ расходов")

# 1. Структура расходов по категориям
st.subheader("🥧 Структура расходов по категориям")

category_summary = df_filtered.groupby('Категория расходов')['Сумма'].sum().reset_index()
category_summary = category_summary.sort_values('Сумма', ascending=False)

# Создаем список цветов в соответствии с порядком категорий
colors_list = [CATEGORY_COLORS.get(cat, '#CCCCCC') for cat in category_summary['Категория расходов']]

fig_pie = px.pie(
    category_summary,
    values='Сумма',
    names='Категория расходов',
    title='Доля категорий в общих расходах',
    hole=0.4,
    color_discrete_sequence=colors_list
)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
fig_pie.update_layout(height=500)
st.plotly_chart(fig_pie, use_container_width=True)

# 2. Динамика расходов во времени
st.subheader("📈 Динамика расходов")

daily_expenses = df_filtered.groupby('Дата')['Сумма'].sum().reset_index()

fig_line = px.line(
    daily_expenses,
    x='Дата',
    y='Сумма',
    title='Ежедневные расходы',
    markers=True,
    color_discrete_sequence=['#FF6B6B']
)
fig_line.update_layout(
    xaxis_title='Дата', 
    yaxis_title='Сумма (₽)',
    hovermode='x unified'
)
st.plotly_chart(fig_line, use_container_width=True)

# 3. Расходы по категориям (столбчатая диаграмма)
st.subheader("📊 Расходы по категориям")

fig_bar = px.bar(
    category_summary,
    x='Категория расходов',
    y='Сумма',
    title='Расходы по категориям',
    color='Категория расходов',
    color_discrete_map=CATEGORY_COLORS,
    text='Сумма'
)
fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_bar.update_layout(
    xaxis_title='Категория', 
    yaxis_title='Сумма (₽)', 
    showlegend=False,
    xaxis_tickangle=-45
)
st.plotly_chart(fig_bar, use_container_width=True)

# 4. Топ расходов
st.subheader("🔝 Топ-10 крупнейших расходов")

top_expenses = df_filtered.nlargest(10, 'Сумма')[['Дата', 'Категория расходов', 'Сумма', 'Описание']].copy()
top_expenses['Дата'] = top_expenses['Дата'].dt.strftime('%d.%m.%Y')
top_expenses['Сумма'] = top_expenses['Сумма'].apply(lambda x: f"{x:,.0f} ₽")

st.dataframe(top_expenses, use_container_width=True, hide_index=True)

# 5. Детальная таблица
with st.expander("📋 Детальные данные"):
    df_display = df_filtered[['Дата', 'Категория расходов', 'Сумма', 'Описание', 'Источник данных']].copy()
    df_display['Дата'] = df_display['Дата'].dt.strftime('%d.%m.%Y')
    df_display['Сумма'] = df_display['Сумма'].apply(lambda x: f"{x:,.0f} ₽")
    df_display = df_display.sort_values('Дата', ascending=False)
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"🔄 Данные обновлены: {datetime.now().strftime('%d.%m.%Y %H:%M')} | 📊 Всего записей: {len(df)}")
