# Battery Analyzer v2.0 - Production Architecture Design

## Executive Summary

A complete redesign of the Battery Cycle Analyzer for production deployment, supporting multiple concurrent users, API access, and extensible analysis capabilities. Built with performance, scalability, and maintainability as core principles.

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[React/Vue SPA]
        CLI[CLI Tool]
        API_CLIENT[Python/JS SDK]
    end
    
    subgraph "API Gateway"
        NGINX[Nginx/Traefik]
    end
    
    subgraph "Application Layer"
        FASTAPI[FastAPI Server]
        CELERY[Celery Workers]
        WEBSOCKET[WebSocket Server]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        S3[S3/MinIO Storage]
    end
    
    WEB --> NGINX
    CLI --> NGINX
    API_CLIENT --> NGINX
    NGINX --> FASTAPI
    NGINX --> WEBSOCKET
    FASTAPI --> CELERY
    FASTAPI --> POSTGRES
    FASTAPI --> REDIS
    CELERY --> S3
    CELERY --> POSTGRES
```

## Tech Stack

### Backend Core
```yaml
Language: Python 3.11+
Framework: FastAPI
Data Processing: Polars + NumPy
Task Queue: Celery + Redis
Database: PostgreSQL + TimescaleDB extension
Object Storage: MinIO (S3-compatible)
Cache: Redis
Container: Docker + Kubernetes
```

### Frontend
```yaml
Framework: Vue 3 + TypeScript (or React 18)
UI Components: PrimeVue or Ant Design
Charts: Plotly.js + D3.js
State Management: Pinia (Vue) or Zustand (React)
Build Tool: Vite
```

### DevOps & Monitoring
```yaml
Containerization: Docker
Orchestration: Kubernetes (K8s) or Docker Swarm
CI/CD: GitHub Actions / GitLab CI
Monitoring: Prometheus + Grafana
Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
Tracing: OpenTelemetry + Jaeger
```

## Project Structure

```
battery-analyzer-v2/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── dependencies.py         # Dependency injection
│   │   ├── middleware.py           # Auth, CORS, rate limiting
│   │   └── routers/
│   │       ├── auth.py            # Authentication endpoints
│   │       ├── analysis.py        # Analysis endpoints
│   │       ├── files.py           # File upload/download
│   │       ├── results.py         # Results retrieval
│   │       └── websocket.py       # Real-time updates
│   │
│   ├── core/
│   │   ├── config.py              # Pydantic settings
│   │   ├── security.py            # Auth/encryption utilities
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── constants.py           # App constants
│   │
│   ├── models/
│   │   ├── database.py            # SQLAlchemy models
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── enums.py               # Enum definitions
│   │
│   ├── services/
│   │   ├── analysis/
│   │   │   ├── base.py            # Abstract analysis class
│   │   │   ├── cycle_analyzer.py  # Standard cycle analysis
│   │   │   ├── dqdu_analyzer.py   # dQ/dU analysis
│   │   │   ├── eis_analyzer.py    # EIS analysis
│   │   │   └── plugins/           # Plugin system
│   │   ├── data_processing/
│   │   │   ├── loader.py          # File parsing
│   │   │   ├── validator.py       # Data validation
│   │   │   ├── transformer.py     # Data transformation
│   │   │   └── cache.py           # Caching layer
│   │   ├── storage.py             # S3/MinIO interface
│   │   └── notification.py        # Email/webhook notifications
│   │
│   ├── workers/
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── tasks/
│   │   │   ├── analysis.py        # Long-running analysis
│   │   │   ├── export.py          # Export generation
│   │   │   └── cleanup.py         # Maintenance tasks
│   │   └── beat_schedule.py       # Periodic tasks
│   │
│   ├── database/
│   │   ├── migrations/            # Alembic migrations
│   │   └── seeds/                 # Sample data
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── fixtures/
│       └── conftest.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── analysis/
│   │   │   ├── charts/
│   │   │   ├── common/
│   │   │   └── layout/
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Analysis.vue
│   │   │   ├── Results.vue
│   │   │   └── Settings.vue
│   │   ├── stores/               # State management
│   │   ├── services/             # API clients
│   │   ├── utils/
│   │   └── types/                # TypeScript types
│   ├── public/
│   └── package.json
│
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.worker
│   ├── kubernetes/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── configmaps/
│   │   └── secrets/
│   ├── terraform/                # Infrastructure as Code
│   └── scripts/
│       ├── deploy.sh
│       └── backup.sh
│
├── docs/
│   ├── api/                      # OpenAPI/Swagger
│   ├── architecture/
│   └── user-guide/
│
├── docker-compose.yml             # Local development
├── docker-compose.prod.yml        # Production stack
├── .env.example
├── pyproject.toml                 # Python dependencies
└── README.md
```

## Core Components Design

### 1. Data Models (Pydantic + SQLAlchemy)

```python
# models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    STANDARD_CYCLE = "standard_cycle"
    DQ_DU = "dq_du"
    EIS = "eis"
    RATE_CAPABILITY = "rate_capability"
    CALENDAR_AGING = "calendar_aging"

