# 1.3 Infrastructure Planning - MCP-BD Explorer

## Tech Stack Decision Matrix

### Storage Layer

| Component | Choice | Rationale | Alternatives Considered |
|-----------|--------|-----------|--------------------------|
| **Primary Database** | PostgreSQL | Relational data model for domains/categories, strong consistency, ACID compliance, mature ecosystem | Firebase (no migration path), MongoDB (overkill) |
| **Search Index** | Elasticsearch | Full-text search for crawled content, faceted search, aggregations for analytics | Meilisearch (limited features), Algolia (SaaS costs) |
| **Caching Layer** | Redis | Session management, crawl job queue, rate limiting, real-time analytics | Memcached (no persistence), In-memory only |
| **File Storage** | Object Storage (S3/R2) | Store crawled HTML/JSON content, screenshots, logs | Database BLOB (performance impact), Local disk (not scalable) |

**Decision Rationale:**
- PostgreSQL handles relational data (domains → crawl logs → categories)
- Elasticsearch enables faceted search on crawled content
- Redis manages job queues for distributed crawlers
- Object storage keeps database lean for performance

---

### Backend Layer

**Primary Choice: Python/FastAPI**

| Aspect | FastAPI | Node.js Comparison |
|--------|---------|-------------------|
| **Async Support** | Native async/await, asyncio | Promise-based, event-driven |
| **Type Safety** | Pydantic models, runtime validation | TypeScript (additional layer) |
| **Data Science Integration** | pandas, numpy, scikit-learn ready | Manual wrapping needed |
| **Performance** | 22k req/s (benchmarks) | 20k req/s with clustering |
| **Dev Experience** | Modern, autodocs (Swagger) | Mature, larger ecosystem |
| **Deployment** | Uvicorn, Gunicorn, containers | PM2, clustering needed |
| **Learning Curve** | Moderate | Flatter initially, complex at scale |

**Why FastAPI over Node.js:**
- Better support for data processing (ML models, analytics)
- Native async primitives for web scraping
- Excellent type safety with Pydantic
- Simpler deployment with containers
- Automatic API documentation

**Architecture:**
```
FastAPI Backend Layers:
├── API Routes (FastAPI routers)
├── Service Layer (business logic)
├── Data Layer (SQLAlchemy ORM)
├── Queue Worker (Celery + Redis)
└── Utils (logging, error handling, auth)
```

---

### Web Crawling Layer

**Primary Choice: Puppeteer (JavaScript) with Python Orchestration**

| Tool | Decision | Rationale |
|------|----------|-----------|
| **Crawler Framework** | Puppeteer | Modern headless browser, handles JavaScript-heavy sites |
| **Alternative** | Scrapy | Better for HTML-only content, middleware system |
| **Execution** | Node.js service | Puppeteer native support, lightweight |
| **Orchestration** | Python + Celery | Distributed task queue, scalability |

**Hybrid Architecture:**
- Python (FastAPI) handles scheduling & orchestration
- Node.js (Puppeteer) handles browser automation
- Redis queue coordinates jobs
- Celery workers distribute crawls

**Why Puppeteer + Node.js:**
- Handles JavaScript-rendered content (modern SPAs)
- Chrome DevTools Protocol for advanced control
- Better cookie/session handling
- Screenshot & PDF generation built-in
- Native async/await in JavaScript

**Why Not Scrapy:**
- Limited JavaScript execution (would need Splash)
- Better for static HTML content
- More verbose configuration
- Less suitable for dynamic content

---

### Analytics & BI Layer

**Primary Choice: Metabase**

| Component | Choice | Rationale | Alternatives |
|-----------|--------|-----------|--------------|
| **BI Dashboard** | Metabase | No-code dashboards, SQL queries, MongoDB support | Superset (Python-heavy, more setup) |
| **Data Warehouse** | PostgreSQL views | Aggregated data from transactional DB | Separate DW (complexity overkill) |
| **Analytics Events** | PostgREST hooks | Real-time event triggers | Custom webhooks |
| **Reports** | Scheduled queries | Daily/weekly aggregations | Ad-hoc analysis via API |

**Why Metabase over Superset:**
- Simpler deployment (single Java jar or Docker)
- Better UX for non-technical users
- Faster setup time
- SQL editor with autocomplete
- Native PostgreSQL support
- Easy sharing & embedding

**Analytics Stack:**
```
Crawl Data
    ↓
PostgreSQL (transactional)
    ↓
Views (aggregated data)
    ↓
Metabase Dashboard
    ├─ Domain crawl success rates
    ├─ Content discovery trends
    ├─ Performance metrics
    └─ API usage analytics
```

