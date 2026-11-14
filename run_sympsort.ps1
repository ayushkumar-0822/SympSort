# Alias for run.ps1
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$PSScriptRootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
& (Join-Path $PSScriptRootPath "run.ps1") @ArgsList