class FileUpload(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    
    @validator('size_bytes')
    def validate_size(cls, v):
        max_size = 500 * 1024 * 1024  # 500MB
        if v > max_size:
            raise ValueError(f"File too large: {v/1024/1024:.1f}MB (max: {max_size/1024/1024}MB)")
        return v

class BatteryMetadata(BaseModel):
    test_name: str
    battery_id: str
    active_material_mass_g: float = Field(..., gt=0)
    theoretical_capacity_ah: float = Field(..., gt=0)
    electrode_area_cm2: Optional[float] = Field(None, gt=0)
    temperature_c: Optional[float] = None
    test_date: datetime
    operator: Optional[str] = None
    notes: Optional[str] = None

class CycleData(BaseModel):
    cycle_number: int
    half_cycle_type: str  # "charge" or "discharge"
    capacity_ah: float
    specific_capacity_mah_g: float
    coulombic_efficiency: Optional[float]
    energy_wh: float
    avg_voltage_v: float
    duration_h: float
    c_rate: float
    
    class Config:
        orm_mode = True

class AnalysisRequest(BaseModel):
    file_id: str
    analysis_type: AnalysisType
    parameters: Dict[str, Any]
    metadata: BatteryMetadata
    user_id: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)

class AnalysisResult(BaseModel):
    id: str
    request_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = Field(0.0, ge=0.0, le=100.0)
    cycles: List[CycleData]
    summary_stats: Dict[str, Any]
    plots: List[Dict[str, Any]]  # Plot configurations for frontend
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
```

### 2. Database Schema (PostgreSQL + TimescaleDB)

```sql
-- Enable TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Users and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Projects/Experiments
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- File uploads
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- S3/MinIO path
    size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    content_type VARCHAR(100),
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis jobs
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    priority INTEGER DEFAULT 5,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    celery_task_id VARCHAR(255)
);

-- Battery metadata
CREATE TABLE battery_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    test_name VARCHAR(255),
    battery_id VARCHAR(255),
    active_material_mass_g FLOAT,
    theoretical_capacity_ah FLOAT,
    electrode_area_cm2 FLOAT,
    temperature_c FLOAT,
    test_date DATE,
    operator VARCHAR(255),
    notes TEXT,
    raw_metadata JSONB  -- Store all parsed metadata
);

