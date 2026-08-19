[app]

title = Daftar
package.name = daftar
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db,ttf,otf

version = 0.1

requirements = python3,kivy==2.3.1,kivymd==1.2.0

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