---

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Next.js Frontend (React)                                   │
│  ├─ Search Interface                                        │
│  ├─ Admin Dashboard                                         │
│  └─ Analytics Dashboard                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐     ┌───────▼──────────┐
│  API Gateway     │     │  WebSocket       │
│  (Rate Limiting) │     │  (Real-time)     │
└───────┬──────────┘     └──────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                    BACKEND LAYER (FastAPI)                   │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Routes                                           │   │
│  │ ├─ /api/domains (CRUD)                             │   │
│  │ ├─ /api/crawl (start/status)                       │   │
│  │ ├─ /api/search (full-text)                         │   │
│  │ ├─ /api/analytics                                  │   │
│  │ └─ /api/auth                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Service Layer                                        │   │
│  │ ├─ DomainService (CRUD operations)                 │   │
│  │ ├─ CrawlService (orchestration)                    │   │
│  │ ├─ SearchService (ES queries)                      │   │
│  │ └─ AnalyticsService (aggregations)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Middleware                                           │   │
│  │ ├─ Authentication (JWT)                            │   │
│  │ ├─ Authorization (RBAC)                            │   │
│  │ ├─ Logging & Monitoring                            │   │
│  │ └─ Error Handling                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬────────────┬───────────┬────────────┬────────────────┘
        │            │           │            │
┌───────▼────┐ ┌────▼────┐ ┌───▼──────┐ ┌──▼──────────┐
│  PostgreSQL│ │ Redis   │ │Elastic   │ │  S3/R2      │
│  (Primary  │ │(Queue   │ │ Search   │ │ (Crawled    │
│   DB)      │ │ & Cache)│ │(Indexes) │ │  Content)   │
└────────────┘ └─────────┘ └──────────┘ └─────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│               JOB QUEUE LAYER (Celery)                   │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐                 │
│  │  Crawler Tasks │  │ Analytics Jobs │                 │
│  │  ├─ Domain crawl    │ ├─ Daily agg    │                 │
│  │  ├─ Content index   │ ├─ ES reindex   │                 │
│  │  └─ Screenshot      │ └─ Report gen   │                 │
│  └────────────────┘  └────────────────┘                 │
└──────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│            WEB CRAWLING LAYER (Puppeteer)                │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐ │
│  │ Headless Chrome (Puppeteer + Node.js)             │ │
│  │ ├─ Page rendering                                │ │
│  │ ├─ Content extraction                            │ │
│  │ ├─ JavaScript execution                          │ │
│  │ └─ Screenshot capture                            │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│              ANALYTICS LAYER (Metabase)                  │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐ │
│  │ Metabase BI Dashboard                             │ │
│  │ ├─ Crawl success rates                            │ │
│  │ ├─ Content discovery trends                       │ │
│  │ ├─ Performance metrics                            │ │
│  │ ├─ API usage patterns                             │ │
│  │ └─ User activity analytics                        │ │
│  └────────────────────────────────────────────────────┘ │
│  Query Against: PostgreSQL Views                       │
└──────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development Environment
```
Local Machine
├─ Next.js (port 3000)
├─ FastAPI (port 8000)
├─ Redis (port 6379)
├─ PostgreSQL (port 5432)
└─ Elasticsearch (port 9200)
```

### Production Environment
```
┌─────────────────────────────────────────────┐
│         Vercel (Next.js Frontend)           │
│  ├─ Edge functions for API routing         │
│  └─ Static asset CDN                       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│    Container Orchestration (Kubernetes)     │
├──────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐        │
│  │ FastAPI Pods │  │ Celery Pods  │        │
│  │ (3 replicas) │  │ (2 replicas) │        │
│  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Puppeteer    │  │ Health Check │        │
│  │ Containers   │  │ Service      │        │
│  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
┌───────▼───┐ ┌───▼─────┐ ┌─▼──────────┐
│PostgreSQL │ │  Redis  │ │Elasticsearch
│(Managed)  │ │(Managed)│ │ (Managed)
└───────────┘ └─────────┘ └─────────────┘
```

---

## Data Flow Diagrams

### Crawling Pipeline
```
1. User adds domain via UI
   ↓
2. API stores domain in PostgreSQL
   ↓
3. Celery job scheduled (Redis queue)
   ↓
4. Puppeteer crawler starts
   ├─ Fetch page content
   ├─ Execute JavaScript
   ├─ Extract metadata
   └─ Take screenshot
   ↓
5. Crawl results stored:
   ├─ PostgreSQL (metadata, status)
   ├─ Elasticsearch (full-text index)
   └─ S3 (raw HTML, screenshots)
   ↓
6. Real-time update to frontend (WebSocket)
   ↓
7. Analytics job triggered (Celery)
   ├─ Update aggregated views
   ├─ Calculate success rates
   └─ Index new data
```