-- Cycle data (time-series)
CREATE TABLE cycle_data (
    time TIMESTAMPTZ NOT NULL,
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    cycle_number INTEGER NOT NULL,
    half_cycle_type VARCHAR(10) NOT NULL,
    capacity_ah FLOAT NOT NULL,
    specific_capacity_mah_g FLOAT NOT NULL,
    coulombic_efficiency FLOAT,
    energy_wh FLOAT,
    avg_voltage_v FLOAT,
    min_voltage_v FLOAT,
    max_voltage_v FLOAT,
    duration_h FLOAT,
    c_rate FLOAT,
    temperature_c FLOAT,
    internal_resistance_ohm FLOAT
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('cycle_data', 'time');

-- Create indexes
CREATE INDEX idx_cycle_data_job_id ON cycle_data(job_id);
CREATE INDEX idx_cycle_data_cycle_number ON cycle_data(cycle_number);

-- dQ/dU analysis results
CREATE TABLE dqdu_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    cycle_number INTEGER NOT NULL,
    voltage_array FLOAT[],
    dqdu_array FLOAT[],
    peaks JSONB,  -- [{voltage: x, intensity: y, width: z}, ...]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis cache for expensive computations
CREATE TABLE analysis_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Create cleanup function for expired cache
CREATE OR REPLACE FUNCTION cleanup_expired_cache() RETURNS void AS $$
BEGIN
    DELETE FROM analysis_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

### 3. API Design (FastAPI)

```python
# api/main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from typing import List, Optional

app = FastAPI(
    title="Battery Analyzer API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# api/routers/analysis.py
from fastapi import APIRouter, BackgroundTasks, WebSocket
from services.analysis import AnalysisService
from workers.tasks import process_analysis

router = APIRouter(prefix="/api/v2/analysis", tags=["analysis"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = None,
    current_user = Depends(get_current_user)
):
    """Upload battery test data file."""
    # Validate file
    if not file.filename.endswith(('.txt', '.csv', '.xlsx')):
        raise HTTPException(400, "Invalid file format")
    
    # Stream to S3/MinIO
    file_id = await storage_service.upload_file(file, current_user.id)
    
    # Parse metadata in background
    background_tasks.add_task(parse_file_metadata, file_id)
    
    return {"file_id": file_id, "status": "uploaded"}

@router.post("/start")
async def start_analysis(request: AnalysisRequest, current_user = Depends(get_current_user)):
    """Start battery data analysis."""
    # Create job record
    job = await analysis_service.create_job(request, current_user.id)
    
    # Queue async task
    task = process_analysis.delay(job.id, request.dict())
    
    # Update job with Celery task ID
    await analysis_service.update_job(job.id, {"celery_task_id": task.id})
    
    return {
        "job_id": job.id,
        "status": "queued",
        "estimated_time_seconds": estimate_processing_time(request)
    }

@router.get("/status/{job_id}")
async def get_analysis_status(job_id: str, current_user = Depends(get_current_user)):
    """Get analysis job status."""
    job = await analysis_service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message
    }

@router.get("/results/{job_id}")
async def get_results(
    job_id: str,
    format: str = "json",
    current_user = Depends(get_current_user)
):
    """Get analysis results."""
    results = await analysis_service.get_results(job_id, current_user.id)
    
    if format == "csv":
        csv_data = export_service.to_csv(results)
        return StreamingResponse(
            io.BytesIO(csv_data.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=results_{job_id}.csv"}
        )
    elif format == "excel":
        excel_data = export_service.to_excel(results)
        return StreamingResponse(
            excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=results_{job_id}.xlsx"}
        )
    
    return results

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time progress updates."""
    await websocket.accept()
    
    try:
        while True:
            # Get job status from Redis
            status = await redis_client.get(f"job:{job_id}:status")
            progress = await redis_client.get(f"job:{job_id}:progress")
            
            await websocket.send_json({
                "type": "progress",
                "job_id": job_id,
                "status": status,
                "progress": float(progress or 0)
            })
            
            if status in ["completed", "failed"]:
                break
                
            await asyncio.sleep(1)  # Poll every second
            
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()

@router.post("/batch")
async def batch_analysis(
    files: List[UploadFile],
    analysis_type: AnalysisType,
    parameters: dict,
    current_user = Depends(get_current_user)
):
    """Process multiple files in batch."""
    jobs = []
    
    for file in files:
        file_id = await storage_service.upload_file(file, current_user.id)
        job = await analysis_service.create_job(
            AnalysisRequest(
                file_id=file_id,
                analysis_type=analysis_type,
                parameters=parameters
            ),
            current_user.id
        )
        process_analysis.delay(job.id)
        jobs.append(job.id)
    
    return {"jobs": jobs, "count": len(jobs)}
```

### 4. Analysis Engine (Plugin Architecture)

```python
# services/analysis/base.py
from abc import ABC, abstractmethod
import polars as pl
from typing import Dict, Any, Optional

class AnalysisPlugin(ABC):
    """Base class for all analysis plugins."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.progress = 0.0
        
    @abstractmethod
    def validate_data(self, df: pl.DataFrame) -> bool:
        """Validate that data has required columns."""
        pass
    
    @abstractmethod
    def preprocess(self, df: pl.DataFrame) -> pl.DataFrame:
        """Preprocess data before analysis."""
        pass
    
    @abstractmethod
    def analyze(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Perform the analysis."""
        pass
    
    @abstractmethod
    def generate_plots(self, results: Dict[str, Any]) -> List[Dict]:
        """Generate plot configurations."""
        pass
    
    def update_progress(self, value: float):
        """Update progress for real-time tracking."""
        self.progress = value
        # Publish to Redis for WebSocket updates
        redis_client.set(f"job:{self.job_id}:progress", value)

# services/analysis/dqdu_analyzer.py
import numpy as np
from scipy import interpolate, signal
from typing import Tuple, List

class DQDUAnalyzer(AnalysisPlugin):
    """Differential capacity (dQ/dU) analysis plugin."""
    
    def validate_data(self, df: pl.DataFrame) -> bool:
        required_cols = ['Time[h]', 'U[V]', 'I[A]', 'Command']
        return all(col in df.columns for col in required_cols)
    
    def preprocess(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filter and prepare data for dQ/dU analysis."""
        # Filter to charge/discharge only
        df_filtered = df.filter(
            pl.col('Command').str.to_lowercase().is_in(['charge', 'discharge'])
        )
        
        # Calculate cumulative capacity
        df_filtered = df_filtered.with_columns([
            (pl.col('I[A]').abs() * pl.col('Time[h]').diff().fill_null(0))
            .cumsum()
            .alias('Capacity_Ah')
        ])
        
        return df_filtered
    
    def analyze(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Perform dQ/dU analysis."""
        results = {}
        
        # Get cycle selections from config
        cycles_to_analyze = self.config.get('cycles', [1, 50, 100, 500, 1000])
        half_cycle_type = self.config.get('half_cycle_type', 'discharge')
        
        for cycle_num in cycles_to_analyze:
            self.update_progress(cycle_num / len(cycles_to_analyze) * 100)
            
            # Extract cycle data
            cycle_data = self._extract_cycle(df, cycle_num, half_cycle_type)
            if cycle_data is None:
                continue
            
            # Calculate dQ/dU
            voltage, dqdu = self._calculate_dqdu(
                cycle_data['U[V]'].to_numpy(),
                cycle_data['Capacity_Ah'].to_numpy()
            )
            
            # Detect peaks
            peaks = self._detect_peaks(voltage, dqdu)
            
            results[f'cycle_{cycle_num}'] = {
                'voltage': voltage.tolist(),
                'dqdu': dqdu.tolist(),
                'peaks': peaks,
                'metadata': {
                    'cycle_number': cycle_num,
                    'half_cycle_type': half_cycle_type
                }
            }
        
        return results
    
    def _extract_cycle(self, df: pl.DataFrame, cycle_num: int, half_cycle_type: str):
        """Extract specific cycle data."""
        # Implementation here
        pass
    
    def _calculate_dqdu(
        self, 
        voltage: np.ndarray, 
        capacity: np.ndarray,
        n_points: int = 333
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate differential capacity."""
        # Remove duplicates and sort
        unique_idx = np.unique(voltage, return_index=True)[1]
        voltage = voltage[unique_idx]
        capacity = capacity[unique_idx]
        
        # Interpolate to uniform grid
        v_min, v_max = voltage.min(), voltage.max()
        v_uniform = np.linspace(v_min, v_max, n_points)
        
        # Use cubic spline interpolation
        cs = interpolate.CubicSpline(voltage, capacity, extrapolate=False)
        q_uniform = cs(v_uniform)
        
        # Calculate derivative (dQ/dV)
        dq_dv = np.gradient(q_uniform, v_uniform)
        
        # Convert to dQ/dU (same as dQ/dV for voltage)
        dq_du = dq_dv * 1000  # Convert to mAh/V
        
        # Apply smoothing if configured
        if self.config.get('smoothing', 'savgol') == 'savgol':
            window = self.config.get('smoothing_window', 11)
            poly = self.config.get('smoothing_poly', 3)
            dq_du = signal.savgol_filter(dq_du, window, poly)
        
        return v_uniform, dq_du
    
    def _detect_peaks(
        self, 
        voltage: np.ndarray, 
        dqdu: np.ndarray,
        prominence: float = 0.1
    ) -> List[Dict]:
        """Detect peaks in dQ/dU curve."""
        # Find peaks
        peaks, properties = signal.find_peaks(
            dqdu,
            prominence=prominence * np.max(dqdu),
            width=3
        )
        
        peak_data = []
        for idx in peaks:
            peak_data.append({
                'voltage': float(voltage[idx]),
                'intensity': float(dqdu[idx]),
                'width': float(properties['widths'][len(peak_data)] if 'widths' in properties else 0),
                'prominence': float(properties['prominences'][len(peak_data)])
            })
        
        return peak_data
    
    def generate_plots(self, results: Dict[str, Any]) -> List[Dict]:
        """Generate Plotly plot configurations."""
        plots = []
        
        # Multi-cycle dQ/dU comparison plot
        traces = []
        for cycle_key, cycle_data in results.items():
            if not isinstance(cycle_data, dict):
                continue
                
            traces.append({
                'type': 'scatter',
                'x': cycle_data['voltage'],
                'y': cycle_data['dqdu'],
                'name': f"Cycle {cycle_data['metadata']['cycle_number']}",
                'mode': 'lines'
            })
            
            # Add peak markers
            if cycle_data.get('peaks'):
                peak_x = [p['voltage'] for p in cycle_data['peaks']]
                peak_y = [p['intensity'] for p in cycle_data['peaks']]
                traces.append({
                    'type': 'scatter',
                    'x': peak_x,
                    'y': peak_y,
                    'mode': 'markers',
                    'marker': {'size': 10, 'color': 'red'},
                    'name': f"Peaks - Cycle {cycle_data['metadata']['cycle_number']}",
                    'showlegend': False
                })
        
        plots.append({
            'id': 'dqdu_comparison',
            'type': 'plotly',
            'data': traces,
            'layout': {
                'title': 'dQ/dU Analysis - Cycle Comparison',
                'xaxis': {'title': 'Voltage (V)'},
                'yaxis': {'title': 'Differential Capacity (mAh/V)'},
                'height': 500
            }
        })
        
        # Peak evolution plot
        peak_evolution = self._analyze_peak_evolution(results)
        if peak_evolution:
            plots.append({
                'id': 'peak_evolution',
                'type': 'plotly',
                'data': peak_evolution['traces'],
                'layout': {
                    'title': 'Peak Evolution Across Cycles',
                    'xaxis': {'title': 'Cycle Number'},
                    'yaxis': {'title': 'Peak Voltage (V)'},
                    'height': 400
                }
            })
        
        return plots
```

### 5. Worker Tasks (Celery)

```python
# workers/celery_app.py
from celery import Celery
from kombu import Queue

celery_app = Celery(
    'battery_analyzer',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1',
    include=['workers.tasks.analysis']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'workers.tasks.analysis.*': {'queue': 'analysis'},
        'workers.tasks.export.*': {'queue': 'export'},
        'workers.tasks.cleanup.*': {'queue': 'maintenance'}
    },
    task_queues=(
        Queue('analysis', priority=10),
        Queue('export', priority=5),
        Queue('maintenance', priority=1),
    ),
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# workers/tasks/analysis.py
from celery import Task
import polars as pl
from typing import Dict, Any

class AnalysisTask(Task):
    """Base task with progress tracking."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = args[0]
        # Update job status in database
        update_job_status(job_id, 'failed', error_message=str(exc))
        # Notify user via email/webhook
        notify_failure(job_id, str(exc))

@celery_app.task(bind=True, base=AnalysisTask, name='process_analysis')
def process_analysis(self, job_id: str, request_data: Dict[str, Any]):
    """Process battery analysis job."""
    try:
        # Update status
        update_job_status(job_id, 'processing')
        
        # Load data from S3/MinIO
        file_path = get_file_path(request_data['file_id'])
        df = load_battery_data(file_path)
        
        # Get appropriate analyzer
        analyzer_class = get_analyzer_class(request_data['analysis_type'])
        analyzer = analyzer_class(request_data['parameters'])
        analyzer.job_id = job_id
        
        # Validate data
        if not analyzer.validate_data(df):
            raise ValueError("Invalid data format for selected analysis")
        
        # Preprocess
        self.update_state(state='PROGRESS', meta={'progress': 20})
        df_processed = analyzer.preprocess(df)
        
        # Run analysis
        self.update_state(state='PROGRESS', meta={'progress': 50})
        results = analyzer.analyze(df_processed)
        
        # Generate plots
        self.update_state(state='PROGRESS', meta={'progress': 80})
        plots = analyzer.generate_plots(results)
        
        # Save results to database
        save_results(job_id, results, plots)
        
        # Update job status
        update_job_status(job_id, 'completed')
        
        # Send notification
        notify_completion(job_id)
        
        return {'job_id': job_id, 'status': 'completed'}
        
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(name='export_results')
def export_results(job_id: str, format: str = 'excel'):
    """Export analysis results to various formats."""
    results = get_results_from_db(job_id)
    
    if format == 'excel':
        file_path = export_to_excel(results)
    elif format == 'origin':
        file_path = export_to_origin_format(results)
    elif format == 'matlab':
        file_path = export_to_matlab(results)
    else:
        raise ValueError(f"Unsupported export format: {format}")
    
    # Upload to S3 and generate presigned URL
    download_url = upload_export(file_path)
    
    return {'download_url': download_url, 'expires_in': 3600}
```

### 6. Frontend Architecture (Vue 3 + TypeScript)

```typescript
// frontend/src/types/analysis.ts
export interface AnalysisRequest {
  fileId: string;
  analysisType: 'standard_cycle' | 'dq_du' | 'eis';
  parameters: Record<string, any>;
  metadata: BatteryMetadata;
}

export interface BatteryMetadata {
  testName: string;
  batteryId: string;
  activeMaterialMassG: number;
  theoreticalCapacityAh: number;
  electrodeAreaCm2?: number;
  temperatureC?: number;
}

export interface AnalysisJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  createdAt: Date;
  completedAt?: Date;
  errorMessage?: string;
}

// frontend/src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v2',
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`;
  }
  return config;
});

