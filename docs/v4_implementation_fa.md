# تغییرات فنی نسخه ۴ نی‌ریز

## انجام‌شده

- tile واقعی ASTER GDEM موجود در ریپو به pipeline وصل شد.
- برای ۳۵۷ سلول شبکه، featureهای `elevation_m`، `slope_deg` و `relief_m_local` محاسبه شد.
- خروجی `data/processed/manganese_topography_features.geojson` تولید شد.
- ده هدف قبلی به polygonهای نسخه چهار در `data/processed/manganese_targets_v4.geojson` تبدیل شدند.
- جدول `outputs/tables/manganese_targets_v4.csv` با featureهای توپوگرافی تولید شد.
- برای هر هدف، `model_version`، پوشش DEM و منبع feature ثبت شده است.
- manifest سنجش‌ازدور با checksum واقعی DEM در `data/remote_sensing/remote_sensing_manifest.csv` ساخته شد.
- قالب‌های استاندارد ژئوشیمی، ژئوفیزیک، کاداستر و برچسب مستقل اضافه شدند.
- اسکریپت `prepare_spatial_validation.py` برای بررسی قرارداد آزمون مستقل اضافه شد.
- نقشه تعاملی polygonهای نسخه چهار در `outputs/maps/manganese_targets_v4_map.html` تولید می‌شود.

## محدودیت علمی باقی‌مانده

Featureهای DEM فعلاً برای تحلیل و آماده‌سازی داده تولید شده‌اند و به‌تنهایی وزن جدیدی به امتیاز منگنز نداده‌اند؛ چون بدون برچسب‌های مستقل، وزن‌دهی جدید می‌تواند overfit یا ظاهراً دقیق باشد. برای آموزش واقعی باید داده ژئوشیمی و test مکانی مستقل وارد شود.

همچنین این tile فقط بخشی از پوشش DEM موردنیاز را پوشش می‌دهد و DEM به‌تنهایی شاهد کانه‌زایی نیست.

## اجرای بازتولیدپذیر

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt rasterio
.venv/bin/python scripts/build_v4_topography.py
.venv/bin/python scripts/build_maps.py
.venv/bin/python scripts/prepare_spatial_validation.py
.venv/bin/python scripts/validate_evidence_gates.py
```

پس از ورود داده واقعی، ابتدا `prepare_spatial_validation.py` و سپس ارزیابی مستقل اجرا شود. تا قبل از آن، هرگونه precision یا ادعای دقت بالا باید blocked بماند.
