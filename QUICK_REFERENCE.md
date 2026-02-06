# Infrastructure Stack - Quick Reference Card

## 🎯 Core Technologies at a Glance

### Frontend
```
Next.js 14+ (React 18)
├─ Deployed on Vercel
├─ TypeScript + Tailwind CSS
├─ Real-time updates via WebSocket
└─ Edge functions for API routing
```

### Backend
```
Python 3.11+ with FastAPI
├─ 22,000+ requests/second
├─ Automatic API documentation (Swagger)
├─ Pydantic validation (type-safe)
├─ Async/await native support
└─ Deployed on Kubernetes
```

### Web Crawling
```
Node.js + Puppeteer
├─ Handles JavaScript-rendered content
├─ Chrome DevTools Protocol automation
├─ Screenshot & PDF generation
├─ Orchestrated by FastAPI + Celery
└─ Scales horizontally with worker pools
```

### Databases
```
PostgreSQL 15+ (Primary)
├─ 100GB+ capacity
├─ Multi-AZ for HA
├─ ACID transactions
└─ AWS RDS Managed

Redis 7+ (Cache & Queue)
├─ Session management
├─ Celery broker
├─ Rate limiting
└─ AWS ElastiCache

Elasticsearch 8+ (Search)
├─ Full-text indexing
├─ Sub-second queries
├─ Faceted search
└─ AWS OpenSearch
```

### Job Queue
```
Celery 5.3+
├─ Distributed task processing
├─ Redis broker
├─ Automatic retries
├─ Task scheduling (Celery Beat)
└─ Horizontal scaling
```

### Analytics
```
Metabase 47+
├─ No-code dashboards
├─ SQL query editor
├─ Scheduled reports
├─ Real-time alerts
└─ Docker deployment
```

### Infrastructure
```
Kubernetes 1.27+
├─ 3-10 nodes (auto-scaling)
├─ AWS EKS managed service
├─ Rolling updates
├─ Self-healing pods
└─ Multi-AZ deployment

Docker
├─ Container images
├─ ECR registry
├─ Reproducible deployments
└─ Multi-stage builds

GitHub Actions
├─ CI/CD pipeline
├─ Automated tests
├─ Image building
└─ Kubernetes deployment
```

### Monitoring
```
Prometheus + Grafana
├─ Metrics collection
├─ Custom dashboards
├─ Alerting rules
└─ Time-series data

ELK Stack / Loki
├─ Centralized logging
├─ Log aggregation
├─ Searchable logs
└─ Docker integration

Jaeger
├─ Distributed tracing
├─ Request flow visualization
├─ Performance profiling
└─ Error analysis
```

---

## 📊 Decision Matrix

### Database Selection
```
Requirement              PostgreSQL  MongoDB  Firebase
────────────────────────────────────────────────────
Relational Data         ✅✅✅      ❌       ⚠️
Full-Text Search        ❌          ❌       ❌
Transactions            ✅✅✅      ⚠️       ❌
Scalability             ✅✅        ✅✅✅    ✅✅✅
Cost at Scale           ✅✅        ✅✅     ⚠️
Maturity                ✅✅✅      ✅✅     ✅✅
Self-Hosted Option      ✅✅✅      ✅✅✅    ❌

CHOICE: PostgreSQL (+ Elasticsearch for search)
```

### Backend Framework
```
Requirement              FastAPI    Node.js   Java
────────────────────────────────────────────────────
Type Safety             ✅✅✅      ⚠️        ✅✅
Async Native            ✅✅✅      ✅✅✅    ❌
Performance             ✅✅✅      ✅✅      ✅✅
Data Processing         ✅✅✅      ⚠️        ✅
Auto Documentation      ✅✅✅      ❌        ⚠️
Learning Curve          ✅✅        ✅✅✅    ⚠️
Scalability             ✅✅✅      ✅✅✅    ✅✅✅

CHOICE: Python + FastAPI
```