export class AnalysisService {
  async uploadFile(file: File, projectId?: string): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) formData.append('project_id', projectId);
    
    const response = await api.post('/analysis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const progress = (progressEvent.loaded / progressEvent.total!) * 100;
        // Update progress in store
      },
    });
    
    return response.data.file_id;
  }
  
  async startAnalysis(request: AnalysisRequest): Promise<AnalysisJob> {
    const response = await api.post('/analysis/start', request);
    return response.data;
  }
  
  async getStatus(jobId: string): Promise<AnalysisJob> {
    const response = await api.get(`/analysis/status/${jobId}`);
    return response.data;
  }
  
  connectWebSocket(jobId: string, onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/api/v2/analysis/ws/${jobId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    return ws;
  }
}

// frontend/src/components/analysis/DQDUAnalysis.vue
<template>
  <div class="dqdu-analysis">
    <div class="configuration">
      <h3>dQ/dU Analysis Configuration</h3>
      
      <div class="form-group">
        <label>Select Cycles</label>
        <MultiSelect 
          v-model="selectedCycles" 
          :options="availableCycles"
          placeholder="Select cycles to analyze"
        />
      </div>
      
      <div class="form-group">
        <label>Half-Cycle Type</label>
        <RadioGroup v-model="halfCycleType">
          <Radio value="discharge">Discharge</Radio>
          <Radio value="charge">Charge</Radio>
        </RadioGroup>
      </div>
      
      <div class="form-group">
        <label>Interpolation Points</label>
        <Slider 
          v-model="interpolationPoints" 
          :min="100" 
          :max="1000" 
          :step="10"
        />
        <span>{{ interpolationPoints }} points</span>
      </div>
      
      <div class="form-group">
        <label>Smoothing</label>
        <Select v-model="smoothingMethod">
          <option value="none">None</option>
          <option value="savgol">Savitzky-Golay</option>
          <option value="moving_avg">Moving Average</option>
        </Select>
      </div>
      
      <Button 
        @click="startAnalysis" 
        :loading="isProcessing"
        type="primary"
      >
        Start Analysis
      </Button>
    </div>
    
    <div class="results" v-if="results">
      <h3>Analysis Results</h3>
      
      <div class="plot-container">
        <PlotlyChart 
          :data="plotData" 
          :layout="plotLayout"
          :config="plotConfig"
        />
      </div>
      
      <div class="peak-table" v-if="peaks.length">
        <h4>Detected Peaks</h4>
        <DataTable :data="peaks" :columns="peakColumns" />
      </div>
      
      <div class="export-options">
        <Button @click="exportData('csv')">Export CSV</Button>
        <Button @click="exportData('excel')">Export Excel</Button>
        <Button @click="exportData('origin')">Export for Origin</Button>
      </div>
    </div>
    
    <ProgressModal 
      v-if="showProgress" 
      :progress="currentProgress"
      :status="jobStatus"
      @cancel="cancelAnalysis"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import { AnalysisService } from '@/services/api';

