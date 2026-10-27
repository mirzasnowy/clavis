<#
.SYNOPSIS
  Windows UI Automation — official Microsoft UIA pattern, no external download.
  Uses System.Windows.Automation (UIAutomationClient / UIAutomationTypes),
  which ships with Windows .NET. Same pattern as Microsoft Learn:
  AutomationElement.RootElement -> FindFirst/FindAll(TreeScope, PropertyCondition)
  -> GetCurrentPattern(InvokePattern/ValuePattern/TogglePattern).

  Actions:
    ListWindows  - list top-level windows (Name, AutomationId, ClassName)
    Dump         - dump all descendants of a window (Name, ControlType, AutomationId, BoundingRectangle)
    Find         - find first descendant by Name (contains, case-insensitive)
    Click        - find by Name, then InvokePattern.Invoke() (fail closed if 0 or >1 match)
    Type         - find by Name, then ValuePattern.SetValue(text) if supported,
                   else fall back to SetFocus + SendKeys (only for Edit controls)

  Usage (run ON a Windows host, in a desktop session, not headless/SSH without a session):
    powershell -ExecutionPolicy Bypass -File winui.ps1 -Action ListWindows
    powershell -ExecutionPolicy Bypass -File winui.ps1 -Action Dump -Window "Notepad"
    powershell -ExecutionPolicy Bypass -File winui.ps1 -Action Click -Window "Calculator" -Name "7"
    powershell -ExecutionPolicy Bypass -File winui.ps1 -Action Type -Window "Notepad" -Name "Text Editor" -Text "Hello"

  Safety: Click/Type fail closed on ambiguous matches (never click the first
  match when several match). Dump/ListWindows are read-only.
  STATUS: written from official UIA documentation, NOT tested on a real
  Windows desktop by this agent (host here is headless Linux). Test it on
  your Windows laptop with Notepad/Calculator first, see docs/ui-automation.md.
#>
param(
    [ValidateSet("ListWindows","Dump","Find","Click","Type")]
    [string]$Action = "ListWindows",
    [string]$Window = "",
    [string]$Name = "",
    [string]$Text = ""
)

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

function To-JsonObj($obj) { $obj | ConvertTo-Json -Depth 4 -Compress }

function Get-Window($windowName) {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    if ([string]::IsNullOrWhiteSpace($windowName)) { return $root }
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NameProperty, $windowName)
    $win = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $cond)
    if ($null -eq $win) {
        # Fall back: window name contains (search all children, first contains-match)
        $all = $root.FindAll([System.Windows.Automation.TreeScope]::Children,
            [System.Windows.Automation.Condition]::TrueCondition)
        foreach ($w in $all) {
            if ($w.Current.Name -like "*$windowName*") { return $w }
        }
    }
    return $win
}

function Element-Info($el) {
    $rect = $el.Current.BoundingRectangle
    return @{
        Name = $el.Current.Name
        ControlType = $el.Current.ControlType.ProgrammaticName
        AutomationId = $el.Current.AutomationId
        ClassName = $el.Current.ClassName
        IsEnabled = $el.Current.IsEnabled
        BoundingRectangle = @{ X = $rect.X; Y = $rect.Y; Width = $rect.Width; Height = $rect.Height }
    }
}

function Find-Descendants($rootEl, $name) {
    $all = $rootEl.FindAll([System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    $matches = @()
    foreach ($el in $all) {
        if ($el.Current.Name -like "*$name*") { $matches += $el }
    }
    return $matches
}

switch ($Action) {
    "ListWindows" {
        $root = [System.Windows.Automation.AutomationElement]::RootElement
        $all = $root.FindAll([System.Windows.Automation.TreeScope]::Children,
            [System.Windows.Automation.Condition]::TrueCondition)
        $out = @()
        foreach ($w in $all) { if ($w.Current.Name) { $out += (Element-Info $w) } }
        Write-Output (To-JsonObj @{ windows = $out })
    }
    "Dump" {
        $win = Get-Window $Window
        if ($null -eq $win) { Write-Output (To-JsonObj @{ error = "window not found: $Window" }); exit 1 }
        $all = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition)
        $out = @()
        foreach ($el in $all) { $out += (Element-Info $el) }
        Write-Output (To-JsonObj @{ window = $win.Current.Name; count = $out.Count; elements = $out })
    }
    "Find" {
        $win = Get-Window $Window
        if ($null -eq $win) { Write-Output (To-JsonObj @{ error = "window not found: $Window" }); exit 1 }
        $m = Find-Descendants $win $Name
        $out = @(); foreach ($el in $m) { $out += (Element-Info $el) }
        Write-Output (To-JsonObj @{ window = $win.Current.Name; matches = $out.Count; elements = $out })
    }
    "Click" {
        $win = Get-Window $Window
        if ($null -eq $win) { Write-Output (To-JsonObj @{ error = "window not found: $Window" }); exit 1 }
        $m = Find-Descendants $win $Name
        if ($m.Count -eq 0) { Write-Output (To-JsonObj @{ error = "element not found: $Name" }); exit 1 }
        if ($m.Count -gt 1) { Write-Output (To-JsonObj @{ error = "ambiguous: $($m.Count) elements match '$Name', refusing to click the first one" }); exit 1 }
        $el = $m[0]
        $inv = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        if ($null -eq $inv) { Write-Output (To-JsonObj @{ error = "element does not support InvokePattern: $Name" }); exit 1 }
        $inv.Invoke()
        Write-Output (To-JsonObj @{ ok = $true; clicked = (Element-Info $el) })
    }
    "Type" {
        $win = Get-Window $Window
        if ($null -eq $win) { Write-Output (To-JsonObj @{ error = "window not found: $Window" }); exit 1 }
        $m = Find-Descendants $win $Name
        if ($m.Count -eq 0) { Write-Output (To-JsonObj @{ error = "element not found: $Name" }); exit 1 }
        if ($m.Count -gt 1) { Write-Output (To-JsonObj @{ error = "ambiguous: $($m.Count) elements match '$Name'" }); exit 1 }
        $el = $m[0]
        $val = $null
        try { $val = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern) } catch {}
        if ($null -ne $val -and -not $val.Current.IsReadOnly) {
            $val.SetValue($Text)
            Write-Output (To-JsonObj @{ ok = $true; typed_via = "ValuePattern"; element = (Element-Info $el) })
        } else {
            $el.SetFocus()
            Start-Sleep -Milliseconds 200
            [System.Windows.Forms.SendKeys]::SendWait($Text)
            Write-Output (To-JsonObj @{ ok = $true; typed_via = "SendKeys fallback"; element = (Element-Info $el) })
        }
    }
}
