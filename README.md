# link2filesir
لینک مستقیم دانلود بده، GitHub Actions فایل رو دانلود می‌کنه، با API توکن توی **Files.ir** آپلود می‌کنه و لینک اشتراک عمومی تحویل می‌ده.

## راه‌اندازی
1. توی my.files.ir برو **تنظیمات حساب ← توسعه‌دهندگان** و یه Personal Access Token (با `pat_` شروع میشه) بساز.
2. این ریپو رو روی GitHub push کن (ترجیحاً **private**).
3. **Settings ← Secrets and variables ← Actions ← New repository secret**
   - نام: `FILESIR_TOKEN`
   - مقدار: توکنت
4. تب **Actions ← Link to Files.ir ← Run workflow** رو بزن و لینک رو وارد کن (اسم فایل و id پوشه اختیاری‌ان).
5. لینک Files.ir توی **Summary** همون Run نشون داده میشه.

## اجرای محلی
```bash
pip install -r requirements.txt
export FILESIR_TOKEN=pat_xxxxxxxx
python uploader.py "https://example.com/file.zip" --parent-id 123
```

## نکته‌ها
- آپلود با کتابخونه غیررسمی [aiofilesir](https://github.com/loopy-iri/aiofilesir) انجام میشه که فایل‌های بزرگ رو هم تکه‌تکه (multipart/tus) می‌فرسته.
- توکن رو هیچ‌وقت توی کد commit نکن، فقط توی Secret بذارش.
- دیسک runner گیت‌هاب حدود ۱۴ گیگه و هر job حداکثر ۶ ساعت وقت داره.
- اگه Files.ir آی‌پی خارجی رو محدود کنه، روی سیستم یا سرور داخل ایران اجرا کن (self-hosted runner).