const analysisStore = useAnalysisStore();
const analysisService = new AnalysisService();

const selectedCycles = ref<number[]>([1, 50, 100, 500, 1000]);
const halfCycleType = ref<'charge' | 'discharge'>('discharge');
const interpolationPoints = ref(333);
const smoothingMethod = ref('savgol');

const isProcessing = ref(false);
const currentProgress = ref(0);
const jobStatus = ref('');
const results = ref(null);
const ws = ref<WebSocket | null>(null);

async function startAnalysis() {
  isProcessing.value = true;
  
  const request = {
    fileId: analysisStore.currentFileId,
    analysisType: 'dq_du',
    parameters: {
      cycles: selectedCycles.value,
      half_cycle_type: halfCycleType.value,
      n_points: interpolationPoints.value,
      smoothing: smoothingMethod.value,
    },
    metadata: analysisStore.metadata,
  };
  
  try {
    const job = await analysisService.startAnalysis(request);
    
    // Connect WebSocket for progress updates
    ws.value = analysisService.connectWebSocket(job.id, (data) => {
      if (data.type === 'progress') {
        currentProgress.value = data.progress;
        jobStatus.value = data.status;
      } else if (data.type === 'completed') {
        loadResults(job.id);
      }
    });
    
  } catch (error) {
    console.error('Analysis failed:', error);
    isProcessing.value = false;
  }
}