### Web Crawler
```
Requirement              Puppeteer  Scrapy   Selenium
────────────────────────────────────────────────────
JavaScript Support      ✅✅✅     ❌        ⚠️
Performance             ✅✅        ✅✅✅    ⚠️
Modern SPA Support      ✅✅✅      ❌        ⚠️
Screenshot/PDF          ✅✅✅      ❌        ❌
Memory Usage            ⚠️          ✅✅✅    ❌
DevTools Protocol       ✅✅✅      ❌        ❌
Ease of Use             ✅✅✅      ⚠️        ✅✅

CHOICE: Puppeteer (Node.js)
```

### Container Orchestration
```
Requirement              Kubernetes  Docker  AWS ECS
                                     Swarm
────────────────────────────────────────────────────
Cloud Agnostic          ✅✅✅      ✅✅     ❌
Auto-Scaling            ✅✅✅      ⚠️       ✅✅✅
Self-Healing            ✅✅✅      ❌        ✅✅
Rolling Updates         ✅✅✅      ⚠️       ✅✅
Ecosystem               ✅✅✅      ✅✅     ✅✅
Monitoring Tools        ✅✅✅      ⚠️       ⚠️
Learning Curve          ⚠️          ✅✅✅    ✅✅

CHOICE: Kubernetes (AWS EKS)
```

---

## 🔄 Data Flow Diagrams

### Crawling Pipeline
```
User Request
    ↓
API /api/crawl/start
    ↓
Store domain in PostgreSQL
    ↓
Create Celery task → Redis queue
    ↓
Worker picks up task
    ↓
Puppeteer renders page
    ├─ Execute JavaScript
    ├─ Extract content
    └─ Take screenshot
    ↓
Store results:
├─ PostgreSQL (metadata)
├─ Elasticsearch (index)
└─ S3 (raw content)
    ↓
WebSocket: Real-time status update
    ↓
Update dashboard
```

### Search Flow
```
User enters query
    ↓
API /api/search
    ↓
Check Redis cache (15 min TTL)
    ↓
Cache miss?
├─YES: Query Elasticsearch
│     ├─ Full-text search
│     ├─ Apply filters
│     └─ Rank results
└─NO: Return cached results
    ↓
Fetch metadata from PostgreSQL
    ↓
Cache results in Redis
    ↓
Return JSON to frontend
```

### Analytics Pipeline
```
Crawl completes
    ↓
Insert log to PostgreSQL
    ↓
Celery job: Index in Elasticsearch
    ↓
Scheduled jobs (hourly/daily)
├─ Calculate success rates
├─ Aggregate trends
└─ Update materialized views
    ↓
Metabase reads aggregated views
    ↓
Dashboards refresh
    ↓
Stakeholders view insights
```

---

## 📈 Performance Specifications

### API Performance Targets
```
Endpoint                    Target      Rationale
──────────────────────────────────────────────────
GET /api/search            <500ms       ES query time
POST /api/crawl/start      <200ms       Quick response
GET /api/domains           <100ms       Cache hit
GET /api/analytics         <1000ms      Aggregation
GET /api/health            <50ms        Simple check
```

### Scalability Metrics
```
Metric                      Target        Status
──────────────────────────────────────────────────
Domains stored             1,000,000     PostgreSQL
Crawl logs retained        5,000,000     Partitioned
Search index size          50GB          Elasticsearch
Concurrent users           1,000         FastAPI + HPA
Requests/second            5,000         K8s scaling
Crawl throughput           100/min       Celery workers
```

### Infrastructure Limits
```
Component               Max Capacity      Scaling Method
────────────────────────────────────────────────────────
K8s Cluster            10 nodes          Manual (EKS)
FastAPI Pods           10 replicas       HPA at 70% CPU
Celery Workers         20 workers        HPA at queue depth
PostgreSQL             100GB             RDS upgrades
Elasticsearch          3 nodes           Shard count
Redis Cache            2GB               ElastiCache tier
```

---

## 💰 Cost Breakdown

### Monthly Costs (Production)

```
Component                   Cost        % of Total
────────────────────────────────────────────────
EKS Cluster                 $300        22%
RDS PostgreSQL              $450        33%
ElastiCache Redis           $100        7%
OpenSearch                  $250        19%
S3 Storage/Transfer         $150        11%
Network & Misc              $80         6%
Vercel Frontend             $20         1%

TOTAL                       $1,350      100%
```

### Optimization Strategies

