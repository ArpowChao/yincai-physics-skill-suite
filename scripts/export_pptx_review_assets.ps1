param(
    [Parameter(Mandatory = $true)]
    [string]$InputPptx,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [int]$DefaultSlideSeconds = 5,
    [int]$VerticalResolution = 720,
    [int]$FramesPerSecond = 24,
    [int]$Quality = 85
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $InputPptx).Path
$target = [System.IO.Path]::GetFullPath($OutputDir)
$slidesDir = Join-Path $target "slides"
$videoPath = Join-Path $target "playback.mp4"
$statusPath = Join-Path $target "export-status.json"

New-Item -ItemType Directory -Force -Path $slidesDir | Out-Null

function Write-ExportStatus {
    param(
        [string]$State,
        [string]$Message,
        [int]$SlideCount = 0,
        [int]$PowerPointStatus = -1
    )
    [ordered]@{
        updated_at = [DateTimeOffset]::Now.ToString("o")
        state = $State
        message = $Message
        slide_count = $SlideCount
        powerpoint_status = $PowerPointStatus
        playback_path = $videoPath
    } | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding utf8
}

Write-ExportStatus -State "starting" -Message "Opening PowerPoint presentation."
$app = $null
$presentation = $null

try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open($source, $true, $false, $false)
    $slideCount = $presentation.Slides.Count

    Write-ExportStatus -State "rendering_slides" -Message "Exporting slide PNG files." -SlideCount $slideCount
    foreach ($slide in $presentation.Slides) {
        $slidePath = Join-Path $slidesDir ("slide-{0:D2}.png" -f $slide.SlideNumber)
        $slide.Export($slidePath, "PNG", 1280, 720)
    }

    if (Test-Path -LiteralPath $videoPath) {
        Remove-Item -LiteralPath $videoPath -Force
    }

    Write-ExportStatus -State "exporting_video" -Message "PowerPoint is creating the playback MP4." -SlideCount $slideCount
    $presentation.CreateVideo(
        $videoPath,
        $true,
        $DefaultSlideSeconds,
        $VerticalResolution,
        $FramesPerSecond,
        $Quality
    )

    $deadline = [DateTimeOffset]::Now.AddMinutes(30)
    while ([DateTimeOffset]::Now -lt $deadline) {
        $status = [int]$presentation.CreateVideoStatus
        switch ($status) {
            3 {
                Write-ExportStatus -State "completed" -Message "Slides and playback MP4 exported." -SlideCount $slideCount -PowerPointStatus $status
                break
            }
            4 {
                throw "PowerPoint reported that video export failed."
            }
            default {
                Write-ExportStatus -State "exporting_video" -Message "PowerPoint video export is still running." -SlideCount $slideCount -PowerPointStatus $status
                Start-Sleep -Seconds 2
            }
        }
        if ($status -eq 3) {
            break
        }
    }

    if ([DateTimeOffset]::Now -ge $deadline) {
        throw "PowerPoint video export exceeded the 30-minute timeout."
    }
}
catch {
    Write-ExportStatus -State "failed" -Message $_.Exception.Message
    throw
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