onUnmounted(() => {
  if (ws.value) {
    ws.value.close();
  }
});
</script>
```

## Deployment Configuration

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.9'

services:
  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_USER: battery_analyzer
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: battery_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  backend:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://battery_analyzer:secure_password@postgres:5432/battery_db
      REDIS_URL: redis://redis:6379
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio
    command: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

  celery_worker:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://battery_analyzer:secure_password@postgres:5432/battery_db
      REDIS_URL: redis://redis:6379
      MINIO_ENDPOINT: minio:9000
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
      - minio
    command: celery -A workers.celery_app worker --loglevel=info -Q analysis,export,maintenance

  celery_beat:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://battery_analyzer:secure_password@postgres:5432/battery_db
      REDIS_URL: redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    command: celery -A workers.celery_app beat --loglevel=info

  frontend:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000/api/v2
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### Kubernetes Deployment (Production)

```yaml
# infrastructure/kubernetes/deployments/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: battery-analyzer-backend
  namespace: battery-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: battery-analyzer-backend
  template:
    metadata:
      labels:
        app: battery-analyzer-backend
    spec:
      containers:
      - name: backend
        image: battery-analyzer/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: battery-analyzer-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: battery-analyzer-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: battery-analyzer-backend
  namespace: battery-analyzer
spec:
  selector:
    app: battery-analyzer-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: battery-analyzer-backend-hpa
  namespace: battery-analyzer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: battery-analyzer-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Performance Optimizations

