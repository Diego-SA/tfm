@echo off

call ..\SourceMeterRPG.exe -projectBaseDir=.\ -resultsDir=Results -projectName=instrg -rpg3FileNamePattern=.*\.rpg
call ..\SourceMeterRPG.exe -projectBaseDir=.\ -resultsDir=Results -projectName=samplerpg -rpg4FileNamePattern=.*\.rpgle
call ..\SourceMeterRPG.exe -projectBaseDir=.\ -resultsDir=Results -projectName=cldemo -spoolFileNamePattern=.*\.txt