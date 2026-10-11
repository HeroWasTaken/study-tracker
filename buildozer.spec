[app]

title = Study Tracker
package.name = studytracker
package.domain = org.studytracker
source.dir = .
source.include_exts = py,json,kv,png,jpg,atlas
version = 1.0.0
requirements = python3==3.11.9,hostpython3==3.11.9,kivy
orientation = portrait
fullscreen = 0

# Android settings
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

# Keep the app offline and avoid requesting unnecessary permissions.
android.permissions =

p4a.branch = develop
p4a.commit = d2ee8c5

[buildozer]

log_level = 2
warn_on_root = 1
