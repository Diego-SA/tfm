@echo off

cd log4cplus-1.1.0\msvc10
msbuild log4cplus.vcxproj /t:Rebuild /p:Configuration=Release /p:PLatform=x64