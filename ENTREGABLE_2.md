# Entregable 2 - Implementación

---

## Nivel 3 - Componentes

### Controller

Cada servicio expone su lógica HTTP a través de un módulo `controller.py` que contiene un `APIRouter` de FastAPI. El router se monta en `main.py` y se encarga únicamente de recibir requests, delegar al repositorio o a la saga, y devolver respuestas. No contiene lógica de base de datos ni de negocio pesada.

Servicios que implementan el patrón: `business`, `booking`, `payment`, `analytics`, `auth`.

Ejemplo representativo: `services/booking/controller.py` maneja los endpoints `GET /`, `GET /slots`, `POST /`, `GET /{id}`, `POST /{id}/cancel`.

---

### Gestor de inventario con bloqueos optimistas

Implementado en `services/booking/repository.py`, método `update_status_optimistic`.

El mecanismo funciona así: al crear una reserva se le asigna un campo `version: 1`. Cada vez que se quiere cambiar su estado (de `pending` a `confirmed` o `cancelled`) se usa `find_one_and_update` con la condición `{ "_id": id, "version": expected_version }`. Si entre la lectura y la escritura otro proceso ya modificó el documento, la versión no coincide, la operación devuelve `None` y se lanza un `HTTP 409 Conflict`.

Esto evita que dos procesos concurrentes actualicen la misma reserva sin coordinar entre sí, sin necesidad de bloquear filas o colecciones.

```python
# services/booking/repository.py
result = await self.collection.find_one_and_update(
    {"_id": ObjectId(id), "version": expected_version},
    {
        "$set": {"status": new_status, "updated_at": ...},
        "$inc": {"version": 1},
    },
    return_document=True,
)
if not result:
    raise HTTPException(409, "Conflict: booking was modified by another process")
```

---

### Repository pattern

Cada servicio tiene un archivo `repository.py` que encapsula todo el acceso a MongoDB. Los controllers nunca escriben queries directamente; siempre llaman métodos del repositorio (`find_all`, `find_by_id`, `create`, `update`, `delete`). Esto aísla la capa de persistencia y facilita el reemplazo del motor de base de datos sin tocar la lógica de negocio.

Repositorios existentes:
- `services/business/repository.py` - `BusinessRepository`
- `services/booking/repository.py` - `BookingRepository`
- `services/payment/repository.py` - `PaymentRepository`
- `services/analytics/repository.py` - `AnalyticsWriteRepository`, `AnalyticsReadRepository`
- `services/auth/repository.py` - `UserRepository`

---

### Circuit breaker para llamadas externas

Implementado en `services/payment/circuit_breaker.py` y usado en `services/payment/controller.py`.

El circuit breaker maneja tres estados:

- **CLOSED**: funcionamiento normal, las llamadas pasan.
- **OPEN**: se superó el umbral de fallos (`failure_threshold = 3`), las llamadas se bloquean inmediatamente devolviendo `HTTP 503` sin intentar la llamada real.
- **HALF_OPEN**: pasado el tiempo de recuperación (`recovery_timeout = 30s`), se permite una llamada de prueba. Si tiene éxito vuelve a CLOSED; si falla regresa a OPEN.

En el controller, antes de llamar al proveedor de pagos externo se consulta `circuit_breaker.can_execute()`. Si el circuito está abierto, se responde de inmediato sin hacer la llamada. El endpoint `GET /circuit-breaker/status` expone el estado actual para monitoreo.

---

## Patrones arquitectónicos

### Microservicios (mínimo 4 servicios independientes)

El sistema tiene 6 servicios desplegables de forma independiente, cada uno con su propio proceso, Dockerfile y base de datos:

