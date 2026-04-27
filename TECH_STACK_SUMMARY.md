# Tech Stack Decision Summary

## Executive Overview

**MCP-BD Explorer** is transitioning from a Next.js-only application to a production-grade microservices architecture optimized for web crawling, content indexing, and analytics.

---

## Selected Tech Stack

### 🎯 Frontend Layer
- **Framework**: Next.js 14+ (existing)
- **UI**: React 18, Tailwind CSS, shadcn/ui
- **Deployment**: Vercel (existing)
- **Status**: ✅ No changes

### 🔌 API & Backend Layer
- **Framework**: **Python/FastAPI** ✅
- **Server**: Uvicorn (production), Gunicorn (scaling)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Authentication**: JWT + Bcrypt
- **API Documentation**: Swagger/OpenAPI (auto-generated)
- **Deployment**: Docker containers on Kubernetes

### 💾 Storage Layer
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary DB** | PostgreSQL 15+ | Domain data, crawl logs, user info |
| **Cache** | Redis 7+ | Session management, job queues, rate limiting |
| **Search** | Elasticsearch 8+ | Full-text content indexing, faceted search |
| **File Storage** | S3-compatible (R2/AWS S3) | Crawled HTML, screenshots, archives |

### 🔄 Message Queue & Background Jobs
- **Framework**: Celery 5+
- **Broker**: Redis
- **Worker**: Multiple Celery workers
- **Task Types**: Domain crawling, content indexing, analytics aggregation

### 🌐 Web Crawling Engine
- **Technology**: **Puppeteer (Node.js)** ✅
- **Architecture**: Headless Chrome automation
- **Integration**: Orchestrated by FastAPI, scheduled via Celery
- **Capabilities**:
  - JavaScript-rendered content
  - Screenshot & PDF generation
  - Cookie/session management
  - Network request interception

### 📊 Analytics & BI
- **Dashboard**: **Metabase** ✅
- **Data Warehouse**: PostgreSQL views (no separate DW needed)
- **Metrics**: 
  - Crawl success rates
  - Content discovery trends
  - API usage patterns
  - Performance metrics

### 🚀 Infrastructure & Deployment
- **Containerization**: Docker
- **Orchestration**: Kubernetes (K8s)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or Loki
- **Service Mesh** (optional): Istio for advanced traffic management

---

## Decision Rationale

### Why Python/FastAPI over Node.js?
```
┌─────────────────────────────────────────┐
│ Criteria          │ FastAPI │ Node.js  │
├─────────────────────────────────────────┤
│ Async Support     │ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐⭐ │
│ Type Safety       │ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐  │
│ Data Science      │ ⭐⭐⭐⭐⭐ │ ⭐⭐   │
│ Web Scraping      │ ⭐⭐⭐⭐  │ ⭐⭐⭐⭐ │
│ Auto Docs         │ ⭐⭐⭐⭐⭐ │ Manual  │
│ Performance       │ 22k req/s│ 20k req/s
│ Dev Experience    │ Modern   │ Mature  │
│ Learning Curve    │ Moderate │ Flat    │
└─────────────────────────────────────────┘

Winner: FastAPI (better for this use case)
- Native async/await
- Pydantic validation
- Data processing capabilities
- Simpler deployment
```

### Why Puppeteer + Hybrid Architecture?
```
Scrapy                          Puppeteer
├─ Best for HTML-only          ├─ Best for dynamic content
├─ Middle layer for JS          ├─ Native JS support
├─ Complex setup                ├─ Simple integration
└─ Better middleware            └─ Better browser control

Hybrid Approach:
┌─────────────────────────────────┐
│ Python (FastAPI) - Orchestration│
│ + Node.js (Puppeteer) - Crawling│
│ = Best of both worlds           │
└─────────────────────────────────┘
```

### Why Metabase over Apache Superset?
```
Metabase                    Apache Superset
├─ Simple deployment        ├─ Python-heavy
├─ No-code dashboards       ├─ Requires setup
├─ Better UX                ├─ More features
├─ Fast to value            ├─ More customizable
└─ Perfect for SMB          └─ Better for enterprises

Choice: Metabase
(Faster to implement, easier to maintain)
```

---

## Architecture Comparison

### Before (Current - Next.js Only)
```
Frontend (Next.js)
    ↓
Supabase (DB + Auth)
    ↓
Limited to built-in REST API
```

### After (Production-Ready Microservices)
```
Frontend (Next.js)
    ↓
FastAPI Backend (Multiple instances)
    ├─ Crawling Service
    ├─ Search Service
    ├─ Analytics Service
    └─ Admin API
    ↓
Distributed Infrastructure
├─ PostgreSQL (scalable)
├─ Elasticsearch (fast search)
├─ Redis (caching & queues)
├─ S3 (file storage)
└─ Celery Workers (parallel processing)
    ↓
Metabase (Analytics)
```

---

## Feature Capabilities by Component

