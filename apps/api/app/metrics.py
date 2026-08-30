from prometheus_client import Counter, Histogram

EVENTS_PROCESSED = Counter(
    'events_processed_total',
    'Total number of events ingested',
    ['organization_id', 'status']
)

CASES_CREATED = Counter(
    'cases_created_total',
    'Total number of risk cases created',
    ['organization_id']
)

INVESTIGATIONS_STARTED = Counter(
    'investigations_started_total',
    'Total number of investigations started',
    ['worker_id']
)

SLA_BREACHES = Counter(
    'sla_breaches_total',
    'Total number of SLA breaches',
    ['organization_id']
)

INVESTIGATION_LATENCY = Histogram(
    'investigation_latency_seconds',
    'Time taken to complete an investigation',
    ['worker_id']
)