| Servicio | Puerto | Responsabilidad |
|---|---|---|
| `auth-service` | 8005 | Registro, login, validación de tokens JWT |
| `business-service` | 8001 | CRUD de negocios y sus servicios/horarios |
| `booking-service` | 8002 | Reservas, disponibilidad de slots, saga |
| `payment-service` | 8003 | Pagos, circuit breaker contra proveedor externo |
| `analytics-service` | 8004 | Métricas agregadas, consumidor de eventos |
| `notification-service` | - | Notificaciones al cliente vía eventos |

Cada uno se comunica a través de HTTP (sincrónicamente) o Redis pub/sub (asincrónicamente), sin compartir código ni base de datos.

---

### Event-Driven Architecture (eventos de dominio)

Los servicios publican eventos de dominio en un canal de Redis (`domain_events`) usando la clase `EventPublisher` en `services/booking/events.py`. Los suscriptores reciben y reaccionan de forma desacoplada.

Eventos publicados:

| Evento | Publicado por | Consumido por |
|---|---|---|
| `booking.created` | booking-service (saga) | analytics, notification |
| `booking.confirmed` | booking-service (saga) | analytics, notification |
| `booking.cancelled` | booking-service (saga) | analytics, notification |
| `payment.completed` | payment-service | notification |

`analytics-service` y `notification-service` suscriben al canal en su arranque y procesan cada mensaje de forma asíncrona. Ninguno de los dos necesita saber quién publicó el evento ni hace una llamada HTTP directa al servicio de origen.

---

### CQRS (separación lectura/escritura en módulo de analíticas)

El módulo de analíticas tiene dos repositorios con responsabilidades separadas:

**Write side** (`AnalyticsWriteRepository`): recibe cada evento de dominio y lo persiste tal cual en la colección `events`. Esto actúa como el log de eventos.

**Read side** (`AnalyticsReadRepository`): mantiene resúmenes pre-agregados por negocio y fecha en la colección `summaries`. Cuando llega un evento, el handler incrementa los contadores correspondientes (total reservas, confirmadas, canceladas, ingresos). Las queries de lectura nunca tocan la colección de eventos raw; consultan directamente los resúmenes, lo que los hace muy rápidos independientemente del volumen de eventos.

El `AnalyticsEventHandler` en `event_handler.py` actúa como el proyector que transforma los eventos del write side en las vistas del read side.

---

### API Gateway pattern

El servicio `gateway/main.py` es el único punto de entrada para el frontend. Recibe todas las peticiones en `/api/{service}/{path}` y las reenvía al microservicio correspondiente usando `httpx`.

Responsabilidades que centraliza el gateway:
- Enrutamiento hacia los 5 servicios backend
- Validación de tokens JWT para rutas protegidas (llama internamente a `auth-service/validate`)
- Inyección del header `X-User-Id` en los requests downstream una vez autenticado el token
- El frontend nunca conoce las URLs internas de los servicios

Las rutas protegidas son: `POST/PUT/DELETE /api/businesses` y cualquier método en `/api/analytics`.

---

### Database per Service

Cada servicio tiene su propia base de datos MongoDB aislada. Ningún servicio accede a la base de datos de otro:

| Servicio | Base de datos |
|---|---|
| auth-service | `auth_db` |
| business-service | `business_db` |
| booking-service | `booking_db` |
| payment-service | `payment_db` |
| analytics-service | `analytics_db` |

La comunicación entre servicios que necesita datos de otro servicio se hace por HTTP (por ejemplo, booking-service consulta al business-service para obtener el horario al calcular slots disponibles), nunca accediendo directamente a otra base de datos.

---

### Saga pattern para transacciones distribuidas (reserva -> pago)

Implementado en `services/booking/saga.py` como una saga de orquestación. El `BookingSaga` coordina los pasos de la transacción distribuida y maneja las compensaciones en caso de fallo.

Flujo normal:
1. La reserva se crea en estado `pending` (ya persistida antes de llamar la saga).
2. Se publica el evento `booking.created`.
3. Se llama al payment-service por HTTP para procesar el cobro.
4. Si el pago tiene éxito, se actualiza la reserva a `confirmed` usando bloqueo optimista y se publica `booking.confirmed`.

