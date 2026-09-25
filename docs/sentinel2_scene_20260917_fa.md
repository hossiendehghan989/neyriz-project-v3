# Sentinel-2 کم‌ابر نی‌ریز — صحنهٔ L2A مورخ ۱۷ سپتامبر ۲۰۲۶

## نتیجهٔ جست‌وجوی کاتالوگ

صحنهٔ زیر با STAC رسمی [Copernicus Data Space Ecosystem](https://stac.dataspace.copernicus.eu/v1/) و کاتالوگ عمومی [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/api/stac/v1/) پیدا و شناسهٔ همان محصول در هر دو کاتالوگ تطبیق داده شد:

- شناسه: `S2C_MSIL2A_20260917T065621_R063_T40RBT_20260917T121802`
- مجموعه: `sentinel-2-l2a`، سطح L2A
- مأموریت/ماهواره: Copernicus Sentinel-2C
- زمان برداشت: `2026-09-17T06:56:21.025Z`
- کاشی MGRS: `T40RBT`؛ CRS تصویر اصلی: `EPSG:32640`
- ابرناکی کل کاشی طبق `eo:cloud_cover`: **۰٫۱۴۹۱۵۷٪**
- footprint کاشی تمام AOI فعلی را می‌پوشاند.
- اعلامیهٔ حقوق Sentinel: [Sentinel Data Legal Notice](https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice)

### سنجش ابر در خود AOI

عدد ابر کاتالوگ مربوط به کاشی بزرگ Sentinel است، نه فقط محدودهٔ نی‌ریز. به همین دلیل پیش از پذیرش، فایل SCL (Scene Classification Layer) از محصول باز شد و شمارش پیکسل روی AOI دقیق انجام شد:

- پیکسل‌های ۲۰ متری در AOI: **۲٬۲۱۰٬۳۸۵**
- کلاس‌های SCL: ۲ (سایه/ناحیهٔ تاریک) ۱۱٬۳۶۶؛ ۴ (پوشش گیاهی) ۷٬۲۴۴؛ ۵ (سطح برهنه) ۲٬۱۹۰٬۹۵۷؛ ۷ (نامشخص) ۸؛ ۸ (ابر با احتمال متوسط) ۷۸۹؛ ۹ (ابر با احتمال بالا) ۲۱.
- ابر/سایه/سیروس، طبق کلاس‌های SCL `3, 8, 9, 10`: **۰٫۰۳۶۶۴۵٪**.
- کلاس‌های سطح قابل‌مشاهدهٔ بدون پوشش ابر طبق تعریف این کنترل، `4, 5, 6`: **۹۹٫۴۴۸۷۸۴٪**.

این اعداد فقط غربال کیفیت ابری‌اند؛ تضمین نبود haze، غبار، سایهٔ توپوگرافی، خطای طبقه‌بندی یا مشکل رادیومتریک نیستند.

## دادهٔ موجود در ریپو

| فایل | باند/کلاس | اندازهٔ پیکسل |
|---|---|---:|
| `data/remote_sensing/sentinel2/2026-09-17/sentinel2_spectral_10m.tif` | B02, B03, B04, B08 | ۱۰ متر |
| `data/remote_sensing/sentinel2/2026-09-17/sentinel2_spectral_20m.tif` | B05, B06, B07, B8A, B11, B12 | ۲۰ متر |
| `data/remote_sensing/sentinel2/2026-09-17/sentinel2_scl_20m.tif` | کلاس‌های اصلی SCL | ۲۰ متر |
| `data/remote_sensing/sentinel2/2026-09-17/sentinel2_clear_surface_mask_20m.tif` | ۱=کلاس ۴/۵/۶، ۰=سایر پیکسل‌های داخل AOI، ۲۵۵=بیرون AOI/NoData | ۲۰ متر |
| `data/acquired/sentinel2/S2C_MSIL2A_20260917T065621_R063_T40RBT_20260917T121802.json` | فرادادهٔ عمومی STAC، بدون URL امضاشده | — |
| `data/remote_sensing/remote_sensing_manifest.csv` | provenance، وضعیت QC و SHA-256 محصولات | — |
| `outputs/validation/sentinel2_scene_manifest.json` | گزارش machine-readable تنظیمات/QC/خروجی | — |

دسترسی داده از COGهای عمومی با SAS موقت Planetary Computer انجام می‌شود. **SAS token و URL امضاشده داخل ریپو نگهداری نمی‌شوند.** باندها فقط روی AOI بریده شده‌اند؛ مقدارهای quantized L2A بدون scale/offset به‌عنوان DN حفظ شده‌اند.

## بازتولید دریافت و برش

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-geospatial.txt
make sentinel2 PYTHON=.venv/bin/python
.venv/bin/python scripts/validate_sentinel2_outputs.py
```

اسکریپت، صحنه را از شناسهٔ ثابت کاتالوگ می‌گیرد، از وجود باندها و footprint، CRS و تفکیک مکانی کنترل می‌گذرد و حدود ابرناکی را بررسی می‌کند؛ اگر کنترل شکست بخورد خروجی معتبر ثبت نمی‌شود. manifest STAC ذخیره‌شده metadata عمومی بدون SAS است.

## محدودیت استفاده

- AOI فعلی از شواهد موجود ساخته شده و یک **پوشش مستطیلی موقت** است؛ مرز حقوقی/کاداستر/مجوز نیست. برای کاربرد مجاز و دقیق باید AOI رسمی و CRSدار جایگزین شود.
- این اقدام صحنه را پیدا، کنترل، clip و نسخه‌بندی می‌کند؛ **شاخص دگرسانی یا کانه‌زایی محاسبه نشده است**.
- کد مقیاس/offset بازتاب را اعمال نکرده، cloud-fill، terrain illumination correction، atmospheric reprocessing یا compositing زمانی انجام نداده است.
- هیچ باند یا شاخصی به امتیاز اهداف منگنز اضافه نشده؛ `model_integration=NOT_APPLIED`.
- برای تحلیل زمین‌شناسی/اکتشاف، پردازش طیفی باید با کالیبراسیون صحیح محصول، کنترل اثر توپوگرافی و گردوغبار، نقشهٔ زمین‌شناسی معتبر، بازبینی متخصص و برچسب‌های مستقل انجام شود. داشتن تصویر به‌تنهایی دقت مدل را اثبات نمی‌کند.
