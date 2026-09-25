# پروژه پتانسیل‌سنجی چندماده‌ای نی‌ریز — نسخه ۳.۱

این ریپو یک **workflow بازتولیدپذیر برای غربالگری اکتشافی** است؛ نه سامانهٔ اثبات معدن، ذخیره، عیار، دقت مدل یا وضعیت حقوقی. مدل منگنز فعلاً دانش‌محور و در سطح غربالگری است؛ مدل‌های کرومیت و آهن تا دریافت دادهٔ مکانی و آزمون مستقل، عمداً مسدود هستند.

> **مرز علمی و حقوقی:** امتیاز منگنز فقط اولویت بررسی است. خروجی هیچ‌گاه به‌معنای احتمال، ذخیره، عیار، «معدن ثبت‌نشده»، مجوز دسترسی یا آزادی کاداستری نیست.

## وضعیت عملیاتی

| جزء | وضعیت | کنترل اصلی |
|---|---|---|
| مدل غربالگری منگنز | فعال، ۱۰ هدف | `data_confidence_score <= 30` و `SCREENING_ONLY` |
| مدل کرومیت و آهن | مسدود | نبود دادهٔ مکانی مستقل و آزمون اعتبارسنجی |
| ASTER GDEM V003 | فعال، ۹ تایل کنترل‌شده | SHA-256 برای همهٔ ورودی‌ها |
| مشتقات توپوگرافی نسخه ۳.۱ | فعال | CRS متریک، ۳۰ متر، manifest و اعتبارسنجی خروجی |
| Sentinel-2، زمین‌شناسی رسمی، ژئوشیمی، ژئوفیزیک، کاداستر | هنوز ورودی عملیاتی نیست | evidence gates |
| اعتبارسنجی مستقل مکانی | مسدود | حداقل ۲۰ برچسب، از جمله ۱۰ آزمون مستقل |

## شروع سریع

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-geospatial.txt
make ci PYTHON=.venv/bin/python
```

برای مشاهدهٔ همهٔ فرمان‌ها:

```bash
make help
```

### اجرای مرحله DEM

```bash
make terrain PYTHON=.venv/bin/python
```

این فرمان با کنترل SHA-256، ۶ مشتق توپوگرافی را می‌سازد و برای ۱۰ هدف منگنز فعلی sample می‌گیرد. خروجی‌ها به‌صورت صریح `NOT_APPLIED` برچسب می‌خورند؛ بنابراین اجرای آن رتبه یا امتیاز مدل را تغییر نمی‌دهد.

برای AOI تأییدشده:

```bash
.venv/bin/python scripts/build_terrain_derivatives.py \
  --aoi-file data/incoming/approved_aoi.geojson
```

جزئیات روش، فرمول‌ها، کنترل کیفیت و شرط ورود DEM به مدل در [`docs/terrain_workflow_v31_fa.md`](docs/terrain_workflow_v31_fa.md) آمده است.

## ترتیب اجرای استاندارد

```bash
.venv/bin/python scripts/merge_project_inputs.py
.venv/bin/python scripts/build_multicommodity_prospectivity.py
.venv/bin/python scripts/build_maps.py
.venv/bin/python scripts/build_terrain_derivatives.py
.venv/bin/python scripts/validate_data_provenance.py
.venv/bin/python scripts/validate_evidence_gates.py
.venv/bin/python scripts/evaluate_independent_validation.py
.venv/bin/python scripts/evaluate_spatial_validation.py
.venv/bin/python scripts/validate_project.py
.venv/bin/python scripts/validate_terrain_outputs.py
```

GitHub Actions همین قرارداد را روی Python 3.12 اجرا می‌کند.

## خروجی‌های اصلی

| خروجی | محتوا |
|---|---|
| `outputs/tables/manganese_targets.csv` | ده هدف غربالگری منگنز؛ وضعیت حقوقی `NOT_VERIFIED` |
| `outputs/tables/manganese_targets_terrain_v31.csv` | ویژگی‌های terrain برای همان ده هدف؛ فقط بررسی، نه مدل‌سازی |
| `data/processed/terrain/*.tif` | ارتفاع، شیب، جهت، انحنا، ناهمواری و سایه‌روشن در EPSG:32640 |
| `outputs/validation/terrain_run_manifest_v31.json` | provenance، checksum، تنظیمات و آمار تولید مشتقات |
| `outputs/validation/*.json` | وضعیت evidence gates و کنترل اعتبارسنجی |
| `docs/final_report_fa_v3.md` | گزارش فنی نسخه ۳ |
| `docs/terrain_workflow_v31_fa.md` | راهنمای اجرایی DEM نسخه ۳.۱ |
| `docs/user_action_required_fa.md` | داده‌ها و اقدام‌های ضروری کاربر/تیم میدانی |

## دروازه‌های تصمیم‌گیری

تا وقتی همهٔ موارد زیر فراهم نشده‌اند، ادعای دقت، احتمال، calibration یا تغییر وزن مدل مجاز نیست:

1. نقشهٔ زمین‌شناسی/GIS با منبع، CRS و مجوز روشن؛
2. Sentinel-2 یا داده سنجش‌ازدور مناسب با checksum و کنترل ابر؛
3. حداقل ۲۰ نمونه ژئوشیمی واقعی با standard، blank و duplicate QA/QC؛
4. داده ژئوفیزیک محلی قابل ممیزی، در صورت نیاز مدل کانساری؛
5. خروجی رسمی و تاریخ‌دار کاداستر؛
6. حداقل ۲۰ برچسب مکانی با حداقل ۱۰ مورد `independent_test` جدا از آموزش؛
7. ارزیابی مکانی مستقل شامل `precision@k`، recall، PR-AUC و بازه اطمینان.

## ساختار و حاکمیت داده

- دادهٔ محلی و حساس ابتدا در `data/incoming/` قرار می‌گیرد و توسط Git نادیده گرفته می‌شود.
- فقط داده‌ای با provenance، مجوز و metadata کامل وارد مسیرهای نسخه‌بندی‌شده می‌شود.
- تایل‌های DEM منبع در Git هستند و checksum آن‌ها در manifest کنترل می‌شود.
- خروجی‌های داده‌شده در repository قابل بازتولیدند؛ `.venv/`، credentials و logs هرگز commit نمی‌شوند.

## اقدام بعدی پیشنهادی

خروجی DEM اکنون آمادهٔ **بازبینی زمین‌شناس** است. گام بعدی، ورود نقشه رسمی زمین‌شناسی ورقه ۶۸۴۸ و Sentinel-2 کم‌ابر با metadata و checksum است؛ سپس فقط در صورت وجود برچسب مستقل، باید آزمون ablation برای سنجش ارزش افزودهٔ terrain طراحی شود.
