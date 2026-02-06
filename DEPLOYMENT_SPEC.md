# 1.3 Infrastructure Planning - Implementation Specifications

## Quick Reference Guide

### Stack Components at a Glance

```
┌────────────────────────────────────────────────────────────────┐
│                    TECH STACK OVERVIEW                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER          │ TECHNOLOGY           │ VERSION│ PURPOSE      │
│  ─────────────────────────────────────────────────────────────  │
│  Frontend       │ Next.js + React      │ 14+   │ Web UI       │
│  API Gateway    │ Vercel Edge Functions│ -     │ API routing  │
│                 │                      │       │              │
│  Backend        │ Python + FastAPI     │ 3.11+ │ REST API     │
│  Async Workers  │ Celery               │ 5.3+  │ Job queue    │
│  Task Broker    │ Redis                │ 7.x   │ Message q.   │
│                 │                      │       │              │
│  Primary DB     │ PostgreSQL           │ 15.x  │ Relational   │
│  Search Engine  │ Elasticsearch        │ 8.x   │ Full-text    │
│  Cache/Queue    │ Redis                │ 7.x   │ Pub/sub      │
│  File Storage   │ S3/R2/MinIO          │ -     │ Objects      │
│                 │                      │       │              │
│  Web Crawler    │ Puppeteer + Node.js  │ 20+   │ Browser auto │
│  Orchestration  │ Kubernetes           │ 1.27+ │ Container mgmt
│                 │                      │       │              │
│  Analytics      │ Metabase             │ 47+   │ BI Dashboard │
│  Monitoring     │ Prometheus + Grafana │ -     │ Metrics      │
│  Logging        │ ELK / Loki           │ -     │ Log agg      │
│  Tracing        │ Jaeger               │ 1.x   │ Distributed  │
│                 │                      │       │              │
└────────────────────────────────────────────────────────────────┘
```

---

## Deployment Specifications

### Development Environment Setup

#### Local Development Stack
```yaml
# docker-compose.yml for local development
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: mcp_bd_explorer
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - es_data:/usr/share/elasticsearch/data

  fastapi:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/mcp_bd_explorer
      REDIS_URL: redis://redis:6379
      ELASTICSEARCH_HOST: http://elasticsearch:9200
    depends_on:
      - postgres
      - redis
      - elasticsearch
    volumes:
      - ./backend:/app

  celery_worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/mcp_bd_explorer
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
  redis_data:
  es_data:
```

#### Setup Commands
```bash
# Clone repository
git clone https://github.com/neopilotai/mcp-bd-explorer.git
cd mcp-bd-explorer

# Start development stack
docker-compose up -d

# Wait for services to be ready
docker-compose logs -f postgres | grep "database system is ready"

# Create database tables
docker-compose exec fastapi alembic upgrade head

# Run initial seed data
docker-compose exec fastapi python -m app.scripts.seed

# Access services
# - Frontend: http://localhost:3000
# - FastAPI Docs: http://localhost:8000/docs
# - Elasticsearch: http://localhost:9200
# - Redis CLI: redis-cli -h localhost
```

---

### Production Environment Specifications

#### Kubernetes Deployment (AWS EKS)

##### Infrastructure Sizing
```
┌─────────────────────────────────────────────────────┐
│         PRODUCTION CLUSTER CONFIGURATION             │
├─────────────────────────────────────────────────────┤
│ Cluster Type     │ AWS EKS (Elastic Kubernetes)    │
│ Node Type        │ t3.large (2 vCPU, 8GB RAM)      │
│ Min Nodes        │ 3 (for HA)                      │
│ Max Nodes        │ 10 (auto-scaling)               │
│ Node Storage     │ 100GB GP3 (general purpose)     │
│                  │                                  │
│ FastAPI Pods     │ 3 replicas (rolling updates)    │
│ Celery Pods      │ 2 replicas (parallel crawling)  │
│ Puppeteer Pods   │ 5 replicas (crawler nodes)      │
│                  │                                  │
│ PostgreSQL       │ AWS RDS (multi-AZ, 100GB)       │
│ Redis            │ AWS ElastiCache (cache.t3.micro)
│ Elasticsearch    │ AWS OpenSearch (2 nodes)        │
│ S3               │ Standard (pay per use)          │
└─────────────────────────────────────────────────────┘
```

