[app]
title = id check
package.name = idcheck
package.domain = com.idcheck
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,md,csv
version = 0.2.0
requirements = python3,kivy,pillow,sqlite3,plyer,android
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 28
android.archs = arm64-v8a, armeabi-v7a
android.permissions = CAMERA,READ_MEDIA_IMAGES
android.allow_backup = False
android.accept_sdk_license = True
android.presplash_color = #FFFFFF
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0
