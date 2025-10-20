# REST API

`neuromotorica run-api` розгортає FastAPI-сервіс для персоналізації протоколів тренувань.

## Аутентифікація
- За замовчуванням використовує токени, згенеровані через CLI `neuromotorica create-token`.
- У продакшн-середовищі рекомендується інтегрувати OAuth2/OIDC.

## Ендпоінти
### `POST /policy/outcome`
- **Призначення**: запис результату чергової підказки та оновлення моделі користувача.
- **Тіло запиту**:
  ```json
  {
    "user_id": "athlete-42",
    "exercise_id": "isometric-elbow-flexion",
    "reps": 10,
    "success": true,
    "metrics": {"twitch": 0.41, "snr": 18.2},
    "extended": false
  }
  ```
- **Відповідь**: підтвердження запису, оновлені агрегати.

### `GET /policy/best/{user_id}/{exercise_id}`
- **Призначення**: отримати топ-`k` рекомендацій (Laplace-smoothed).
- **Параметри**: `k` (за замовчуванням 3), `profile` (`healthy`, `myasthenia`, ...).
- **Відповідь**:
  ```json
  {
    "user_id": "athlete-42",
    "exercise_id": "isometric-elbow-flexion",
    "recommendations": [
      {"cue": "stabilize scapula", "score": 0.82},
      {"cue": "slow concentric", "score": 0.77}
    ]
  }
  ```

## Документація API
- Swagger/OpenAPI доступні на `/docs`.
- JSON Schema — `/openapi.json`.

## Режими розгортання
- **Локально**: `neuromotorica run-api --host 0.0.0.0 --port 8000`.
- **Docker**: `docker compose up api` (див. `docker-compose.yml`).
- **Kubernetes**: використовуйте готовий `helm`-чарт із параметрами ресурсів (CPU/GPU).

## Моніторинг
- Метрики Prometheus за адресою `/metrics` (експортуються через `prometheus_fastapi_instrumentator`).
- Логи у форматі JSON сумісні з ELK/Datadog.
