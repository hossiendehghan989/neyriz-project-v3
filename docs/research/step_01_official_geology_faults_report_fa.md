# استپ تحقیق ۱ — زمین‌شناسی و گسل‌های رسمی نی‌ریز

## نتیجه تأییدشده

یک سرویس واقعی و قابل‌دسترسی WMS از لایه‌های GSI/NGDIR برای زمین‌شناسی بستر و گسل‌های ایران پیدا و در محدوده نی‌ریز آزمایش شد. لایه‌های `IRN_GSI_1M_BG` و `IRN_GSI_1M_MSF` در مقیاس اسمی ۱:۱٬۰۰۰٬۰۰۰ هستند و برای محدوده نی‌ریز تصویر غیرتهی تولید کردند.

سرویس با GetCapabilities و GetMap بررسی شده و فایل XML قابلیت‌ها و دو تصویر خروجی در پوشه `data/acquired/research_step_01_geology_faults/` ذخیره شده‌اند. این داده برای زمینه منطقه‌ای و کنترل کیفی مناسب است، اما جایگزین نقشه دقیق ۱:۱۰۰٬۰۰۰ یا لایه برداری محلی نیست.

## منبع و محدودیت

سرویس GSI/NGDIR یک WMS نقشه‌ای است و در متادیتای بررسی‌شده WFS یا دانلود برداری کامل ارائه نمی‌کند. بنابراین تصویر WMS را به‌عنوان شیپ‌فایل یا هندسه دقیق گسل وارد مدل نکرده‌ام. شرایط استفاده، حق نشر GSI و لزوم ارجاع باید رعایت شود.

داده USGS مربوط به گسل‌های عمده ایران نیز به‌عنوان منبع عمومی شناسایی شد. این داده EPSG:4326 دارد، اما از نقشه‌های بسیار تعمیم‌یافته با خطای مکانی کیلومتری ساخته شده است. رکورد رسمی و URL فایل‌ها ثبت شد، ولی دانلود باینری در این محیط با چالش Cloudflare مواجه شد؛ بنابراین فایل شیپ‌فایل به‌دروغ به‌عنوان دانلودشده در پروژه قرار نگرفت.

## اثر بر مدل

این استپ وضعیت «منبع رسمی قابل مشاهده» را بهتر می‌کند، اما امتیاز منگنز فعلی همچنان از خطوط تقریبی پروژه استفاده می‌کند. برای جایگزینی آن‌ها باید لایه برداری دقیق، مجوز استفاده و کنترل مقیاس دریافت شود.

## فایل‌های پیوست‌شده

- `gsi_wms_getcapabilities.xml`
- `IRN_GSI_1M_BG_neyriz.png`
- `IRN_GSI_1M_MSF_neyriz.png`
- `get_neyriz_wms.sh`
- `check_ogc.sh`
- `metadata_extract.txt`
- `step_01_official_geology_faults_evidence.md`

## منابع

[1]: https://gsi.ir/en "Geological Survey and Mineral Exploration of Iran"
[2]: https://ogc.bgs.ac.uk/cgi-bin/BGS_GSI_EN_Bedrock_and_Structural_Geology/ows?language=eng&service=WMS&request=GetCapabilities&version=1.3.0 "GSI/NGDIR bedrock and structural geology WMS capabilities"
[3]: https://doi.org/10.5066/P9TMSOQ0 "USGS Major faults in Iran"
