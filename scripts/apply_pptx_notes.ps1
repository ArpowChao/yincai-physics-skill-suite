param(
    [Parameter(Mandatory = $true)]
    [string]$InputPptx,

    [Parameter(Mandatory = $true)]
    [string]$NotesJson,

    [Parameter(Mandatory = $true)]
    [string]$OutputPptx
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $InputPptx).Path
$notesPath = (Resolve-Path -LiteralPath $NotesJson).Path
$target = [System.IO.Path]::GetFullPath($OutputPptx)
$targetParent = Split-Path -Parent $target

if ($source -eq $target) {
    throw "OutputPptx must not overwrite the input presentation."
}
if (Test-Path -LiteralPath $target) {
    throw "OutputPptx already exists: $target"
}
New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

$payload = Get-Content -LiteralPath $notesPath -Raw -Encoding utf8 | ConvertFrom-Json
$notesBySlide = @{}
foreach ($entry in $payload.slides) {
    $notesBySlide[[int]$entry.slide] = [string]$entry.notes
}

$app = $null
$presentation = $null
$updated = 0

try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open($source, $false, $false, $false)
    if ($presentation.Slides.Count -ne $notesBySlide.Count) {
        throw "Slide count mismatch: presentation=$($presentation.Slides.Count), notes=$($notesBySlide.Count)"
    }

    foreach ($slide in $presentation.Slides) {
        $number = [int]$slide.SlideNumber
        if (-not $notesBySlide.ContainsKey($number)) {
            throw "Missing note for slide $number"
        }
        $body = $null
        foreach ($shape in $slide.NotesPage.Shapes) {
            try {
                if (
                    [int]$shape.Type -eq 14 -and
                    [int]$shape.PlaceholderFormat.Type -eq 2 -and
                    [int]$shape.HasTextFrame -eq -1
                ) {
                    $body = $shape
                    break
                }
            }
            catch {
                continue
            }
        }
        if ($body -eq $null) {
            throw "Could not find the notes body placeholder on slide $number"
        }
        $body.TextFrame.TextRange.Text = $notesBySlide[$number]
        $updated += 1
    }

    # ppSaveAsOpenXMLPresentation = 24
    $presentation.SaveAs($target, 24)
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    if ($app -ne $null) {
        $app.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

[ordered]@{
    input = $source
    output = $target
    updated_slides = $updated
} | ConvertTo-Json
