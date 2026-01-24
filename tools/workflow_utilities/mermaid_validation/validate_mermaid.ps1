#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates Mermaid diagrams in markdown files against known syntax rules
.DESCRIPTION
    Scans markdown files for Mermaid diagrams and checks for common syntax errors
    based on the documented rules in .cursor/rules/mermaid-rule.mdc
.PARAMETER Path
    Directory path to scan for markdown files (defaults to current directory)
.PARAMETER Recurse
    Recursively scan subdirectories
.EXAMPLE
    .\validate_mermaid.ps1 -Path "tasks/my_task"
.EXAMPLE
    .\validate_mermaid.ps1 -Path "." -Recurse
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$Path = ".",

    [Parameter(Mandatory = $false)]
    [switch]$Recurse
)

# Known bad patterns from mermaid-rule.mdc
$badPatterns = @(
    # HTML tags in node labels
    @{ Pattern = '<br/?>'; Description = "HTML <br/> tags found - replace with | for line breaks"; Severity = "Error" }
    @{ Pattern = '<b>|</b>|<i>|</i>'; Description = "HTML formatting tags found - remove HTML tags"; Severity = "Error" }

    # Unquoted special characters in node labels
    @{ Pattern = '\b\w+\[([^\]"]*[/\\][^\]"]*)\]'; Description = "Unquoted special characters in node labels - use quotes"; Severity = "Warning" }

    # Nested quotes - DISABLED: Current pattern too aggressive for valid Mermaid quoted strings
    # @{ Pattern = '(?<![\"\[])"[^"]*"[^"]*"[^"]*"(?![\"\]])' ; Description = "Nested quotes detected outside valid Mermaid syntax - remove inner quotes"; Severity = "Error" }

    # Wrong orientation for vertical docs
    @{ Pattern = 'graph LR'; Description = "Horizontal orientation (LR) found - use TD for vertical docs"; Severity = "Warning" }

    # Complex class diagram syntax
    @{ Pattern = '\|\|--\|\|'; Description = "Complex class syntax found - use --> with labels"; Severity = "Warning" }

    # Diamond shape syntax errors
    @{ Pattern = '\{[^{}]*\{[^{}]*\}'; Description = "Malformed diamond shape syntax - nested braces in diamond"; Severity = "Error" }
    @{ Pattern = '\{[^}]*$'; Description = "Unclosed diamond shape - missing closing brace"; Severity = "Error" }
)

function Write-Header {
    param([string]$Text)
    Write-Host "`n$Text" -ForegroundColor Cyan
    Write-Host ("=" * $Text.Length) -ForegroundColor Cyan
}

function Write-Result {
    param(
        [string]$File,
        [string]$LineNumber,
        [string]$Pattern,
        [string]$Description,
        [string]$Severity,
        [string]$LineContent
    )

    $color = switch ($Severity) {
        "Error" { "Red" }
        "Warning" { "Yellow" }
        default { "White" }
    }

    Write-Host "[$Severity] $File`:$LineNumber" -ForegroundColor $color
    Write-Host "  Pattern: $Pattern" -ForegroundColor Gray
    Write-Host "  Issue: $Description" -ForegroundColor Gray
    Write-Host "  Line: $LineContent" -ForegroundColor DarkGray
    Write-Host ""
}

