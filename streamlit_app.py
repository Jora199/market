import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Настройка страницы
st.set_page_config(page_title="Price History Viewer", layout="wide")

# Функция загрузки данных с ограничением времени кэша
@st.cache_data(ttl=3600)  # Кэш будет обновляться каждый час
def load_data():
    # При каждой загрузке данных обновляем время следующего обновления кэша
    if 'cache_update_time' not in st.session_state:
        st.session_state.cache_update_time = datetime.now() + timedelta(hours=1)
    
    df = pd.read_csv("data/price_history.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def main():
    # Заголовок
    st.title("Price History Analysis")
    
    # Загрузка данных
    df = load_data()
    
    # Получение списка предметов (исключая столбец timestamp)
    items = [col for col in df.columns if col != 'timestamp']
    
    # Боковая панель с фильтрами
    with st.sidebar:
        st.subheader("Filters")
        
        # Выбор предметов
        selected_items = st.multiselect("Select items:", items)
        
        # Выбор диапазона дат
        min_date = df['timestamp'].dt.date.min()
        max_date = df['timestamp'].dt.date.max()
        date_range = st.date_input(
            "Select date range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Настройки скользящей средней
        show_ma = st.checkbox("Show Moving Average")
        if show_ma:
            ma_period = st.slider("MA Period (hours)", 1, 24, 4)
        
        # Таймер обновления кэша
        st.subheader("Cache Update Timer")
        time_until_cache_update = st.session_state.cache_update_time - datetime.now()
        
        if time_until_cache_update.total_seconds() <= 0:
            # Устанавливаем новое время обновления кэша
            st.session_state.cache_update_time = datetime.now() + timedelta(hours=1)
            time_until_cache_update = st.session_state.cache_update_time - datetime.now()
        
        minutes = int(time_until_cache_update.total_seconds() // 60)
        seconds = int(time_until_cache_update.total_seconds() % 60)
        
        st.markdown(
            f"<div style='padding: 10px; background-color: #262730; border-radius: 5px;'>"
            f"Cache update in: {minutes:02d}:{seconds:02d}"
            f"</div>",
            unsafe_allow_html=True
        )

    # Основная область с графиком
    if selected_items:
        # Фильтрация по датам
        mask = (df['timestamp'].dt.date >= date_range[0]) & (df['timestamp'].dt.date <= date_range[1])
        filtered_df = df.loc[mask]
        
        # Создание графика
        fig = go.Figure()
        
        for item in selected_items:
            # Добавление линии цены
            fig.add_trace(go.Scatter(
                x=filtered_df['timestamp'],
                y=filtered_df[item],
                mode='lines',
                name=item
            ))
            
            # Добавление скользящей средней
            if show_ma:
                window = int(ma_period * 2)
                ma = filtered_df[item].rolling(window=window).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=ma,
                    mode='lines',
                    line=dict(dash='dash'),
                    name=f'{item} MA({ma_period}h)'
                ))
        
        # Настройка макета графика
        fig.update_layout(
            height=600,
            xaxis_title="Time",
            yaxis_title="Price",
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        # Отображение графика
        st.plotly_chart(fig, use_container_width=True)
        
        # Статистика
        if len(selected_items) == 1:
            st.subheader("Statistics")
            col1, col2, col3 = st.columns(3)
            
            current_price = filtered_df[selected_items[0]].iloc[-1]
            min_price = filtered_df[selected_items[0]].min()
            max_price = filtered_df[selected_items[0]].max()
            
            col1.metric("Current Price", f"{current_price:.2f}")
            col2.metric("Minimum Price", f"{min_price:.2f}")
            col3.metric("Maximum Price", f"{max_price:.2f}")

if __name__ == "__main__":
    main()