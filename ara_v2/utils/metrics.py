"""
Prometheus metrics for ARA v2.
Tracks application performance and usage metrics.
"""

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge

# Flask metrics (initialized in app factory)
flask_metrics = None

# Custom metrics
papers_ingested = Counter(
    'ara_papers_ingested_total',
    'Total papers ingested',
    ['source']
)

scoring_duration = Histogram(
    'ara_scoring_duration_seconds',
    'Time to score a paper',
    ['score_type']
)

claude_api_calls = Counter(
    'ara_claude_api_calls_total',
    'Claude API calls',
    ['status']
)

claude_api_cost = Counter(
    'ara_claude_api_cost_dollars',
    'Claude API cost in dollars'
)

active_users = Gauge(
    'ara_active_users',
    'Number of active users'
)

pending_evaluations = Gauge(
    'ara_pending_evaluations',
    'Number of papers awaiting Claude evaluation'
)


def init_metrics(app):
    """Initialize Prometheus metrics with Flask app."""
    global flask_metrics

    flask_metrics = PrometheusMetrics(app)
    app.logger.info("Prometheus metrics initialized")

    return flask_metrics


def record_paper_ingestion(source: str):
    """Record paper ingestion from source."""
    papers_ingested.labels(source=source).inc()


def record_claude_call(success: bool, cost: float):
    """Record Claude API call and cost."""
    status = 'success' if success else 'error'
    claude_api_calls.labels(status=status).inc()
    claude_api_cost.inc(cost)


def update_pending_evaluations(count: int):
    """Update pending evaluations gauge."""
    pending_evaluations.set(count)