function Test-MermaidSyntax {
    param([string]$FilePath)

    $content = Get-Content $FilePath -Raw
    $lines = Get-Content $FilePath
    $foundIssues = $false

    # Check if file contains mermaid diagrams (only code blocks for reliability)
    if ($content -notmatch '(?s)```mermaid') {
        return $false
    }

    # Remove YAML frontmatter first (between --- markers)
    # Handle multiple frontmatter blocks by removing all of them
    $contentWithoutFrontmatter = $content
    while ($contentWithoutFrontmatter -match '(?s)---.*?---\s*') {
        $frontmatterPattern = '(?s)---.*?---\s*'
        $contentWithoutFrontmatter = [regex]::Replace($contentWithoutFrontmatter, $frontmatterPattern, '', 1)
    }

    # Extract only Mermaid diagram content
    $diagramContent = ""

    # ONLY process Mermaid code blocks - this is the most reliable approach
    $mermaidBlocks = [regex]::Matches($contentWithoutFrontmatter, '(?s)```mermaid\s*(.*?)```')
    foreach ($block in $mermaidBlocks) {
        if ($block.Groups.Count -gt 1) {
            $diagramContent += $block.Groups[1].Value + "`n"
        }
    }

    # If no diagrams found, skip this file
    if ($diagramContent -eq "") {
        return $false
    }

    Write-Header "Checking: $FilePath"

    # Check each bad pattern only within Mermaid diagram content
    foreach ($pattern in $badPatterns) {
        $regex = [regex]$pattern.Pattern
        $patternMatches = $regex.Matches($diagramContent)

        foreach ($match in $patternMatches) {
            # Find the corresponding line number in the original file
            # We need to map the match position back to the original file
            $lineNumber = 1
            $foundInDiagram = $false

            # Find Mermaid code blocks in original content and map the match
            $originalMermaidBlocks = [regex]::Matches($contentWithoutFrontmatter, '(?s)```mermaid\s*(.*?)```')
            $currentPos = 0

            foreach ($block in $originalMermaidBlocks) {
                if ($block.Groups.Count -gt 1) {
                    $blockContent = $block.Groups[1].Value
                    $blockStart = $block.Index + $block.Length - $blockContent.Length - 3  # Account for ```

                    # Check if our match is within this block
                    $matchPosInBlock = $match.Index - $currentPos
                    if ($matchPosInBlock -ge 0 -and $matchPosInBlock -lt $blockContent.Length) {
                        # Find the line number within this block
                        $blockLines = $blockContent -split "`n"
                        $posInBlock = 0
                        for ($lineIdx = 0; $lineIdx -lt $blockLines.Count; $lineIdx++) {
                            $lineLength = $blockLines[$lineIdx].Length + 1  # +1 for newline
                            if ($matchPosInBlock -lt $posInBlock + $lineLength) {
                                # Find the actual line in the original file
                                $originalContent = $contentWithoutFrontmatter
                                $blockStartLine = ($originalContent.Substring(0, $blockStart) -split "`n").Count
                                $lineNumber = $blockStartLine + $lineIdx
                                $foundInDiagram = $true
                                break
                            }
                            $posInBlock += $lineLength
                        }
                        break
                    }
                    $currentPos += $blockContent.Length
                }
            }

            # Only report if we found it in a valid diagram block
            if ($foundInDiagram) {
                Write-Result -File $FilePath -LineNumber $lineNumber -Pattern $match.Value -Description $pattern.Description -Severity $pattern.Severity -LineContent "Mermaid diagram content"
                $foundIssues = $true
            }
        }
    }

    return $foundIssues
}

function Test-MermaidDiagrams {
    param([string]$ScanPath, [bool]$Recursive)

    Write-Header "Mermaid Diagram Validation"
    Write-Host "Scanning: $ScanPath" -ForegroundColor Green
    Write-Host "Recursive: $Recursive" -ForegroundColor Green
    Write-Host ""

    $filesChecked = 0
    $filesWithIssues = 0

    # Find markdown files
    $params = @{
        Path = $ScanPath
        Filter = "*.md"
        File = $true
    }

    if ($Recursive) {
        $params.Recurse = $true
    }

    $markdownFiles = Get-ChildItem @params

    foreach ($file in $markdownFiles) {
        $filesChecked++
        if (Test-MermaidSyntax -FilePath $file.FullName) {
            $filesWithIssues++
        }
    }

    # Summary
    Write-Header "Validation Summary"
    Write-Host "Files checked: $filesChecked" -ForegroundColor White
    Write-Host "Files with issues: $filesWithIssues" -ForegroundColor $(if ($filesWithIssues -gt 0) { "Red" } else { "Green" })

    if ($filesWithIssues -eq 0) {
        Write-Host "`n✅ All Mermaid diagrams appear to follow syntax rules!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Issues found. Please fix the reported syntax errors." -ForegroundColor Red
        Write-Host "Reference: .cursor/rules/mermaid-rule.mdc for detailed rules." -ForegroundColor Yellow
    }
}

# Main execution
try {
    if (-not (Test-Path $Path)) {
        Write-Error "Path '$Path' does not exist."
        exit 1
    }

    Test-MermaidDiagrams -ScanPath $Path -Recursive $Recurse
}
catch {
    Write-Error "An error occurred: $_"
    exit 1
}

