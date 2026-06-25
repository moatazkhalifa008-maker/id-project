# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen

from app.storage.database import Database
from app.services.ocr_service import OCRService
from app.services.export_service import export_csv
from app.services.camera_service import ensure_camera_permissions, get_default_capture_dir, take_picture
from app.utils.arabic_normalizer import normalize_arabic
from app.utils.rtl import rtl_text

APP_TITLE = 'id check'
DEFAULT_FONT = 'assets/fonts/Cairo-Regular.ttf'

KV = r'''
#:import dp kivy.metrics.dp

<PrimaryButton@Button>:
    font_name: app.font_path if app.font_exists else 'Roboto'
    font_size: '18sp'
    size_hint_y: None
    height: dp(48)
    background_normal: ''
    background_color: (.12, .45, .78, 1)
    color: (1,1,1,1)

<SectionLabel@Label>:
    font_name: app.font_path if app.font_exists else 'Roboto'
    color: (.1,.1,.1,1)
    text_size: self.width, None
    halign: 'right'
    valign: 'middle'
    size_hint_y: None
    height: dp(26)

<ReadonlyField@Label>:
    font_name: app.font_path if app.font_exists else 'Roboto'
    text_size: self.width, None
    halign: 'right'
    valign: 'middle'
    size_hint_y: None
    height: dp(42)
    color: (.1, .1, .1, 1)

<MainMenuScreen>:
    name: 'menu'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(12)
        Label:
            text: app.rtl('id check')
            font_name: app.font_path if app.font_exists else 'Roboto'
            bold: True
            font_size: '28sp'
            size_hint_y: None
            height: dp(50)
            color: (.05,.05,.05,1)
        Label:
            text: app.rtl('تطبيق أوفلاين لحفظ صور وبيانات بطاقات الهوية المصرية')
            font_name: app.font_path if app.font_exists else 'Roboto'
            text_size: self.width, None
            halign: 'right'
            valign: 'middle'
            size_hint_y: None
            height: dp(50)
            color: (.2,.2,.2,1)
        PrimaryButton:
            text: app.rtl('التقاط بطاقة جديدة بالكاميرا')
            on_release: root.capture_with_camera()
        PrimaryButton:
            text: app.rtl('استيراد صورة بطاقة من مسار موجود')
            on_release: root.import_existing_image()
        PrimaryButton:
            text: app.rtl('البحث بالاسم')
            on_release: app.root.current = 'search'
        PrimaryButton:
            text: app.rtl('عرض آخر السجلات')
            on_release: app.root.get_screen('records').refresh_records(); app.root.current = 'records'
        PrimaryButton:
            text: app.rtl('تصدير CSV')
            on_release: app.root.current = 'export'
        Label:
            text: app.rtl(root.status_message)
            font_name: app.font_path if app.font_exists else 'Roboto'
            text_size: self.width, None
            halign: 'right'
            size_hint_y: None
            height: dp(60)
            color: (.15,.15,.15,1)
        Widget:

<SearchScreen>:
    name: 'search'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(8)
            PrimaryButton:
                size_hint_x: .28
                text: app.rtl('رجوع')
                on_release: app.root.current = 'menu'
            TextInput:
                id: q
                multiline: False
                hint_text: app.rtl('ابحث بالاسم...')
                font_name: app.font_path if app.font_exists else 'Roboto'
                halign: 'right'
                write_tab: False
            PrimaryButton:
                size_hint_x: .28
                text: app.rtl('بحث')
                on_release: root.do_search(q.text)
        Label:
            id: status
            text: app.rtl('اكتب جزءًا من الاسم ثم اضغط بحث')
            font_name: app.font_path if app.font_exists else 'Roboto'
            text_size: self.width, None
            halign: 'right'
            size_hint_y: None
            height: dp(36)
            color: (.2,.2,.2,1)
        RecycleView:
            id: rv
            viewclass: 'Button'
            data: []
            RecycleBoxLayout:
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'

<ReviewScreen>:
    name: 'review'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)
        Label:
            text: app.rtl('مراجعة البيانات المستخرجة')
            font_name: app.font_path if app.font_exists else 'Roboto'
            font_size: '22sp'
            size_hint_y: None
            height: dp(40)
            color: (.05,.05,.05,1)
        Image:
            allow_stretch: True
            keep_ratio: True
            source: root.image_path if root.image_path else ''
            size_hint_y: .34
        GridLayout:
            cols: 1
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            SectionLabel:
                text: app.rtl('الاسم')
            ReadonlyField:
                text: app.rtl(root.full_name)
            SectionLabel:
                text: app.rtl('العنوان')
            ReadonlyField:
                text: app.rtl(root.address)
            SectionLabel:
                text: app.rtl('الرقم القومي')
            ReadonlyField:
                text: root.national_id
            SectionLabel:
                text: app.rtl('تاريخ الميلاد')
            ReadonlyField:
                text: root.birth_date
            SectionLabel:
                text: app.rtl('السن')
            ReadonlyField:
                text: root.age_text
        Label:
            text: app.rtl(root.status_message)
            font_name: app.font_path if app.font_exists else 'Roboto'
            text_size: self.width, None
            halign: 'right'
            size_hint_y: None
            height: dp(48)
            color: (.75,.12,.12,1) if 'خطأ' in root.status_message or 'فشل' in root.status_message else (.15,.45,.15,1)
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            PrimaryButton:
                text: app.rtl('إعادة التصوير')
                on_release: app.root.current = 'menu'
            PrimaryButton:
                text: app.rtl('حفظ')
                on_release: root.save_record()

<RecordsScreen>:
    name: 'records'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(8)
            PrimaryButton:
                size_hint_x: .28
                text: app.rtl('رجوع')
                on_release: app.root.current = 'menu'
            Label:
                text: app.rtl('آخر السجلات')
                font_name: app.font_path if app.font_exists else 'Roboto'
                color: (.1,.1,.1,1)
        RecycleView:
            id: rv_records
            viewclass: 'Button'
            data: []
            RecycleBoxLayout:
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'

<DetailScreen>:
    name: 'detail'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(8)
            PrimaryButton:
                size_hint_x: .28
                text: app.rtl('رجوع')
                on_release: app.root.current = 'search'
            Label:
                text: app.rtl('تفاصيل السجل')
                font_name: app.font_path if app.font_exists else 'Roboto'
                color: (.1,.1,.1,1)
        Image:
            source: root.image_path
            allow_stretch: True
            keep_ratio: True
            size_hint_y: .38
        GridLayout:
            cols: 1
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            SectionLabel:
                text: app.rtl('الاسم')
            ReadonlyField:
                text: app.rtl(root.full_name)
            SectionLabel:
                text: app.rtl('العنوان')
            ReadonlyField:
                text: app.rtl(root.address)
            SectionLabel:
                text: app.rtl('الرقم القومي')
            ReadonlyField:
                text: root.national_id
            SectionLabel:
                text: app.rtl('السن')
            ReadonlyField:
                text: root.age_text

<ExportScreen>:
    name: 'export'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)
        Label:
            text: app.rtl('تصدير ملف CSV')
            font_name: app.font_path if app.font_exists else 'Roboto'
            font_size: '22sp'
            size_hint_y: None
            height: dp(40)
            color: (.1,.1,.1,1)
        SectionLabel:
            text: app.rtl('المسار الذي تحدده للحفظ (مثال: /storage/emulated/0/Download)')
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: export_path
            multiline: False
            hint_text: '/storage/emulated/0/Download'
            font_name: app.font_path if app.font_exists else 'Roboto'
            halign: 'right'
            size_hint_y: None
            height: dp(42)
        Label:
            id: export_status
            text: app.rtl('أدخل مسار المجلد ثم اضغط تصدير')
            font_name: app.font_path if app.font_exists else 'Roboto'
            text_size: self.width, None
            halign: 'right'
            size_hint_y: None
            height: dp(48)
            color: (.2,.2,.2,1)
        PrimaryButton:
            text: app.rtl('تصدير CSV')
            on_release: root.do_export(export_path.text)
        PrimaryButton:
            text: app.rtl('رجوع')
            on_release: app.root.current = 'menu'
        Widget:
'''