### 1. Data Processing

```python
# Use Polars for 10-50x faster processing
import polars as pl

def process_large_file(file_path: str):
    # Lazy evaluation - doesn't load until needed
    lazy_df = pl.scan_csv(file_path)
    
    # Chain operations efficiently
    result = (
        lazy_df
        .filter(pl.col('Command').is_in(['charge', 'discharge']))
        .groupby('CycleNumber')
        .agg([
            pl.col('Capacity_Ah').mean().alias('avg_capacity'),
            pl.col('U[V]').max().alias('max_voltage'),
            pl.col('Duration_h').sum().alias('total_duration')
        ])
        .sort('CycleNumber')
        .collect()  # Execute the query
    )
    
    return result
```

### 2. Caching Strategy

```python
from functools import lru_cache
import hashlib
import pickle

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def cache_key(self, *args, **kwargs):
        """Generate cache key from arguments."""
        key_data = pickle.dumps((args, kwargs))
        return hashlib.sha256(key_data).hexdigest()
    
    async def get_or_compute(self, key: str, compute_func, ttl: int = 3600):
        """Get from cache or compute and store."""
        # Check cache
        cached = await self.redis.get(key)
        if cached:
            return pickle.loads(cached)
        
        # Compute
        result = await compute_func()
        
        # Store in cache
        await self.redis.setex(key, ttl, pickle.dumps(result))
        
        return result
```

### 3. Database Optimization

```sql
-- Partitioning for time-series data
CREATE TABLE cycle_data_2024_q1 PARTITION OF cycle_data
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE cycle_data_2024_q2 PARTITION OF cycle_data
FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Indexes for common queries
CREATE INDEX CONCURRENTLY idx_cycle_data_job_cycle 
ON cycle_data(job_id, cycle_number);

CREATE INDEX CONCURRENTLY idx_analysis_jobs_user_status 
ON analysis_jobs(created_by, status)
WHERE status IN ('pending', 'processing');

-- Materialized view for dashboard stats
CREATE MATERIALIZED VIEW user_statistics AS
SELECT 
    u.id as user_id,
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT f.id) as total_files,
    COUNT(DISTINCT aj.id) as total_analyses,
    SUM(f.size_bytes) / 1024 / 1024 as total_storage_mb,
    MAX(aj.created_at) as last_analysis_date
FROM users u
LEFT JOIN projects p ON u.id = p.user_id
LEFT JOIN files f ON p.id = f.project_id
LEFT JOIN analysis_jobs aj ON f.id = aj.file_id
GROUP BY u.id;

-- Refresh materialized view periodically
CREATE OR REPLACE FUNCTION refresh_user_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
END;
$$ LANGUAGE plpgsql;
```

## Security Considerations

### 1. Authentication & Authorization

```python
# backend/core/security.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    @staticmethod
    def create_access_token(user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)
    
    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
        token = credentials.credentials
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return await get_user_by_id(user_id)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

@router.post("/analysis/start")
@limiter.limit("10 per minute")
async def start_analysis(request: AnalysisRequest):
    # Implementation
    pass
```

### 3. Input Validation & Sanitization

```python
from pydantic import validator
import magic

class FileUploadValidator:
    ALLOWED_MIME_TYPES = [
        'text/plain',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    @staticmethod
    async def validate_file(file: UploadFile):
        # Check file size
        if file.size > FileUploadValidator.MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")
        
        # Check MIME type
        file_bytes = await file.read(2048)
        await file.seek(0)
        
        mime = magic.from_buffer(file_bytes, mime=True)
        if mime not in FileUploadValidator.ALLOWED_MIME_TYPES:
            raise HTTPException(400, f"Invalid file type: {mime}")
        
        # Check for malicious content
        if b'<script' in file_bytes or b'javascript:' in file_bytes:
            raise HTTPException(400, "Potentially malicious content detected")
        
        return True
```

## Monitoring & Observability

### 1. Application Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
analysis_counter = Counter('analysis_requests_total', 'Total analysis requests', ['analysis_type', 'status'])
analysis_duration = Histogram('analysis_duration_seconds', 'Analysis duration', ['analysis_type'])
active_jobs = Gauge('active_analysis_jobs', 'Currently active analysis jobs')

# Use in code
@router.post("/analysis/start")
async def start_analysis(request: AnalysisRequest):
    start_time = time.time()
    
    try:
        # Process request
        result = await process_analysis(request)
        analysis_counter.labels(analysis_type=request.analysis_type, status='success').inc()
        return result
    except Exception as e:
        analysis_counter.labels(analysis_type=request.analysis_type, status='error').inc()
        raise
    finally:
        analysis_duration.labels(analysis_type=request.analysis_type).observe(time.time() - start_time)
```

### 2. Logging Configuration

```python
import structlog
from pythonjsonlogger import jsonlogger

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