```
Strategy                    Savings     Effort
────────────────────────────────────────────
Reserved Instances (1yr)    30-40%      Medium
Spot Instances (workers)    50-70%      Medium
Data Archival (old crawls)  80%         Low
Right-size resources        15-20%      Low
Consolidate services        10%         Medium
────────────────────────────────────────────
Optimized Total             ~$900-1000  
```

---

## 🔐 Security Checklist

```
✅ Authentication
  ├─ JWT tokens
  ├─ Refresh token rotation
  ├─ Password hashing (bcrypt)
  └─ Session timeouts

✅ Authorization
  ├─ Role-based access control (RBAC)
  ├─ Resource-level permissions
  ├─ Admin vs. user tiers
  └─ API key management

✅ Data Protection
  ├─ TLS/HTTPS everywhere
  ├─ PostgreSQL encryption at rest
  ├─ S3 server-side encryption
  ├─ Redis ACLs
  └─ Secrets in sealed-secrets

✅ Infrastructure Security
  ├─ Network policies (K8s)
  ├─ Pod security policies
  ├─ DDoS protection
  ├─ WAF on load balancer
  └─ Regular patching

✅ Monitoring
  ├─ Audit logging
  ├─ Failed login alerts
  ├─ Rate limit tracking
  ├─ Vulnerability scanning
  └─ Security headers
```

---

## 📋 Implementation Checklist

### Pre-Implementation
- [ ] Get team buy-in and approval
- [ ] Allocate engineering resources
- [ ] Set up AWS account and EKS cluster
- [ ] Configure GitHub repository and CI/CD
- [ ] Provision development environment

### Phase 1: Foundation (Weeks 1-2)
- [ ] Initialize FastAPI project
- [ ] Set up PostgreSQL and migrations
- [ ] Create basic API routes
- [ ] Implement JWT authentication
- [ ] Configure environment variables

### Phase 2: Crawling (Weeks 3-4)
- [ ] Deploy Puppeteer service
- [ ] Set up Celery workers
- [ ] Configure Redis broker
- [ ] Implement job status tracking
- [ ] Create crawl API endpoints

### Phase 3: Search & Analytics (Weeks 5-6)
- [ ] Deploy Elasticsearch cluster
- [ ] Create indexing pipeline
- [ ] Implement search API
- [ ] Set up Metabase
- [ ] Create analytics dashboards

### Phase 4: Production (Weeks 7-8)
- [ ] Deploy to Kubernetes
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring and alerting
- [ ] Perform load testing
- [ ] Documentation and handoff

### Post-Implementation
- [ ] Team training on operations
- [ ] Performance optimization
- [ ] Cost fine-tuning
- [ ] Security audit
- [ ] SLA establishment

---

## 🎓 Team Skill Requirements

### Tier 1: Critical
```
✓ Python 3.9+
✓ FastAPI fundamentals
✓ PostgreSQL & SQL
✓ Docker basics
✓ Git & GitHub
✓ RESTful API design
```

### Tier 2: Important
```
✓ Kubernetes basics
✓ CI/CD pipelines
✓ Monitoring & observability
✓ Linux/Unix
✓ Network concepts
✓ Security best practices
```

### Tier 3: Beneficial
```
✓ Elasticsearch concepts
✓ Message queues (Celery)
✓ Browser automation
✓ Cloud platforms (AWS)
✓ Infrastructure as Code
```

---

## 📞 Support & Resources

### Documentation Files
- `INFRASTRUCTURE.md` - Complete architecture
- `TECH_STACK_SUMMARY.md` - Tech decisions
- `ADR.md` - Architecture decision records
- `DEPLOYMENT_SPEC.md` - Implementation specs
- `INFRASTRUCTURE_PLANNING_SUMMARY.md` - Executive summary

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [PostgreSQL Manual](https://www.postgresql.org/docs/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Docker Documentation](https://docs.docker.com/)

### Key Contacts
- **Architecture Lead**: @architect
- **DevOps Lead**: @devops
- **Backend Lead**: @backend
- **Infrastructure**: @infrastructure

---

**Infrastructure Planning - Phase 1.3**
**Status**: ✅ COMPLETE AND APPROVED
**Next Phase**: Backend Implementation (Phase 2)
**Start Date**: Ready to begin Week 1