### Search Flow
```
1. User enters search query
   ↓
2. Query sent to FastAPI /search endpoint
   ↓
3. Elasticsearch full-text search
   ├─ Query parsed & analyzed
   ├─ Index searched in parallel
   └─ Results ranked by relevance
   ↓
4. Additional metadata fetched from PostgreSQL
   (domain info, crawl status, category)
   ↓
5. Results cached in Redis (15 min TTL)
   ↓
6. Return JSON to frontend
   ↓
7. Frontend renders results with pagination
```

### Analytics Pipeline
```
Transactional Data (PostgreSQL)
   ↓
Scheduled Jobs (Celery)
   ├─ Hourly: Update crawl success rates
   ├─ Daily: Aggregate content discovery trends
   └─ Weekly: Generate performance reports
   ↓
Aggregated Views (PostgreSQL)
   ├─ view_hourly_crawl_stats
   ├─ view_domain_performance
   ├─ view_content_categories
   └─ view_user_activity
   ↓
Metabase Queries
   ├─ Real-time dashboard updates
   ├─ Historical trend analysis
   └─ Scheduled report generation
   ↓
Stakeholder Insights
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up FastAPI project structure
- [ ] PostgreSQL schema migration from Supabase
- [ ] Redis setup (development & production)
- [ ] Basic API endpoints (domains, categories)
- [ ] Authentication middleware

### Phase 2: Crawling Engine (Weeks 3-4)
- [ ] Puppeteer service setup (Node.js)
- [ ] Celery worker configuration
- [ ] Crawl job queue implementation
- [ ] Result storage pipeline
- [ ] Job status tracking

### Phase 3: Search & Analytics (Weeks 5-6)
- [ ] Elasticsearch cluster setup
- [ ] Full-text indexing pipeline
- [ ] Search API endpoint
- [ ] PostgreSQL aggregated views
- [ ] Metabase dashboard setup

### Phase 4: Production Deployment (Weeks 7-8)
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring & alerting (Prometheus, Grafana)
- [ ] Load testing & optimization

---

## Scalability Strategy

### Horizontal Scaling
- **FastAPI**: Load balancer + N replicas (K8s HPA)
- **Celery**: Add worker nodes for more crawling capacity
- **Puppeteer**: Dedicated crawler nodes, browser instance pooling
- **Elasticsearch**: Shard crawl indices by date/domain

### Vertical Optimization
- **Connection pooling**: SQLAlchemy + pgbouncer for DB
- **Caching**: Redis for frequently accessed data
- **CDN**: Cloudflare for static assets
- **Compression**: Gzip response bodies

### Database Optimization
- [ ] Indexing strategy (domain, category, crawl_date)
- [ ] Partitioning crawl logs by date
- [ ] Archive old data to cold storage
- [ ] Query optimization with EXPLAIN ANALYZE

---

## Security Considerations

### API Security
- JWT-based authentication
- Rate limiting (Redis-backed)
- CORS policy enforcement
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

### Data Protection
- PostgreSQL encryption at rest
- TLS for all network communication
- S3 server-side encryption
- Redis ACL for restricted access

### Deployment Security
- Secret management (sealed secrets in K8s)
- Network policies (ingress/egress control)
- Pod security policies
- Regular vulnerability scanning (Trivy)

---

## Monitoring & Logging

### Application Metrics
- Request latency (P50, P95, P99)
- Error rates by endpoint
- Queue depth and job duration
- Crawl success/failure rates
- Elasticsearch query performance

### Infrastructure Metrics
- CPU, memory, disk usage
- Network I/O patterns
- Database connection pool
- Cache hit rates
- Container restart frequency

### Logging Strategy
- Structured logging (JSON format)
- Log aggregation (ELK Stack or Loki)
- Distributed tracing (Jaeger)
- Application performance monitoring (New Relic/DataDog)

---

## Cost Optimization

### Infrastructure Costs
- PostgreSQL: Managed service (AWS RDS ~$200/month for production)
- Redis: Managed service (AWS ElastiCache ~$150/month)
- Elasticsearch: Self-hosted on K8s or managed (~$300-500/month)
- S3: Pay-as-you-go storage (~$100-200/month based on usage)
- Kubernetes: 3-5 nodes (~$300-500/month on AWS EKS)

### Estimated Monthly Cost: $1,000-1,500
- Can be reduced with reserved instances and spot instances

### Cost Reduction Strategies
- Use spot instances for Celery workers (50-70% savings)
- Archive old crawl data to Glacier
- Implement crawl deduplication
- Right-size database replicas based on traffic

---

## Conclusion

This infrastructure supports:
- **Scalability**: Horizontal scaling for all components
- **Reliability**: Managed services, high availability, automatic failover
- **Performance**: Caching, indexing, CDN optimization
- **Maintainability**: Modern tech stack, containerized deployment
- **Analytics**: Real-time insights via Metabase dashboards
- **Cost-effectiveness**: Balanced between features and expenses

**Status**: Ready for implementation
**Next Steps**: Begin Phase 1 foundation setup
