# Модель
- **NMJ (ACh)** — normalized alpha kernel (стабільна нормалізація), low-pass, кліп [0,1].
- **EnhancedNMJ (ACh+Hist)** — сумарна активація з підсиленням, кліп [0,1.5].
- **OptimizedEnhancedNMJ** — zero-phase biquad + нелінійна взаємодія ACh×Hist, кліп [0,1.2].
- **Muscle** — MU масштабування, сила-довжина/швидкість, пасив.
