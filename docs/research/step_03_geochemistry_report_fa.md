# استپ تحقیق ۳ — ژئوشیمی نی‌ریز و کرومیتیت‌ها

## نتیجه تأییدشده

داده ژئوشیمی واقعی و عمومی برای افیولیت نی‌ریز وجود دارد. مجموعه اصلی از Figshare متعلق به Stern و همکاران است و با DOI `10.6084/m9.figshare.1132662.v1` منتشر شده است. شش فایل شامل شیمی کانی‌ها، عناصر کمیاب و عناصر نادر خاکی کلینوپیروکسن، شیمی سنگ کامل سنگ‌های مافیک و اولترامافیک، ایزوتوپ‌های Sr–Nd–Pb و روش‌های آزمایشگاهی در پروژه ذخیره شده‌اند. فایل‌ها از endpointهای عمومی به‌صورت جداگانه دریافت و checksumهای MD5 آن‌ها با API ناشر تطبیق داده شده‌اند. مجوز مجموعه CC BY 4.0 است.

یک منبع عمومی دیگر، مقاله Attarzadeh و همکاران درباره کرومیتیت‌های شرق افیولیت نی‌ریز است. جدول مقاله ۱۶ نمونه با شناسه‌های D.T.1 تا D.T.16 و مقادیر شیمیایی از جمله Cr2O3 را ارائه می‌کند.

## محدودیت تعیین‌کننده

هیچ‌یک از منابع بررسی‌شده برای نمونه‌های منتشرشده، عرض و طول جغرافیایی، UTM، CRS یا پلیگون AOI ارائه نمی‌کند. بنابراین فایل‌های واقعی ژئوشیمی در این نسخه به‌عنوان **داده جدولی مرجع** ذخیره شده‌اند و به نقطه GIS یا رستر پیوسته تبدیل نشده‌اند. نسبت‌دادن مختصات از نام نمونه یا توصیف منطقه‌ای ممنوع است.

پرتال رسمی NGDIR/GSI در این محیط قابل دسترسی و راستی‌آزمایی نبود. GEOROC نیز به کلید API صادرشده از ارائه‌دهنده نیاز دارد و رکورد اختصاصی نی‌ریز از آن استخراج نشده است. بنابراین هیچ داده رسمی یا GEOROC فرضی به پروژه اضافه نشده است.

## اثر بر مدل

دروازه ژئوشیمی از نظر وجود داده مرجع عمومی بهتر شده، اما برای مدل مکانی همچنان `BLOCKED` است. برای ورود واقعی به مدل باید محل نمونه‌ها از نویسندگان، فایل رسمی یا برداشت مجاز مستقل دریافت شود. پس از آن، روش، آزمایشگاه، واحد، حد تشخیص و QA/QC باید ثبت شود.

## فایل‌های اضافه‌شده

- `data/acquired/research_step_03_geochemistry/figshare_files/`: شش فایل اصلی Figshare شامل پنج جدول و یک فایل روش‌ها؛
- `supplementary_inventory.txt`؛
- `figshare_individual_inspection.txt`؛
- اسکریپت‌های دریافت و بررسی؛
- `sha256.txt`؛
- گزارش نتیجه تحقیق و وضعیت دسترسی.

## منابع

[1]: https://tandf.figshare.com/articles/dataset/Supra_subduction_zone_magmatism_of_the_Neyriz_ophiolite_Iran_constraints_from_geochemistry_and_Sr_Nd_Pb_isotopes/1132662 "Taylor & Francis Figshare Neyriz ophiolite geochemistry dataset"
[2]: https://api.figshare.com/v2/articles/1132662 "Figshare public API record"
[3]: https://file.scirp.org/Html/1-1210741_74691.htm "Attarzadeh et al. 2017 eastern Neyriz chromitites"
[4]: https://www.uni-goettingen.de/en/georoc+database/643472.html "GEOROC database official description"
[5]: https://www.ngdir.ir/ "National Geoscience Database of Iran"
