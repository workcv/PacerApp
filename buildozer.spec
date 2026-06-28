[app]
title           = Step Pacer
package.name    = pacerclean
package.domain  = org.test
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,json
version         = 1.0

# Dependencies
requirements    = python3,kivy,pyjnius,android

# UI Configuration
orientation     = portrait
fullscreen      = 0

# Permissions
android.permissions = VIBRATE

# Android SDK/NDK - Updated for Google Play compliance
android.api         = 34
android.minapi      = 21
android.ndk         = 25b
android.archs       = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