### FastAPI Backend
✅ RESTful API endpoints
✅ JWT authentication
✅ Rate limiting
✅ Input validation (Pydantic)
✅ Async background jobs
✅ WebSocket support (real-time)
✅ Auto API documentation
✅ CORS handling
✅ Database transactions

### Celery + Redis
✅ Distributed task queue
✅ Automatic retries
✅ Task scheduling
✅ Result storage
✅ Task monitoring
✅ Priority queues
✅ Rate limiting

### Puppeteer + Node.js
✅ JavaScript rendering
✅ Cookie management
✅ Screenshot capture
✅ PDF generation
✅ Network monitoring
✅ Performance metrics
✅ Error handling

### Elasticsearch
✅ Full-text search
✅ Faceted search
✅ Aggregations
✅ Real-time indexing
✅ Field boosting
✅ Fuzzy matching
✅ Highlighting

### PostgreSQL
✅ ACID transactions
✅ Complex queries
✅ Row-level security (RLS)
✅ JSON fields
✅ Full-text search (basic)
✅ Window functions
✅ Materialized views

### Metabase
✅ No-code dashboards
✅ SQL editor
✅ Scheduled reports
✅ Alerts
✅ Sharing & permissions
✅ Embedded dashboards
✅ Database connections

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | <200ms P95 | TBD |
| Crawl Throughput | 100 domains/min | TBD |
| Search Latency | <500ms | TBD |
| Availability | 99.9% | TBD |
| DB Query Time | <50ms P95 | TBD |
| Cache Hit Rate | >80% | TBD |

---

## Risk Analysis & Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Complexity** | High | Phased implementation, clear documentation |
| **Data migration** | Medium | Automated scripts, validation layer |
| **Puppeteer scaling** | Medium | Browser pooling, dedicated worker nodes |
| **Elasticsearch overhead** | Low | Managed service option available |
| **Celery job failures** | Low | Retry logic, dead letter queue |

### Operational Risks
| Risk | Impact | Mitigation |
|------|--------|-----------|
| **K8s learning curve** | Medium | Training, managed K8s (EKS/GKE) |
| **Multi-service debugging** | High | Distributed tracing (Jaeger) |
| **Cost overruns** | Medium | Reserved instances, spot instances |
| **Vendor lock-in** | Low | Standard technologies, portable |

---

## Migration Path from Current Setup

### Step 1: Parallel Deployment (Week 1-2)
- Deploy FastAPI alongside Next.js
- Both systems connect to Supabase
- Route new traffic to FastAPI, keep Next.js running

### Step 2: Data Migration (Week 2-3)
- PostgreSQL as new primary DB
- Migrate data from Supabase
- Set up PostgreSQL → Elasticsearch sync

### Step 3: Crawling Engine (Week 3-4)
- Deploy Puppeteer service
- Set up Celery workers
- Configure Redis queue

### Step 4: Cutover (Week 4-5)
- Switch frontend to use FastAPI
- Disable Supabase REST API calls
- Keep Supabase auth for now (optional cutover later)

### Step 5: Analytics (Week 5-6)
- Deploy Metabase
- Set up aggregated views
- Connect dashboards

### Step 6: Optimization (Week 6+)
- Performance tuning
- Cost optimization
- Monitoring refinement

---

## Success Criteria

✅ **Performance**: <200ms average response time for API calls
✅ **Reliability**: 99.9% uptime for core services
✅ **Scalability**: Handle 10x traffic increase without code changes
✅ **Maintainability**: Clear documentation, monitoring dashboards
✅ **Cost**: <$1,500/month operational costs
✅ **User Experience**: Improved search speed, real-time crawl updates
✅ **Analytics**: Comprehensive dashboards for insights
✅ **Extensibility**: Easy to add new crawlers, data sources

---

## Team Skills Required

### Core Team
- 1x **Backend Engineer** (Python/FastAPI)
- 1x **DevOps Engineer** (Kubernetes, Docker)
- 1x **Frontend Engineer** (React/Next.js) - can be shared
- 1x **Data Engineer** (optional, for Elasticsearch/Analytics)

### Knowledge Areas
- Python 3.9+
- PostgreSQL & SQL optimization
- Docker & Kubernetes basics
- Redis & message queues
- RESTful API design
- Git & CI/CD

---

## Recommended Next Steps

1. **Week 1**: Set up FastAPI project structure & database schema
2. **Week 2**: Implement core API endpoints
3. **Week 3**: Deploy Puppeteer service & Celery workers
4. **Week 4**: Implement Elasticsearch integration
5. **Week 5**: Set up Metabase dashboards
6. **Week 6**: Performance testing & optimization
7. **Week 7**: Production deployment & monitoring

---

## Documentation References

- Full Architecture: See `INFRASTRUCTURE.md`
- Deployment Guide: See `DEPLOYMENT.md` (to be created)
- API Specification: See `API_SPEC.md` (to be created)
- Database Schema: See `DATABASE_SCHEMA.md` (to be created)

---

**Document Status**: ✅ Approved for Implementation
**Last Updated**: 2026-02-06
**Version**: 1.0
