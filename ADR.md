# Architecture Decision Records (ADR)

## ADR-001: Database Strategy

**Date**: 2026-02-06
**Status**: Accepted
**Context**: 
MCP-BD Explorer requires scalable storage for domain data, crawl logs, search indices, and file content. Current Supabase setup works for MVP but needs separation of concerns for production.

**Decision**:
Use a polyglot persistence approach:
- **PostgreSQL** for transactional data (primary database)
- **Elasticsearch** for full-text search
- **Redis** for caching and message queues
- **S3** for file storage

**Rationale**:
- Separation of concerns improves scalability
- Each technology optimized for specific use case
- PostgreSQL handles complex relationships
- Elasticsearch provides fast full-text search
- Redis enables real-time job queuing
- S3 reduces database size and improves performance

**Consequences**:
- (+) Better performance and scalability
- (+) Can scale each component independently
- (+) Easier to optimize queries per store type
- (-) Increased operational complexity
- (-) Data consistency requires careful synchronization
- (-) Migration effort from Supabase

**Alternatives Considered**:
- Single PostgreSQL with all data → Limited scalability
- MongoDB for everything → Not ideal for relational data
- Cloud-native solutions only → Vendor lock-in

---

## ADR-002: Backend Framework Selection

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Current Next.js API routes are limited for complex business logic. Need to handle distributed web crawling, real-time job management, and analytics aggregation.

**Decision**:
Use **Python with FastAPI** as the backend framework instead of expanding Node.js.

**Rationale**:
- FastAPI provides native async/await (20k+ req/s)
- Pydantic gives compile-time type checking
- Excellent data science ecosystem (pandas, numpy)
- Automatic OpenAPI/Swagger documentation
- Simpler deployment and scaling
- Better suited for data processing pipelines

**Consequences**:
- (+) Type-safe API with auto-documentation
- (+) Better data validation at API boundary
- (+) Native async for I/O-bound operations
- (+) Easier integration with ML/analytics libraries
- (-) Team must learn Python/FastAPI
- (-) Different language from frontend
- (-) Need to set up separate service

**Alternatives Considered**:
- Node.js/Express → Less type safety, not ideal for data processing
- Java/Spring Boot → Overkill for this scale, slower startup
- Go/Gin → Simpler but less ecosystem for data work
- Expand Next.js API routes → Limited scalability and complexity

---

## ADR-003: Web Crawling Technology

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Need to crawl both static HTML sites and JavaScript-rendered SPAs. Must handle cookies, sessions, and modern web technologies.

**Decision**:
Use **Puppeteer with Node.js** for the crawling engine, orchestrated by Python FastAPI backend.

**Rationale**:
- Puppeteer native support for headless Chrome
- Handles JavaScript-rendered content out-of-the-box
- Superior browser automation capabilities
- Better for modern single-page applications
- Can take screenshots and PDFs
- Excellent ecosystem and documentation

**Consequences**:
- (+) Handles dynamic content reliably
- (+) No additional middleware needed (vs. Scrapy + Splash)
- (+) Better browser DevTools Protocol support
- (+) Native JavaScript integration
- (-) More memory-intensive than Scrapy
- (-) Node.js adds another runtime to manage
- (-) Requires browser instance pooling for scale

**Alternatives Considered**:
- Scrapy → Better for HTML-only, needs Splash for JS
- Selenium → Older, slower, less maintained
- Playwright → Good option but Puppeteer more established
- Cheerio/jsdom → Can't handle complex JS interactions

---

## ADR-004: Message Queue & Background Jobs

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Web crawling is long-running, needs to be asynchronous. Must support task scheduling, retries, and status tracking.

**Decision**:
Use **Celery with Redis** as the job queue system.

**Rationale**:
- Industry-standard for Python background jobs
- Redis provides fast, reliable message broker
- Built-in task scheduling (Celery Beat)
- Automatic retry logic with exponential backoff
- Task status tracking and results storage
- Scales horizontally with multiple workers

**Consequences**:
- (+) Production-proven technology
- (+) Integrates seamlessly with FastAPI
- (+) Rich features for task management
- (+) Easy to add more workers
- (-) Redis becomes critical component
- (-) Debugging distributed tasks is harder
- (-) Requires monitoring for queue health

**Alternatives Considered**:
- RabbitMQ → More complex, overkill for this scale
- AWS SQS → Cloud-specific, less control
- APScheduler only → Can't handle distributed jobs
- Huey → Simpler but less mature

---

## ADR-005: Full-Text Search Engine

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Need fast full-text search across crawled content. PostgreSQL's full-text search is basic and not performant for large datasets.

**Decision**:
Use **Elasticsearch 8.x** as the dedicated search engine.

**Rationale**:
- Purpose-built for full-text search
- Fast query performance (sub-second for 1M+ documents)
- Advanced features: faceting, aggregations, highlighting
- Horizontal scaling through sharding
- Real-time indexing with refresh API
- Rich query DSL

**Consequences**:
- (+) Superior search performance
- (+) Faceted navigation support
- (+) Analytics aggregations
- (+) Can handle petabyte scale
- (-) Operational complexity (monitoring, tuning)
- (-) Data synchronization required
- (-) Memory-intensive infrastructure

