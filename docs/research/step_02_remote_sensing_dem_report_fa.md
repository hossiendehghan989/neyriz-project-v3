# استپ تحقیق ۲ — Sentinel‑2، ASTER و DEM

## نتیجه تأییدشده

کاتالوگ زنده Copernicus برای محدوده آزمایشی نی‌ریز رکوردهای واقعی Sentinel‑2 L2A و L1C دارد. یک رکورد مشخص با شناسه `S2B_MSIL2A_20241231T070219_N0511_R063_T40RBT_20241231T091815` بررسی شد. این صحنه محدوده نی‌ریز را پوشش می‌دهد، EPSG:32640 دارد و باندهای JP2 با تفکیک ۱۰، ۲۰ و ۶۰ متر ارائه می‌کند.

**به‌روزرسانی ۲۵ سپتامبر ۲۰۲۶:** بررسی بالا مربوط به رکورد تاریخی ۲۰۲۴ است. پس از آن، صحنهٔ کم‌ابر `S2C_MSIL2A_20260917T065621_R063_T40RBT_20260917T121802` از STAC بازیابی، روی evidence-envelope فعلی clip، کنترل SCL و checksum شده است. فایل‌ها در `data/remote_sensing/sentinel2/2026-09-17/` هستند؛ شاخص طیفی و مدل هنوز آن را مصرف نمی‌کنند. جزئیات QC در [`docs/sentinel2_scene_20260917_fa.md`](../sentinel2_scene_20260917_fa.md) آمده است.

با این حال، ابرناکی صحنه مشخص‌شده ۹۹٫۹۱ درصد است. بنابراین این رکورد فقط دسترسی و پوشش داده را اثبات می‌کند و نباید به‌عنوان تصویر تحلیلی مناسب وارد مدل شود. دانلود محصول و دارایی‌های آن به حساب رایگان CDSE و توکن OIDC نیاز دارد.

برای ارتفاع نیز رکورد واقعی ASTER GDEM V3 با شناسه `ASTGTMV003_N29E054` پیدا شد. این کاشی محدوده نی‌ریز را پوشش می‌دهد و فایل‌های `dem.tif` و `num.tif` دارد. داده ASTER حدود ۳۰ متر است، اما دانلود باینری از LP DAAC به حساب Earthdata نیاز دارد. در این پروژه فقط متادیتا و رکورد کاتالوگ ذخیره شده و فایل DEM ادعا نشده است.

## اثر بر مدل

این استپ ثابت می‌کند داده عمومی واقعی برای افزودن سنجش‌ازدور و توپوگرافی وجود دارد، اما هنوز رسترهای باینری در پروژه نیستند. پس دروازه سنجش‌ازدور عملیاتی همچنان تا دریافت فایل، checksum، ماسک ابر و کنترل کیفیت `BLOCKED` باقی می‌ماند.

## فایل‌های پیوست‌شده

- `stac_item_compact.json`
- `extract_stac.py`
- `research_steps_sha256.txt`

## منابع و نقاط دسترسی

[1]: https://stac.dataspace.copernicus.eu/v1/search?collections=sentinel-2-l2a&bbox=54.20%2C29.10%2C54.50%2C29.35&datetime=2024-01-01T00%3A00%3A00Z%2F2024-12-31T23%3A59%3A59Z&limit=10 "Copernicus live Sentinel-2 L2A search for Neyriz AOI"
[2]: https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items/S2B_MSIL2A_20241231T070219_N0511_R063_T40RBT_20241231T091815 "Concrete Sentinel-2 L2A item covering Neyriz"
[3]: https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C1711961296-LPCLOUD&producer_granule_id=ASTGTMV003_N29E054 "NASA CMR ASTER GDEM V3 tile metadata"
[4]: https://www.earthdata.nasa.gov/data/catalog/lpcloud-astgtm-003 "NASA ASTER GDEM V3 catalog"
[5]: https://documentation.dataspace.copernicus.eu/APIs/Token.html "Copernicus Data Space access-token documentation"
