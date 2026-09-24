# پروژه ارتقایافته پتانسیل‌سنجی چندماده‌ای نی‌ریز — نسخه ۳

این نسخه دو بسته ورودی قبلی را ادغام می‌کند و خروجی‌های جداگانه برای منگنز، کرومیت و آهن فراهم می‌سازد. منگنز در سطح غربالگری دانش‌محور اجرا شده است. کرومیت و آهن به دلیل نبود داده مکانی مستقل و آزمون اعتبارسنجی، عمداً مسدود مانده‌اند.

## وضعیت علمی

این پروژه معدن، ذخیره، عیار، احتمال آماری یا وضعیت حقوقی را اثبات نمی‌کند. امتیاز منگنز فقط اولویت بررسی است. عبارت «معدن ثبت‌نشده» مجاز نیست، زیرا کاداستر رسمی تاریخ‌دار و پاسخ حقوقی در بسته موجود نیست.

## اجرا

```bash
python3 scripts/merge_project_inputs.py
python3 scripts/build_multicommodity_prospectivity.py
python3 scripts/build_maps.py
python3 scripts/validate_data_provenance.py
python3 scripts/validate_evidence_gates.py
python3 scripts/evaluate_independent_validation.py
python3 scripts/validate_project.py
```

## خروجی‌های اصلی

- `docs/final_report_fa_v3.md`: گزارش نهایی فارسی
- `docs/data_gaps_and_next_steps_fa.md`: شکاف داده و اولویت بعدی
- `docs/field_validation_plan_fa.md`: برنامه اعتبارسنجی میدانی
- `outputs/tables/manganese_targets.csv`: ده هدف غربالگری منگنز
- `outputs/tables/chromite_targets.csv`: خالی؛ مدل کرومیت مسدود است
- `outputs/tables/iron_targets.csv`: خالی؛ مدل آهن مسدود است
- `data/processed/*.geojson`: لایه‌های مکانی WGS84
- `outputs/validation/*.json`: وضعیت دروازه‌ها و آزمون مستقل

## خلأ مهم

استپ ۶ در بسته‌های ورودی حاضر وجود نداشت و در `outputs/tables/merge_manifest.json` ثبت شده است. داده واقعی سنجش‌ازدور، ژئوشیمی QA/QC، ژئوفیزیک محلی، کاداستر رسمی و برچسب آزمون مستقل نیز هنوز فراهم نشده‌اند.