class MainMenuScreen(Screen):
    status_message = StringProperty('')

    def on_pre_enter(self, *args):
        self.status_message = 'المجلد الافتراضي للالتقاط: ' + str(get_default_capture_dir())

    def capture_with_camera(self):
        App.get_running_app().start_camera_capture('')

    def import_existing_image(self):
        app = App.get_running_app()
        app.show_text_popup(
            title=app.rtl('إدخال صورة بطاقة'),
            label=app.rtl('أدخل مسار صورة البطاقة الموجودة.'),
            callback=app.process_image_path,
            hint='/storage/emulated/0/Download/card.jpg',
        )

class SearchScreen(Screen):
    def do_search(self, query: str):
        app = App.get_running_app()
        results = app.db.search_by_name(query)
        self.ids.status.text = app.rtl('الاسم غير موجود') if not results else app.rtl('تم العثور على ' + str(len(results)) + ' نتيجة')
        self.ids.rv.data = [
            {
                'text': app.rtl(f"{r['full_name']}  |  {r['national_id']}"),
                'font_name': app.font_path if app.font_exists else 'Roboto',
                'on_release': (lambda rec=r: app.open_detail(rec))
            }
            for r in results
        ]

class ReviewScreen(Screen):
    image_path = StringProperty('')
    full_name = StringProperty('')
    address = StringProperty('')
    national_id = StringProperty('')
    birth_date = StringProperty('')
    age_text = StringProperty('')
    status_message = StringProperty('')

    def set_data(self, image_path: str, result):
        self.image_path = image_path
        self.full_name = getattr(result, 'full_name', '')
        self.address = getattr(result, 'address', '')
        self.national_id = getattr(result, 'national_id', '')
        self.birth_date = getattr(result, 'birth_date', '')
        age = getattr(result, 'age', None)
        self.age_text = str(age) if age is not None else ''
        self.status_message = getattr(result, 'message', '')

    def save_record(self):
        app = App.get_running_app()
        if not self.national_id:
            self.status_message = 'فشل الحفظ: لا يوجد رقم قومي. أعد تصوير البطاقة.'
            return
        if app.db.national_id_exists(self.national_id):
            self.status_message = 'تم تصوير هذه البطاقة مسبقًا'
            return
        app.db.insert_record(
            full_name=self.full_name,
            normalized_name=normalize_arabic(self.full_name),
            address=self.address,
            national_id=self.national_id,
            birth_date=self.birth_date,
            age=int(self.age_text) if self.age_text.isdigit() else None,
            image_path=self.image_path,
        )
        self.status_message = 'تم الحفظ بنجاح'
        Clock.schedule_once(lambda *_: setattr(app.root, 'current', 'menu'), 1.0)