##### Kubernetes Manifests Structure
```
k8s/
├── namespaces/
│   └── mcp-bd-explorer.yaml
├── configmaps/
│   ├── app-config.yaml
│   └── logging-config.yaml
├── secrets/
│   └── credentials.yaml (sealed with sealed-secrets)
├── deployments/
│   ├── fastapi.yaml
│   ├── celery-worker.yaml
│   └── puppeteer-crawler.yaml
├── services/
│   ├── fastapi-service.yaml
│   ├── api-ingress.yaml
│   └── internal-services.yaml
├── statefulsets/
│   └── (optional for stateful components)
├── jobs/
│   └── db-migration-job.yaml
├── monitoring/
│   ├── prometheus-config.yaml
│   └── grafana-dashboard.yaml
└── hpa/
    ├── fastapi-hpa.yaml (Horizontal Pod Autoscaler)
    └── celery-hpa.yaml
```

##### Sample Deployment YAML
```yaml
# k8s/deployments/fastapi.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
  namespace: mcp-bd-explorer
  labels:
    app: fastapi
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      serviceAccountName: fastapi
      containers:
      - name: fastapi
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/mcp-bd-explorer-fastapi:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: credentials
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        - name: ELASTICSEARCH_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: elasticsearch-host
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
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
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: app-config
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - fastapi
              topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi
  namespace: mcp-bd-explorer
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: mcp-bd-explorer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi
  minReplicas: 3
  maxReplicas: 10
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

---

### Database Configuration

#### PostgreSQL Schema Overview
```sql
-- Core tables
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories(id),
    status VARCHAR(50) DEFAULT 'pending',
    last_crawled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_domains_status (status),
    INDEX idx_domains_category (category_id)
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crawl_logs (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id),
    status_code INTEGER,
    content_length BIGINT,
    load_time_ms INTEGER,
    title VARCHAR(255),
    description TEXT,
    keywords VARCHAR(1000),
    crawled_at TIMESTAMP DEFAULT NOW(),
    raw_content_key VARCHAR(255), -- S3 key
    INDEX idx_crawl_logs_domain (domain_id),
    INDEX idx_crawl_logs_crawled_at (crawled_at)
);

-- Aggregated views for Metabase
CREATE VIEW view_crawl_success_rate AS
SELECT 
    DATE(crawled_at) as date,
    COUNT(*) as total_crawls,
    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM crawl_logs