**Alternatives Considered**:
- PostgreSQL full-text → Too slow for large datasets
- Meilisearch → Simpler but less features
- Algolia → SaaS, limited control, expensive
- Opensearch → Similar to ES, less ecosystem

---

## ADR-006: Analytics & BI Platform

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Stakeholders need dashboards showing crawl performance, content discovery trends, and API usage metrics.

**Decision**:
Use **Metabase** as the BI and analytics dashboard platform.

**Rationale**:
- No-code dashboard creation
- Simple deployment (Docker container)
- SQL editor for custom queries
- Automatic schema detection
- Scheduled reports and alerts
- Sharing and permission controls

**Consequences**:
- (+) Fast time-to-insights
- (+) Non-technical users can create queries
- (+) Minimal maintenance overhead
- (+) Cost-effective
- (-) Less powerful than enterprise BI tools
- (-) Customization limited compared to Superset
- (-) Scaling limited to moderate usage

**Alternatives Considered**:
- Apache Superset → More powerful but complex setup
- Tableau → Expensive, not worth for this scale
- Looker → Google/enterprise-focused
- Custom dashboards → Much more work to build

---

## ADR-007: Deployment & Orchestration

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Need to deploy multiple services (FastAPI, Celery, Puppeteer, Metabase) across potentially many servers with auto-scaling.

**Decision**:
Use **Docker + Kubernetes (K8s)** for container orchestration and deployment.

**Rationale**:
- Industry standard for microservices
- Cloud-agnostic (AWS, GCP, Azure compatible)
- Built-in auto-scaling and load balancing
- Self-healing (automatic restart of failed pods)
- Declarative infrastructure as code
- Large ecosystem and community support

**Consequences**:
- (+) Unified deployment across all services
- (+) Automatic scaling based on metrics
- (+) Canary deployments and blue-green deployments
- (+) Self-healing infrastructure
- (-) Steep learning curve for team
- (-) Operational complexity
- (-) Requires monitoring and alerting setup

**Alternatives Considered**:
- Docker Swarm → Simpler but less powerful
- Cloud platforms only (ECS, App Engine) → Vendor lock-in
- Traditional VMs → Manual scaling, hard to manage
- Serverless (Lambda, Cloud Functions) → Puppeteer doesn't fit well

---

## ADR-008: Frontend Deployment

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Next.js frontend is currently deployed on Vercel. New FastAPI backend is separate. Need to ensure smooth integration.

**Decision**:
Keep **Next.js on Vercel** for frontend, with API routes proxying to FastAPI backend.

**Rationale**:
- Vercel optimized for Next.js
- Edge functions can route requests efficiently
- Built-in CDN and auto-scaling
- Seamless deployments from GitHub
- Cost-effective for frontend serving

**Consequences**:
- (+) Best frontend performance
- (+) Simple deployments
- (+) Geographic distribution with Edge
- (-) API latency between Vercel and backend
- (-) Vendor lock-in to Vercel for frontend

**Alternatives Considered**:
- Deploy Next.js on K8s → Complex, defeats Vercel benefits
- Backend-driven SSR → Loses Next.js advantages
- Fully serverless → Puppeteer doesn't fit architecture

---

## ADR-009: Monitoring & Observability

**Date**: 2026-02-06
**Status**: Accepted
**Context**:
Distributed system with multiple services needs comprehensive monitoring to catch issues quickly.

**Decision**:
Use **Prometheus + Grafana** for metrics and **ELK Stack (or Loki)** for logging, with **Jaeger** for distributed tracing.

**Rationale**:
- Prometheus is standard for K8s monitoring
- Grafana provides rich visualization
- Loki designed for container environments
- Jaeger traces requests across services
- All open-source and cost-effective

**Consequences**:
- (+) Complete observability across all services
- (+) Can correlate metrics, logs, and traces
- (+) Early warning for issues
- (+) Cost-effective compared to SaaS
- (-) Operational overhead
- (-) Data storage requirements
- (-) Requires alerting setup

**Alternatives Considered**:
- Datadog → Expensive but enterprise-grade
- New Relic → Good but pricier than open-source
- AWS CloudWatch → Limited features, vendor lock-in
- No monitoring → Impossible to debug issues

---

## Summary Table

| Decision | Chosen | Key Reason |
|----------|--------|-----------|
| Database | PostgreSQL + Elasticsearch + Redis | Polyglot persistence for performance |
| Backend | Python + FastAPI | Type safety, async, data processing |
| Web Crawler | Puppeteer (Node.js) | JavaScript support, reliability |
| Job Queue | Celery + Redis | Production-proven, scales horizontally |
| Search | Elasticsearch | Fast full-text search at scale |
| Analytics | Metabase | No-code dashboards, simple deployment |
| Orchestration | Kubernetes | Standard, cloud-agnostic |
| Frontend | Next.js on Vercel | Optimized for Next.js |
| Monitoring | Prometheus + Grafana + Loki + Jaeger | Complete observability |

---

**Document Status**: ✅ All decisions approved
**Review Date**: 2026-02-06
**Next Review**: Post-implementation (4-6 weeks)
