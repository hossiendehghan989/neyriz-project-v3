# منابع و روش استپ ۳

## منابع گسل/ساختار

- Oskooi et al. (2015), *A Magnetotelluric Survey of Ophiolites in the Neyriz area of southwestern Iran*: https://link.springer.com/article/10.1007/s00024-014-0925-5
  - پهنه گسلی با روند NW–SE را گزارش می‌کند که افیولیت نیریز را از زون سنندج–سیرجان جدا می‌کند.
- Sarkarinejad, *Structural analysis in the Neyriz ophiolite* / شکل نقشه ساختاری: https://www.researchgate.net/figure/Geological-map-of-the-Neyriz-ophiolite-with-its-major-dextral-shear-zone-The-area-is_fig2_248352863
  - پهنه برشی راست‌بر/ترانسفورم قدیمی افیولیت نیریز را در حدود 12 کیلومتری شمال‌غرب نیریز معرفی می‌کند.
- Sarkarinejad et al. (2003), *Structural and microstructural analysis of a palaeo-transform fault zone in the Neyriz ophiolite*: https://www.lyellcollection.org/doi/10.1144/GSL.SP.2003.218.01.08
- IIEES, *Updated Fault Map of Iran*: https://www.iiees.ac.ir/en/updated-fault-map-of-iran/
  - منبع رسمی/نهادی برای نقشه گسل‌های فعال ایران و توضیح دسترسی به فایل‌های دیجیتال؛ فایل محلی با هندسه نیریز از این صفحه قابل استخراج مستقیم نبود.
- USGS, *Major faults in Iran (flt2cg)*: https://data.usgs.gov/datacatalog/data/USGS:60a82961d34ea221ce4e607a
  - منبع عمومی ملی/منطقه‌ای، اما داده آن برای هندسه محلی هدف در این استپ به‌صورت مستقیم استخراج نشد.

## روش محاسباتی

دو خط تقریبی از توصیف‌های علمی و روندهای منتشرشده ساخته شد. همه خطوط و عوارض با `precision_class=B` ثبت شده‌اند. بافرها در سیستم متریک UTM zone 40N / EPSG:32640 با فاصله‌های ۱ و ۲ کیلومتر محاسبه شدند و سپس به WGS 84 / EPSG:4326 برگردانده شدند. اهداف در `exploration_targets_step03.geojson` از تقاطع بافرها با `host_lithology_units.geojson` استپ ۲ تولید شده‌اند.

این خروجی جایگزین لایه رسمی گسل یا نقشه زمین‌شناسی رقومی نیست. با توجه به اینکه هندسه میزبان در استپ ۲ نیز غربالگری و `precision_class=B` است، تمام اهداف این استپ برای مدل‌سازی اولیه‌اند و قبل از استفاده نهایی باید با GIS رسمی/نقشه ژئورفرنس‌شده و کنترل صحرایی بازبینی شوند.