Flujo de compensación (si el pago falla o lanza excepción):
- Se actualiza la reserva a `cancelled` usando bloqueo optimista.
- Se publica `booking.cancelled`.
- El estado queda consistente aunque la transacción no se completó.

El bloqueo optimista dentro de la saga es importante: garantiza que si dos procesos intentan confirmar o cancelar la misma reserva simultáneamente, solo uno lo logrará y el otro recibirá un `409 Conflict`.

---

## Diagramas de arquitectura

### Vista general del sistema

```mermaid
flowchart TD
    subgraph CLIENT["Cliente"]
        FE["Frontend\nReact + Vite  :3000\nLocalStorage: auth_token"]
    end

    subgraph GW_BOX["API Gateway  :8000"]
        GW["FastAPI\nProxy dinamico  /api/service/path\nAuth Guard JWT  rutas protegidas\nCORS global  inyecta X-User-Id"]
    end

    subgraph SVCS["Microservicios"]
        AUTH["auth-service  :8005\nPOST /register  POST /login\nPOST /validate  GET /me\nJWT HS256  expiry 7 dias\nbcrypt password hash"]

        BIZ["business-service  :8001\nGET /  POST /  GET /:id\nPUT /:id  DELETE /:id\nGET /slug/:slug\nServiceItem  DaySchedule  slug unico\nowner_id desde X-User-Id"]

        BOOK["booking-service  :8002\nGET /  GET /slots  POST /\nGET /:id  POST /:id/cancel\nSaga Orchestrator\nOptimistic Lock  campo version\n409 Conflict si version no coincide"]

        PAY["payment-service  :8003\nPOST /  GET /:id\nGET /booking/:id\nGET /circuit-breaker/status\nCircuit Breaker\nthreshold=3  timeout=30s\nCLOSED - OPEN - HALF_OPEN"]

        AN["analytics-service  :8004\nGET /summary/:id\nGET /totals/:id\nCQRS Write + Read\nowner guard via business-service\nAnalyticsEventHandler async"]

        NOTIF["notification-service\nSin HTTP\nSubscriptor Redis\nSimula emails y logs\nbooking.created  confirmed\ncancelled  payment.completed"]
    end

    subgraph INFRA["Infraestructura  Docker Compose"]
        REDIS[("Redis  :6379\nPub/Sub\nchannel: domain_events")]
        MONGO[("MongoDB  :27017\nauth_db\nbusiness_db\nbooking_db\npayment_db\nanalytics_db")]
    end

    EXT["Payment Provider Externo\nStripe  MercadoPago\nSimulado con uuid ref"]

    %% ── Client → Gateway ──────────────────────────────────────────────
    FE -->|"HTTP REST  /api/*"| GW

    %% ── Gateway Routing (proxy dinamico) ─────────────────────────────
    GW -->|"/api/auth/*"| AUTH
    GW -->|"/api/businesses/*"| BIZ
    GW -->|"/api/bookings/*"| BOOK
    GW -->|"/api/payments/*"| PAY
    GW -->|"/api/analytics/*  JWT required"| AN
    GW -. "POST /validate\ninterno sin pasar por /api" .-> AUTH

    %% ── Sync inter-service HTTP ───────────────────────────────────────
    BOOK -->|"GET /{id}\nobtiener horario y ServiceItems"| BIZ
    AN -->|"GET /{id}\nverifica owner_id del negocio"| BIZ
    BOOK -->|"BookingSaga\nPOST /  body: booking_id amount"| PAY

    %% ── Payment → External (Circuit Breaker guard) ───────────────────
    PAY -->|"CircuitBreaker.can_execute\ncall_external_payment_provider"| EXT

    %% ── Redis Pub/Sub (async event-driven) ───────────────────────────
    BOOK -->|"EventPublisher.publish\nbooking.created\nbooking.confirmed\nbooking.cancelled"| REDIS
    PAY -->|"EventPublisher.publish\npayment.completed"| REDIS
    REDIS -->|"SUBSCRIBE domain_events\nCQRS projection"| AN
    REDIS -->|"SUBSCRIBE domain_events\nsimulated email / log"| NOTIF

    %% ── Persistence (Database per Service) ───────────────────────────
    AUTH -. "auth_db\ncol: users" .-> MONGO
    BIZ -. "business_db\ncol: businesses" .-> MONGO
    BOOK -. "booking_db\ncol: bookings" .-> MONGO
    PAY -. "payment_db\ncol: payments" .-> MONGO
    AN -. "analytics_db\ncol: events + summaries" .-> MONGO

    classDef svc fill:#1a4f6e,stroke:#0d2d3f,color:#fff
    classDef gw fill:#7b241c,stroke:#4a0e0a,color:#fff
    classDef infra fill:#6e5a1a,stroke:#3f330a,color:#fff
    classDef ext fill:#4a216e,stroke:#2a0f40,color:#fff
    classDef cli fill:#1a6e3d,stroke:#0a3f20,color:#fff

    class AUTH,BIZ,BOOK,PAY,AN,NOTIF svc
    class GW gw
    class REDIS,MONGO infra
    class EXT ext
    class FE cli
```

