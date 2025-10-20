# Extended Features

Розширення базової моделі дозволяють досліджувати складні явища нейром'язової передачі.

## Stochastic Reliability
- Параметри: `noise_sigma`, `failure_bias`.
- Додає стохастичні зриви передачі та коливання латентності.
- Метрики: `failure_rate`, `jitter_ms`, `latency_cv`, `cv_force`.

## Mechano-sensitivity
- Параметр `topography_factor` моделює неоднорідність м'язових волокон.
- Змінює просторову карту чутливості, впливає на формування сили.
- Можна комбінувати з датчиками натягу для біомеханічних експериментів.

## Tripartite Modulation
- Гліальний модуль вводить коефіцієнт `glial_gain`.
- Модифікує вивільнення гістаміну залежно від історії активності.
- Доступні режими: `static`, `activity-coupled`, `fatigue-aware`.

## Приклади CLI
```bash
neuromotorica simulate-extended \
  --seconds 1.5 \
  --rate 20 \
  --noise-sigma 0.05 \
  --glial-gain 0.25 \
  --topography 1.2 \
  --failure-bias 0.15
```

## Інтеграція з API
- Поле `extended=true` в `POST /policy/outcome` сигналізує збереження розширених метрик.
- Відповідь містить рекомендації з урахуванням стохастики.

## Валідація Extended режиму
- Для шумових досліджень використовуйте тест `tests/extended/test_noise.py`.
- Порівнюйте розподіли сили через `neuromotorica analyze --distribution force`.
