import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Настройка страницы
st.set_page_config(page_title="Price History Viewer", layout="wide")

# Добавляем функцию загрузки изображений
@st.cache_data
def load_images():
    try:
        img_dict = {}
        with open("data/img.csv", 'r', encoding='utf-8') as f:
            for line in f:
                # Разделяем строку по "https:"
                parts = line.split('https:"')
                if len(parts) == 2:
                    # Очищаем название от лишних символов
                    name = parts[0].replace('https', '').strip()
                    # Очищаем URL от кавычек и пробелов
                    url = parts[1].strip().strip('"')
                    # Добавляем протокол обратно
                    url = 'https://' + url
                    img_dict[name] = url
        return img_dict
    except Exception as e:
        st.error(f"Ошибка при загрузке файла img.csv: {str(e)}")
        return {}

# Остальные функции загрузки данных остаются без изменений
@st.cache_data(ttl=60)
def load_data():
    file_path = "data/price_history.csv"
    last_modified = os.path.getmtime(file_path)
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df, last_modified

@st.cache_data
def load_supply_data():
    supply_path = "data/nft_supply_results.csv"
    try:
        supply_df = pd.read_csv(supply_path)
        supply_dict = dict(zip(supply_df['Item Name'], supply_df['Estimated Supply']))
        return supply_dict
    except FileNotFoundError:
        st.error(f"Файл {supply_path} не найден.")
        return {}

def main():
    # Заголовок
    st.title("Price History Analysis")
    
    # Загрузка данных
    df, _ = load_data()
    supply_dict = load_supply_data()
    img_dict = load_images()
    
    # Дефолтное изображение
    default_img = "https://ibb.co/Qv84JNZY"
    
    # Получение списка предметов
    items = [col for col in df.columns if col != 'timestamp']
    
    # Показываем общее количество отслеживаемых предметов
    st.metric("Total Items Tracked", len(items))
    
    # Создаем список items_with_supply для отображения в селекторе
    items_with_supply = [f"{item} (Supply: {int(supply_dict.get(item, 0))})" for item in items]
    display_to_original = dict(zip(items_with_supply, items))
    
    # Боковая панель с фильтрами
    with st.sidebar:
        st.header("Фильтры")
        selected_items_with_supply = st.multiselect(
            "Выберите предметы",
            items_with_supply,
            default=[items_with_supply[0]] if items_with_supply else []
        )
        selected_items = [display_to_original[item] for item in selected_items_with_supply]
        
        date_range = st.date_input(
            "Выберите период",
            value=(df['timestamp'].min().date(), df['timestamp'].max().date()),
            min_value=df['timestamp'].min().date(),
            max_value=df['timestamp'].max().date()
        )
        
        show_ma = st.checkbox("Показать скользящую среднюю", value=True)
        if show_ma:
            ma_period = st.slider("Период скользящей средней (часов)", 1, 24, 6)

    # Отображение изображений выбранных предметов
    if selected_items:
        # Создаем сетку для изображений
        cols = st.columns(min(len(selected_items), 4))  # Максимум 4 колонки
        for idx, item in enumerate(selected_items):
            col_idx = idx % 4  # Определяем, в какую колонку поместить изображение
            with cols[col_idx]:
                # Получаем ссылку на изображение или используем дефолтное
                img_url = img_dict.get(item, default_img)
                st.image(img_url, caption=item, use_column_width=True)
                
    # Основная область с графиком
    if selected_items:
        # Фильтрация по датам
        mask = (df['timestamp'].dt.date >= date_range[0]) & (df['timestamp'].dt.date <= date_range[1])
        filtered_df = df.loc[mask]
        
        # Создание графика
        fig = go.Figure()
        
        for item in selected_items:
            fig.add_trace(go.Scatter(
                x=filtered_df['timestamp'],
                y=filtered_df[item],
                mode='lines',
                name=f"{item} (Supply: {int(supply_dict.get(item, 0))})"
            ))
            
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
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Статистика
        if len(selected_items) == 1:
            st.subheader("Статистика")
            col1, col2, col3, col4 = st.columns(4)
            
            item = selected_items[0]
            current_price = filtered_df[item].iloc[-1]
            min_price = filtered_df[item].min()
            max_price = filtered_df[item].max()
            supply = supply_dict.get(item, 0)
            
            col1.metric("Текущая цена", f"{current_price:.2f}")
            col2.metric("Минимальная цена", f"{min_price:.2f}")
            col3.metric("Максимальная цена", f"{max_price:.2f}")
            col4.metric("Supply", f"{int(supply)}")

if __name__ == "__main__":
    main()