---

### Flujo Saga: Reserva → Pago (camino feliz y compensacion)

```mermaid
sequenceDiagram
    actor C as Cliente
    participant GW as API Gateway
    participant BOOK as booking-service
    participant BIZ as business-service
    participant REDIS as Redis
    participant PAY as payment-service
    participant EXT as Payment Provider
    participant AN as analytics-service
    participant NOTIF as notification-service

    C->>GW: POST /api/bookings
    GW->>GW: validate JWT Bearer token
    GW->>AUTH: POST /validate {Authorization: Bearer ...}
    AUTH-->>GW: 200 {user_id, email}
    GW->>GW: inject header X-User-Id
    GW->>BOOK: POST / {business_id, service_name, date, time_slot, amount}

    BOOK->>BOOK: repo.create() → status=pending  version=1
    Note over BOOK,PAY: BookingSaga.execute(booking)

    BOOK->>REDIS: PUBLISH booking.created
    REDIS-->>AN: _handle → increment total_bookings<br/>store raw event (write side)
    REDIS-->>NOTIF: log booking pending

    BOOK->>PAY: POST / {booking_id, amount}

    alt CircuitBreaker CLOSED o HALF_OPEN
        PAY->>PAY: CircuitBreaker.can_execute() → true
        PAY->>EXT: call_external_payment_provider(amount)
        EXT-->>PAY: {provider_ref: pay_xxxx, status: completed}
        PAY->>PAY: repo.create() → guardar payment en MongoDB
        PAY->>REDIS: PUBLISH payment.completed
        REDIS-->>NOTIF: log payment completed
        PAY-->>BOOK: 201 {status: completed, provider_ref}
        PAY->>PAY: circuit_breaker.record_success()

        BOOK->>BOOK: find_one_and_update {_id, version=1}<br/>→ set status=confirmed  inc version=2
        Note over BOOK: Optimistic Lock: 409 si version ya cambio

        BOOK->>REDIS: PUBLISH booking.confirmed
        REDIS-->>AN: increment confirmed_bookings + total_revenue
        REDIS-->>NOTIF: simulated email confirmacion a cliente

        BOOK-->>GW: 201 {id, status: confirmed, version: 2}
        GW-->>C: 201 Reserva confirmada

    else CircuitBreaker OPEN (3 fallos anteriores)
        PAY->>PAY: CircuitBreaker.can_execute() → false
        PAY-->>BOOK: 503 Payment service unavailable
        Note over BOOK: Compensacion (rollback saga)
        BOOK->>BOOK: find_one_and_update {_id, version=1}<br/>→ set status=cancelled  inc version=2
        BOOK->>REDIS: PUBLISH booking.cancelled
        REDIS-->>AN: increment cancelled_bookings
        REDIS-->>NOTIF: simulated email cancelacion a cliente
        BOOK-->>GW: {status: cancelled}
        GW-->>C: Reserva cancelada (pago fallido)

    else Fallo del proveedor externo
        PAY->>EXT: call_external_payment_provider(amount)
        EXT-->>PAY: Exception / timeout
        PAY->>PAY: circuit_breaker.record_failure()<br/>failure_count += 1
        PAY-->>BOOK: 502 Payment provider failed
        Note over BOOK: Compensacion identica al caso anterior
        BOOK->>BOOK: status=cancelled  version=2
        BOOK->>REDIS: PUBLISH booking.cancelled
        REDIS-->>AN: increment cancelled_bookings
        REDIS-->>NOTIF: simulated email cancelacion
        BOOK-->>GW: {status: cancelled}
        GW-->>C: Reserva cancelada (proveedor fallo)
    end
```