# Usage
logger.info("analysis_started", 
    job_id=job_id, 
    user_id=user_id,
    analysis_type=analysis_type,
    file_size_mb=file_size/1024/1024
)
```

## Cost Optimization

### 1. Resource Allocation

```yaml
# Optimize pod resources based on actual usage
resources:
  requests:
    memory: "256Mi"  # Start small
    cpu: "100m"
  limits:
    memory: "2Gi"    # Allow bursts
    cpu: "2000m"
```

### 2. Storage Tiering

```python
class StorageService:
    """Implement storage tiering for cost optimization."""
    
    async def archive_old_results(self, days_old: int = 30):
        """Move old results to cheaper storage."""
        old_results = await get_results_older_than(days_old)
        
        for result in old_results:
            # Move to Glacier/Cold storage
            await s3_client.copy_object(
                CopySource={'Bucket': 'hot-storage', 'Key': result.key},
                Bucket='cold-storage',
                Key=result.key,
                StorageClass='GLACIER'
            )
            
            # Update database reference
            await update_storage_location(result.id, 'cold-storage')
            
            # Delete from hot storage
            await s3_client.delete_object(Bucket='hot-storage', Key=result.key)
```

## Development Workflow

### 1. Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/battery-analyzer-v2.git
cd battery-analyzer-v2

# Setup Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt

# Setup Node environment
cd frontend
npm install

# Start services with Docker Compose
cd ..
docker-compose up -d postgres redis minio

# Run database migrations
alembic upgrade head

# Start backend in development mode
uvicorn backend.api.main:app --reload

# Start frontend in another terminal
cd frontend
npm run dev

# Start Celery worker in another terminal
celery -A backend.workers.celery_app worker --loglevel=info
```

### 2. Testing Strategy

```python
# backend/tests/test_dqdu_analysis.py
import pytest
from services.analysis.dqdu_analyzer import DQDUAnalyzer
import polars as pl
import numpy as np

class TestDQDUAnalyzer:
    @pytest.fixture
    def sample_data(self):
        """Generate sample battery data."""
        return pl.DataFrame({
            'Time[h]': np.linspace(0, 10, 1000),
            'U[V]': np.linspace(3.0, 4.2, 1000),
            'I[A]': np.ones(1000) * 0.1,
            'Command': ['discharge'] * 1000
        })
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DQDUAnalyzer({'cycles': [1], 'n_points': 100})
    
    def test_calculate_dqdu(self, analyzer, sample_data):
        """Test dQ/dU calculation."""
        voltage = sample_data['U[V]'].to_numpy()
        capacity = np.cumsum(sample_data['I[A]'].to_numpy() * 0.01)  # Simple integration
        
        v_uniform, dqdu = analyzer._calculate_dqdu(voltage, capacity)
        
        assert len(v_uniform) == 100  # Check interpolation
        assert v_uniform.min() >= 3.0
        assert v_uniform.max() <= 4.2
        assert not np.any(np.isnan(dqdu))  # No NaN values
    
    @pytest.mark.integration
    async def test_full_analysis_pipeline(self, analyzer, sample_data):
        """Test complete analysis pipeline."""
        results = analyzer.analyze(sample_data)
        
        assert 'cycle_1' in results
        assert 'voltage' in results['cycle_1']
        assert 'dqdu' in results['cycle_1']
        assert len(results['cycle_1']['voltage']) == 100
```

## Future Enhancements

### Phase 2 Features
1. **Machine Learning Integration**
   - Automatic degradation mechanism identification
   - Remaining useful life prediction
   - Anomaly detection in cycling data

2. **Advanced Visualizations**
   - 3D surface plots for multi-parameter analysis
   - Interactive dashboards with drill-down capabilities
   - Real-time streaming data visualization

3. **Collaboration Features**
   - Shared projects and teams
   - Comments and annotations on results
   - Version control for analysis parameters

4. **Integration Capabilities**
   - REST API for third-party tools
   - Python SDK for programmatic access
   - Jupyter notebook integration
   - MATLAB/Origin export formats

5. **Performance Enhancements**
   - GPU acceleration for large datasets
   - Distributed computing with Dask/Ray
   - Edge caching with CDN

## Conclusion

This v2 architecture provides:

✅ **Scalability**: Handle 100+ concurrent users and TB of data  
✅ **Performance**: 10-50x faster processing with Polars  
✅ **Reliability**: Fault-tolerant with retry mechanisms  
✅ **Extensibility**: Plugin architecture for new analyses  
✅ **Security**: Enterprise-grade authentication and authorization  
✅ **Observability**: Complete monitoring and logging  
✅ **User Experience**: Real-time progress updates and modern UI  

The architecture is designed to grow from a small deployment (3-5 users) to enterprise scale (1000+ users) without major refactoring.