class RecordsScreen(Screen):
    def refresh_records(self):
        app = App.get_running_app()
        records = app.db.list_recent(limit=50)
        self.ids.rv_records.data = [
            {
                'text': app.rtl(f"{r['full_name']}  |  {r['national_id']}"),
                'font_name': app.font_path if app.font_exists else 'Roboto',
                'on_release': (lambda rec=r: app.open_detail(rec))
            }
            for r in records
        ]

class DetailScreen(Screen):
    image_path = StringProperty('')
    full_name = StringProperty('')
    address = StringProperty('')
    national_id = StringProperty('')
    age_text = StringProperty('')

    def set_record(self, rec: dict):
        self.image_path = rec.get('image_path', '')
        self.full_name = rec.get('full_name', '')
        self.address = rec.get('address', '')
        self.national_id = rec.get('national_id', '')
        self.age_text = str(rec.get('age') or '')

class ExportScreen(Screen):
    def do_export(self, folder_path: str):
        app = App.get_running_app()
        try:
            csv_path = export_csv(app.db, folder_path)
            self.ids.export_status.text = app.rtl('تم إنشاء الملف:\n' + str(csv_path))
        except Exception as exc:
            self.ids.export_status.text = app.rtl('فشل التصدير: ' + str(exc))

class IDCheckScreenManager(ScreenManager):
    pass

