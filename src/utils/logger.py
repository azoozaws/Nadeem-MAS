import logging
import sys

def setup_custom_logger(name: str) -> logging.Logger:
    """
    Configure and return a custom isolated logger instance.
    Prevents log spam from other third-party libraries.
    """
    # 1. إنشاء أو جلب كائن الـ Logger
    logger = logging.getLogger(name)
    
    # 2. التحقق لمنع تكرار إضافة القنوات (Handlers) إذا تم استدعاء الدالة عدة مرات
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 3. إعداد التنسيق (Formatter) بشكل أنظف
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 4. توجيه المخرجات إلى الشاشة (Console Handler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 5. (السر الهندسي): منع تسريب السجلات للجذر الأساسي لتجنب التكرار
        logger.propagate = False
        
    return logger