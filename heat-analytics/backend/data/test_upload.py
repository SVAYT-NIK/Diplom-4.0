"""Test script to validate Excel parsing logic."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Create a test Excel file matching the expected format
def create_test_excel():
    output_path = Path(__file__).parent / "test_sample.xlsx"
    
    # Create metadata rows (rows 1-4)
    metadata = [
        ["Отчет сформирован: 01.01.2024"],
        ["Тепловычислитель: ТВ-01"],
        ["Потребитель: ул. Ленина, д. 1"],
        ["Схема: 3,8"],
    ]
    
    # Create headers (row 5)
    headers = ["Дата", "Время", "Состояние", "Отключение", "НС", "Время НС", "T1", "T2", "P1", "P2", 
               "V1", "V2", "M1", "M2", "Q", "d T", "d V", "d M", "Небаланс", "Ти", "Тост", "Тхв", 
               "Система сбора данных"]
    
    # Create sample data (rows 6+)
    data_rows = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        row = [
            date.strftime("%d.%m.%Y"),  # Дата
            "00:00",  # Время
            "OK",  # Состояние
            "",  # Отключение
            "",  # НС
            "",  # Время НС
            95.5 + np.random.uniform(-5, 5),  # T1
            70.2 + np.random.uniform(-3, 3),  # T2
            6.5 + np.random.uniform(-0.5, 0.5),  # P1
            4.2 + np.random.uniform(-0.3, 0.3),  # P2
            15.3 + np.random.uniform(-2, 2),  # V1
            14.8 + np.random.uniform(-2, 2),  # V2
            15.5 + np.random.uniform(-2, 2),  # M1
            15.0 + np.random.uniform(-2, 2),  # M2
            2.5 + np.random.uniform(-0.5, 0.5),  # Q
            25.3,  # d T
            0.5,  # d V
            0.5,  # d M
            0.02,  # Небаланс
            20.0,  # Ти
            -5.0 + np.random.uniform(-3, 3),  # Тост
            5.0,  # Тхв
            "3,8",  # Система сбора данных
        ]
        data_rows.append(row)
    
    # Add summary row to test filtering
    data_rows.append(["Итого за период штатной работы", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    
    # Combine all data
    all_data = metadata + [headers] + data_rows
    
    # Create DataFrame and save
    max_cols = max(len(row) for row in all_data)
    padded_data = [row + [""] * (max_cols - len(row)) for row in all_data]
    
    df = pd.DataFrame(padded_data)
    df.to_excel(output_path, index=False, header=False)
    
    print(f"Test Excel file created: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_excel()
    print("Test file generation complete!")