class IDCheckApp(App):
    font_path = DEFAULT_FONT
    font_exists = False

    def build(self):
        self.title = APP_TITLE
        self.font_exists = os.path.exists(self.font_path)
        self.db = Database()
        self.ocr_service = OCRService()
        Builder.load_string(KV)
        sm = IDCheckScreenManager()
        sm.add_widget(MainMenuScreen())
        sm.add_widget(SearchScreen())
        sm.add_widget(ReviewScreen())
        sm.add_widget(RecordsScreen())
        sm.add_widget(DetailScreen())
        sm.add_widget(ExportScreen())
        return sm

    def rtl(self, text: str) -> str:
        return rtl_text(text)

    def start_camera_capture(self, folder_path: str):
        self._pending_capture_folder = str(get_default_capture_dir())
        ensure_camera_permissions(self.on_permissions_ready, self.on_permissions_denied)

    def on_permissions_ready(self):
        folder_path = getattr(self, '_pending_capture_folder', str(get_default_capture_dir()))
        target_dir = Path(folder_path).expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = target_dir / ('id_check_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg')
        self.root.get_screen('menu').status_message = 'جارٍ فتح الكاميرا...\nسيتم الحفظ في: ' + str(filename)

        def _open_camera(*_):
            try:
                take_picture(str(filename), self.on_picture_taken)
            except Exception as exc:
                self.root.get_screen('menu').status_message = 'فشل فتح الكاميرا: ' + str(exc)

        Clock.schedule_once(_open_camera, 0.2)

    def on_permissions_denied(self):
        self.root.get_screen('menu').status_message = 'تم رفض صلاحية الكاميرا. لا يمكن المتابعة بدونها.'

    def on_picture_taken(self, image_path):
        if not image_path:
            self.root.get_screen('menu').status_message = 'لم يتم التقاط صورة أو تم إلغاء العملية.'
            return False
        self.root.get_screen('menu').status_message = 'تم التقاط الصورة: ' + str(image_path)
        self.process_image_path(str(image_path))
        return False

    def process_image_path(self, image_path: str):
        image_path = (image_path or '').strip()
        if not image_path:
            self.root.get_screen('menu').status_message = 'لا يوجد مسار صورة صالح.'
            return
        result = self.ocr_service.process(image_path)
        review = self.root.get_screen('review')
        review.set_data(image_path, result)
        self.root.current = 'review'

    def open_detail(self, record: dict):
        detail = self.root.get_screen('detail')
        detail.set_record(record)
        self.root.current = 'detail'

    def show_text_popup(self, title: str, label: str, callback, hint='', initial=''):
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        txt = TextInput(multiline=False, hint_text=hint, halign='right', text=initial)
        if self.font_exists:
            txt.font_name = self.font_path
        lbl = Label(text=label, halign='right', valign='middle')
        if self.font_exists:
            lbl.font_name = self.font_path
        btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=8)
        ok = Button(text=self.rtl('متابعة'))
        cancel = Button(text=self.rtl('إلغاء'))
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content.add_widget(lbl)
        content.add_widget(txt)
        content.add_widget(btns)
        popup = Popup(title=title, content=content, size_hint=(.92, .48))
        ok.bind(on_release=lambda *_: (popup.dismiss(), callback(txt.text)))
        cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

if __name__ == '__main__':
    IDCheckApp().run()