---

### CQRS en analytics-service

```mermaid
flowchart LR
    subgraph PRODUCERS["Productores de eventos"]
        BOOK_P["booking-service\nbooking.created\nbooking.confirmed\nbooking.cancelled"]
        PAY_P["payment-service\npayment.completed"]
    end

    REDIS[("Redis\ndomain_events")]

    subgraph AN_SVC["analytics-service"]
        EH["AnalyticsEventHandler\nasyncio task\n_listen  _handle"]

        subgraph WRITE_SIDE["Write Side  (log inmutable)"]
            WR["AnalyticsWriteRepository\nstore_event(event)"]
            EV[("analytics_db\ncol: events\nRaw event log")]
        end

        subgraph READ_SIDE["Read Side  (proyeccion agregada)"]
            RR["AnalyticsReadRepository\nincrement_summary()\nincrement_service_count()\nget_summary()  get_totals()"]
            SU[("analytics_db\ncol: summaries\nbusiness_id + date\ntotal_bookings\nconfirmed_bookings\ncancelled_bookings\ntotal_revenue\nbookings_by_service{}")]
        end
    end

    subgraph QUERIES["Consultas  (read-optimized)"]
        API_AN["GET /summary/:id\nGET /totals/:id\nowner guard via HTTP\nbusiness-service"]
    end

    BOOK_P -->|"PUBLISH"| REDIS
    PAY_P -->|"PUBLISH"| REDIS
    REDIS -->|"SUBSCRIBE asyncio"| EH
    EH -->|"store raw event"| WR
    WR --> EV
    EH -->|"update counters\nno toca events"| RR
    RR --> SU
    API_AN -->|"query directo\nnunca toca events"| RR

    classDef write fill:#1a5276,stroke:#0d2d40,color:#fff
    classDef read fill:#145a32,stroke:#0a3318,color:#fff
    classDef infra fill:#6e5a1a,stroke:#3f330a,color:#fff
    classDef svc fill:#4a1a6e,stroke:#280a3f,color:#fff

    class WR,EV write
    class RR,SU read
    class REDIS infra
    class EH,API_AN svc
```

---

### Circuit Breaker en payment-service

```mermaid
stateDiagram-v2
    [*] --> CLOSED

    CLOSED --> CLOSED : record_success\nfailure_count = 0
    CLOSED --> OPEN : record_failure\nfailure_count >= threshold (3)

    OPEN --> OPEN : can_execute = false\nHTTP 503 inmediato\nsin llamar al proveedor
    OPEN --> HALF_OPEN : time.time() - last_failure_time >= 30s

    HALF_OPEN --> CLOSED : record_success\nuna llamada de prueba exitosa\nfailure_count = 0
    HALF_OPEN --> OPEN : record_failure\nprueba fallo\nlast_failure_time actualizado
```
