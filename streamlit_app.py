import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Настройка страницы
st.set_page_config(page_title="Price History Viewer", layout="wide")

# Функция загрузки данных с отслеживанием изменений файла
@st.cache_data(ttl=60)  # Кеш истекает каждые 60 секунд
def load_data():
    file_path = "data/price_history.csv"
    
    # Получаем время последнего изменения файла
    last_modified = os.path.getmtime(file_path)
    
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Добавляем время последнего изменения в кеш
    return df, last_modified

def main():
    # Заголовок
    st.title("Price History Analysis")
    
    # Загрузка данных
    df, _ = load_data()
    
    # Получение списка предметов (исключая столбец timestamp)
    items = [col for col in df.columns if col != 'timestamp']
    
    # Боковая панель с фильтрами
    with st.sidebar:
        st.header("Фильтры")
        
        # Выбор предмета
        selected_items = st.multiselect(
            "Выберите предметы",
            items,
            default=[items[0]]  # По умолчанию выбран первый предмет
        )
        
        # Выбор временного диапазона
        date_range = st.date_input(
            "Выберите период",
            value=(df['timestamp'].min().date(), df['timestamp'].max().date()),
            min_value=df['timestamp'].min().date(),
            max_value=df['timestamp'].max().date()
        )
        
        # Показывать скользящую среднюю
        show_ma = st.checkbox("Показать скользящую среднюю", value=True)
        if show_ma:
            ma_period = st.slider("Период скользящей средней (часов)", 1, 24, 6)

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
                window = int(ma_period * 2)  # *2 так как точки каждые 30 минут
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
            xaxis_title="Время",
            yaxis_title="Цена",
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
            st.subheader("Статистика")
            col1, col2, col3 = st.columns(3)
            
            current_price = filtered_df[selected_items[0]].iloc[-1]
            min_price = filtered_df[selected_items[0]].min()
            max_price = filtered_df[selected_items[0]].max()
            
            col1.metric("Текущая цена", f"{current_price:.2f}")
            col2.metric("Минимальная цена", f"{min_price:.2f}")
            col3.metric("Максимальная цена", f"{max_price:.2f}")

if __name__ == "__main__":
    main()