GROUP BY DATE(crawled_at)
ORDER BY date DESC;
```

#### Indexing Strategy
```sql
-- Performance-critical indices
CREATE INDEX idx_crawl_logs_domain_crawled ON crawl_logs(domain_id, crawled_at DESC);
CREATE INDEX idx_domains_created_at ON domains(created_at DESC);
CREATE INDEX idx_crawl_logs_status_code ON crawl_logs(status_code);
```

---

### Elasticsearch Configuration

#### Index Template
```json
PUT _index_template/crawled_content
{
  "index_patterns": ["crawled_content-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.refresh_interval": "30s",
      "analysis": {
        "analyzer": {
          "content_analyzer": {
            "type": "standard",
            "stopwords": "_english_"
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "domain_id": { "type": "integer" },
        "url": { "type": "keyword" },
        "title": {
          "type": "text",
          "analyzer": "content_analyzer",
          "fields": {
            "keyword": { "type": "keyword" }
          }
        },
        "content": {
          "type": "text",
          "analyzer": "content_analyzer"
        },
        "keywords": { "type": "keyword" },
        "crawled_at": { "type": "date" },
        "status_code": { "type": "integer" }
      }
    }
  }
}
```

---

### Redis Configuration

#### Production Settings
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
databases 16

# ACL for multi-tenant safety
user default >password +@all ~*
user celery on >celery_password +@all ~celery:*
user cache on >cache_password +@all ~cache:*
```

---

### CI/CD Pipeline (GitHub Actions)

#### Workflow Structure
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'k8s/**'
      - 'Dockerfile'
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: 123456789.dkr.ecr.us-east-1.amazonaws.com
  REPOSITORY_NAME: mcp-bd-explorer

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests --cov=app
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      - uses: aws-actions/amazon-ecr-login@v1
      - name: Build and push
        run: |
          docker build -t $ECR_REGISTRY/$REPOSITORY_NAME:latest -f Dockerfile .
          docker push $ECR_REGISTRY/$REPOSITORY_NAME:latest
          
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/eks-auth-action@v1
        with:
          cluster_name: mcp-bd-explorer-eks
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      - run: kubectl apply -f k8s/ --namespace=mcp-bd-explorer
      - run: kubectl rollout status deployment/fastapi -n mcp-bd-explorer
```

---

## Cost Estimation

### Monthly Infrastructure Costs (Production)

| Component | Size | Cost |
|-----------|------|------|
| **EKS Cluster** | 3 t3.large nodes | $300 |
| **RDS PostgreSQL** | 100GB, multi-AZ | $450 |
| **ElastiCache Redis** | cache.t3.micro | $100 |
| **OpenSearch** | 2 nodes t3.small | $250 |
| **S3 Storage** | 100GB storage | $50 |
| **S3 Transfer** | 1TB out/month | $100 |
| **NAT Gateway** | 1 per AZ (3) | $130 |
| **Elastic IPs** | 3 IPs | $30 |
| **CloudWatch Logs** | 50GB ingestion | $50 |
| **Vercel Frontend** | Pro tier | $20 |
| **Misc** | DNS, monitoring, backup | $50 |
| **TOTAL** | | **$1,530** |

### Cost Optimization Opportunities
- Use Reserved Instances: Save 30-40%
- Use Spot Instances for Celery workers: Save 50-70%
- Archive crawl data to Glacier: Save 80% on old data
- Consolidate small databases: Save 20%
- **Optimized Monthly Cost: ~$900-1,000**

---

## Monitoring & Alerting Setup

### Key Metrics to Monitor
```
┌─────────────────────────────────────────┐
│   CRITICAL METRICS                      │
├─────────────────────────────────────────┤
│ API Response Time    │ Target: <200ms P95│
│ Error Rate          │ Target: <0.1%     │
│ DB Connection Pool  │ Target: <80% use  │
│ Queue Depth         │ Target: <100 jobs │
│ Crawl Success Rate  │ Target: >95%      │
│ Cache Hit Rate      │ Target: >80%      │
│ Disk Space          │ Alert: >80% full  │
│ Pod Restarts        │ Alert: >2/hour    │
│ Memory Usage        │ Alert: >85%       │
│ CPU Usage           │ Alert: >75%       │
└─────────────────────────────────────────┘
```

---

## Security Checklist

- [ ] All API endpoints require authentication
- [ ] Rate limiting configured (100 req/min per user)
- [ ] HTTPS/TLS enforced everywhere
- [ ] Environment variables stored in sealed secrets
- [ ] Database encryption at rest enabled
- [ ] Network policies configured (pod-to-pod)
- [ ] Regular security scanning (Trivy, Snyk)
- [ ] WAF configured on load balancer
- [ ] DDoS protection enabled
- [ ] Regular backup and restore testing

---

**Infrastructure Planning Status**: ✅ COMPLETE
**Next Phase**: Implementation (Start Phase 1 - Week 1)
**Estimated Implementation Timeline**: 8 weeks
