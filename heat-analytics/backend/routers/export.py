"""
Router for exporting reports.
"""
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.db import async_session_maker
from backend.models.schemas import Building, DailyReading, AnalysisResult


logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db_session():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


@router.post("/export/pdf")
async def export_pdf_report(
    building_id: int,
    run_id: str = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export PDF report for a building analysis.
    
    Args:
        building_id: Building ID
        run_id: Optional specific run ID (uses latest if not provided)
        db: Database session
    
    Returns:
        PDF file response
    """
    try:
        from weasyprint import HTML, CSS
        from jinja2 import Template
        
        # Get building info
        result = await db.execute(select(Building).where(Building.id == building_id))
        building = result.scalar_one_or_none()
        
        if not building:
            raise HTTPException(status_code=404, detail=f"Building {building_id} not found")
        
        # Get readings
        readings_result = await db.execute(
            select(DailyReading)
            .where(DailyReading.building_id == building_id)
            .order_by(DailyReading.date)
        )
        readings = readings_result.scalars().all()
        
        # Get analysis results
        if run_id:
            analysis_result = await db.execute(
                select(AnalysisResult)
                .where(AnalysisResult.building_id == building_id, AnalysisResult.run_id == run_id)
            )
        else:
            analysis_result = await db.execute(
                select(AnalysisResult)
                .where(AnalysisResult.building_id == building_id)
                .order_by(AnalysisResult.created_at.desc())
            )
        
        analyses = analysis_result.scalars().all()
        
        # Calculate summary statistics
        q_values = [r.q for r in readings if r.q is not None]
        avg_q = sum(q_values) / len(q_values) if q_values else 0
        total_q = sum(q_values)
        
        anomaly_count = sum(1 for a in analyses if a.anomaly_flag)
        
        # Generate HTML report
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Отчёт по анализу теплопотребления</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .info-box { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #bdc3c7; padding: 10px; text-align: left; }
        th { background: #3498db; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .stat-card { background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; font-size: 14px; }
        .anomaly { background: #ffebee !important; }
        footer { margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <h1>🏠 Отчёт по анализу теплопотребления</h1>
    
    <div class="info-box">
        <strong>Здание:</strong> {{ building.address }}<br>
        <strong>Площадь:</strong> {{ building.area_m2 }} м²<br>
        <strong>Год постройки:</strong> {{ building.year_built or 'Н/Д' }}<br>
        <strong>Тип отопления:</strong> {{ building.heating_type }}<br>
        <strong>Дата генерации:</strong> {{ now }}
    </div>
    
    <h2>📊 Сводная статистика</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-value">{{ readings_count }}</div>
            <div class="stat-label">Записей данных</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ "%.2f"|format(avg_q) }}</div>
            <div class="stat-label">Среднее Q (Гкал)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ "%.2f"|format(total_q) }}</div>
            <div class="stat-label">Суммарное Q (Гкал)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ anomaly_count }}</div>
            <div class="stat-label">Аномалий обнаружено</div>
        </div>
    </div>
    
    <h2>📈 Данные измерений (первые 50 записей)</h2>
    <table>
        <thead>
            <tr>
                <th>Дата</th>
                <th>T1 (°C)</th>
                <th>T2 (°C)</th>
                <th>Q (Гкал)</th>
                <th>НС коды</th>
            </tr>
        </thead>
        <tbody>
            {% for reading in readings[:50] %}
            <tr>
                <td>{{ reading.date }}</td>
                <td>{{ reading.t1 or '-' }}</td>
                <td>{{ reading.t2 or '-' }}</td>
                <td>{{ reading.q or '-' }}</td>
                <td>{{ reading.ns_codes or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    {% if analyses %}
    <h2>🔍 Результаты анализа</h2>
    <table>
        <thead>
            <tr>
                <th>Модель</th>
                <th>Прогноз Q</th>
                <th>Остаток</th>
                <th>Score аномалии</th>
                <th>Класс эффективности</th>
            </tr>
        </thead>
        <tbody>
            {% for analysis in analyses[:20] %}
            <tr class="{{ 'anomaly' if analysis.anomaly_flag else '' }}">
                <td>{{ analysis.model_type }}</td>
                <td>{{ analysis.predicted_q or '-' }}</td>
                <td>{{ analysis.residual or '-' }}</td>
                <td>{{ analysis.anomaly_score or '-' }}</td>
                <td>{{ analysis.efficiency_class or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    <footer>
        Система анализа теплопотребления МКД v0.1.0<br>
        Сгенерировано автоматически
    </footer>
</body>
</html>
        """)
        
        html_content = template.render(
            building=building,
            readings=readings,
            analyses=analyses,
            readings_count=len(readings),
            avg_q=avg_q,
            total_q=total_q,
            anomaly_count=anomaly_count,
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        
        # Generate PDF
        output_dir = Path("./data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"report_building_{building_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = output_dir / pdf_filename
        
        html_doc = HTML(string=html_content)
        css = CSS(string='''
            @page { size: A4; margin: 1cm; }
            img { max-width: 100%; }
        ''')
        html_doc.write_pdf(str(pdf_path), stylesheets=[css])
        
        logger.info(f"Generated PDF report: {pdf_path}")
        
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_filename,
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/export/csv/{building_id}")
async def export_csv(
    building_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export building data as CSV.
    
    Args:
        building_id: Building ID
        db: Database session
    
    Returns:
        CSV file response
    """
    import csv
    import io
    
    # Get readings
    result = await db.execute(
        select(DailyReading)
        .where(DailyReading.building_id == building_id)
        .order_by(DailyReading.date)
    )
    readings = result.scalars().all()
    
    if not readings:
        raise HTTPException(status_code=404, detail=f"No data found for building {building_id}")
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = [
        "date", "t1", "t2", "p1", "p2", "v1", "v2", "m1", "m2",
        "q", "dt", "dv", "dm", "imbalance", "ns_codes", "status"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for reading in readings:
        writer.writerow({
            "date": reading.date,
            "t1": reading.t1,
            "t2": reading.t2,
            "p1": reading.p1,
            "p2": reading.p2,
            "v1": reading.v1,
            "v2": reading.v2,
            "m1": reading.m1,
            "m2": reading.m2,
            "q": reading.q,
            "dt": reading.dt,
            "dv": reading.dv,
            "dm": reading.dm,
            "imbalance": reading.imbalance,
            "ns_codes": reading.ns_codes,
            "status": reading.status,
        })
    
    output.seek(0)
    
    # Save to file
    output_dir = Path("./data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_filename = f"data_building_{building_id}.csv"
    csv_path = output_dir / csv_filename
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(output.getvalue())
    
    logger.info(f"Generated CSV export: {csv_path}")
    
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=csv_filename,
    )
