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
    df = pd.read_csv("data/price_history.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def main():
    # Заголовок
    st.title("Price History Analysis")
    
    # Информация об обновлениях в сайдбаре
    with st.sidebar:
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        
        last_update = st.session_state.last_update
        next_update = last_update + timedelta(hours=1)
        
        # Отладочная информация
        st.write("Debug info:")
        st.write(f"Last update: {last_update}")
        st.write(f"Next update: {next_update}")
        st.write(f"Current time: {datetime.now()}")
        st.write(f"Time left: {(next_update - datetime.now()).total_seconds()} seconds")
        
        placeholder = st.empty()
        placeholder.markdown(
            f"""
            <div style='color: white; font-size: 14px; padding: 0.5em 0;'>
                До обновления: <span id='countdown_timer'>00:00</span>
            </div>
            <script>
                console.log('Script started');
                console.log('Target date:', '{next_update.strftime("%Y-%m-%d %H:%M:%S")}');
                
                function updateCountdown() {{
                    try {{
                        const targetDate = new Date('{next_update.strftime("%Y-%m-%d %H:%M:%S")}');
                        const currentDate = new Date();
                        
                        console.log('Target:', targetDate);
                        console.log('Current:', currentDate);
                        
                        let timeLeft = targetDate - currentDate;
                        console.log('Time left (ms):', timeLeft);
                        
                        if (timeLeft > 0) {{
                            const minutes = Math.floor(timeLeft / (1000 * 60));
                            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
                            
                            const formattedTime = 
                                minutes.toString().padStart(2, '0') + ':' + 
                                seconds.toString().padStart(2, '0');
                            
                            console.log('Formatted time:', formattedTime);
                            document.getElementById('countdown_timer').textContent = formattedTime;
                        }} else {{
                            console.log('Time expired');
                            document.getElementById('countdown_timer').textContent = "00:00";
                            window.location.reload();
                        }}
                    }} catch (e) {{
                        console.error('Timer error:', e);
                    }}
                }}

                // Попробуем разные способы запуска
                window.addEventListener('load', function() {{
                    console.log('Window loaded');
                    updateCountdown();
                    setInterval(updateCountdown, 1000);
                }});
                
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DOM loaded');
                    updateCountdown();
                    setInterval(updateCountdown, 1000);
                }});
                
                // Немедленный запуск с небольшой задержкой
                setTimeout(function() {{
                    console.log('Delayed start');
                    updateCountdown();
                    setInterval(updateCountdown, 1000);
                }}, 100);
            </script>
            """,
            unsafe_allow_html=True
        )

    # Загрузка данных
    df = load_data()
    
    # Получение списка предметов (исключая столбец timestamp)
    items = [col for col in df.columns if col != 'timestamp']
    
    # Боковая панель с фильтрами
    with st.sidebar:
        st.header("Фильтры")
        
        # Выбор предмета
        selected_items = st.multiselect(
            "Выберите предметы",
            items,
            default=[items[0]]
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

    if datetime.now() >= next_update:
        st.session_state.last_update = datetime.now()
        st.experimental_rerun()

if __name__ == "__main__":
    main()