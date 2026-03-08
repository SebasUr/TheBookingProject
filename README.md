# Booking Platform

Multi-business booking and payment platform built with microservices.

## Architecture

- **API Gateway** - Routes requests to services (FastAPI + httpx)
- **Business Service** - Business CRUD, services, schedules (FastAPI + MongoDB)
- **Booking Service** - Booking lifecycle, optimistic locking, saga orchestration (FastAPI + MongoDB)
- **Payment Service** - Payment processing with circuit breaker (FastAPI + MongoDB)
- **Analytics Service** - CQRS read/write separation (FastAPI + MongoDB)
- **Notification Service** - Event consumer (Redis Pub/Sub)
- **Frontend** - React + Vite

## Patterns

| Pattern | Where |
|---|---|
| Microservices | 4+ independent services |
| API Gateway | Reverse proxy routing |
| Database per Service | Separate MongoDB databases |
| Event-Driven | Redis Pub/Sub domain events |
| CQRS | Analytics write/read models |
| Saga | Booking → Payment orchestration |
| Repository | Data access abstraction |
| Optimistic Locking | Booking version control |
| Circuit Breaker | Payment external calls |
| Controller | FastAPI route handlers |

## Run

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Gateway: http://localhost:8000
- Business API: http://localhost:8001
- Booking API: http://localhost:8002
- Payment API: http://localhost:8003
- Analytics API: http://localhost:8004

## Local Development (without Docker)

```bash
# Start MongoDB and Redis locally first

# Each service:
cd services/business && pip install -r requirements.txt && python main.py
cd services/booking && pip install -r requirements.txt && python main.py
cd services/payment && pip install -r requirements.txt && python main.py
cd services/analytics && pip install -r requirements.txt && python main.py
cd services/notification && pip install -r requirements.txt && python main.py
cd gateway && pip install -r requirements.txt && uvicorn main:app --port 8000

# Frontend:
cd frontend && npm install && npm run dev
```
