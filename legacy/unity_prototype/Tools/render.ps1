<#
.SYNOPSIS
    Reproducible render of the proof of concept: Unity (batch mode) -> PNG sequence -> ffmpeg -> MP4.

.DESCRIPTION
    Frames are produced by Disagreement.EditorTools.OfflineRenderer, which poses the scene from the
    frame number alone. Running this twice with the same arguments produces the same frames.

    Output goes to Renders\<profile>\ :
        frames\frame_00000.png ...     full-rate sequence (file number = frame number)
        frames_step<N>\...             when -FrameStep N is used
        poc_<profile>.mp4              encoded video
        contact_<profile>.png          contact sheet, with -Stills

.EXAMPLE
    .\Tools\render.ps1                         # preview, full 30 s
.EXAMPLE
    .\Tools\render.ps1 -Stills                 # 12 preview stills + contact sheet, fastest check
.EXAMPLE
    .\Tools\render.ps1 -RenderProfile final    # on the GPU workstation
.EXAMPLE
    .\Tools\render.ps1 -RenderProfile final -StartFrame 300 -EndFrame 599 -NoEncode
                                               # render a range only; encode later with -EncodeOnly
#>
param(
    [ValidateSet('preview', 'final')]
    [string]$RenderProfile = 'preview',
    [int]$StartFrame = 0,
    [int]$EndFrame = -1,
    [int]$FrameStep = 1,
    # Every 75th frame and a contact sheet instead of a video.
    [switch]$Stills,
    [switch]$NoEncode,
    [switch]$EncodeOnly,
    [string]$UnityPath = $env:UNITY_EDITOR,
    [string]$FfmpegPath = $env:FFMPEG,
    # Music file to mux in. Defaults to Audio\track.* at the repository root, if present.
    [string]$Audio
)

$ErrorActionPreference = 'Stop'

# Must match Assets/Disagreement/Runtime/Core/PocTimeline.cs
$Fps = 30
$TotalFrames = 900
$MusicOffset = 35.0

$root = Split-Path -Parent $PSScriptRoot
if ($Stills -and $FrameStep -eq 1) { $FrameStep = 75 }
if ($FrameStep -lt 1) { throw "FrameStep must be at least 1." }
if ($EndFrame -lt 0 -or $EndFrame -ge $TotalFrames) { $EndFrame = $TotalFrames - 1 }
if ($StartFrame -lt 0 -or $StartFrame -gt $EndFrame) { throw "StartFrame must be between 0 and EndFrame ($EndFrame)." }
$StartFrame -= $StartFrame % $FrameStep

$outRoot = Join-Path $root "Renders\$RenderProfile"
$framesName = if ($FrameStep -gt 1) { "frames_step$FrameStep" } else { 'frames' }
$frames = Join-Path $outRoot $framesName
$fullRange = ($StartFrame -eq 0) -and ($EndFrame -eq $TotalFrames - 1)

function Find-Unity {
    if ($UnityPath) {
        if (-not (Test-Path $UnityPath)) { throw "Unity editor not found at '$UnityPath'." }
        return $UnityPath
    }
    $installed = @()
    foreach ($hub in @("$env:ProgramFiles\Unity\Hub\Editor", "$env:ProgramFiles\Unity Hub\Editor")) {
        if (Test-Path $hub) {
            $installed += Get-ChildItem $hub -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'Editor\Unity.exe') }
        }
    }
    if (-not $installed) {
        throw "No Unity editor found. Install one with Unity Hub, or pass -UnityPath / set UNITY_EDITOR to Unity.exe."
    }
    # Prefer the version the project was last opened with.
    $versionFile = Join-Path $root 'ProjectSettings\ProjectVersion.txt'
    if (Test-Path $versionFile) {
        $match = Select-String -Path $versionFile -Pattern '^m_EditorVersion:\s*(\S+)' | Select-Object -First 1
        if ($match) {
            $wanted = $match.Matches[0].Groups[1].Value
            $exact = $installed | Where-Object { $_.Name -eq $wanted } | Select-Object -First 1
            if ($exact) { return (Join-Path $exact.FullName 'Editor\Unity.exe') }
        }
    }
    $newest = $installed | Sort-Object Name -Descending | Select-Object -First 1
    return (Join-Path $newest.FullName 'Editor\Unity.exe')
}

function Find-Ffmpeg {
    if ($FfmpegPath) {
        if (-not (Test-Path $FfmpegPath)) { throw "ffmpeg not found at '$FfmpegPath'." }
        return $FfmpegPath
    }
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "ffmpeg not found on PATH. Pass -FfmpegPath or set FFMPEG." }
    return $cmd.Source
}

# ---------------------------------------------------------------- render
if (-not $EncodeOnly) {
    $unity = Find-Unity
    New-Item -ItemType Directory -Force $frames | Out-Null

    # A full-range render replaces the sequence; a partial range only overwrites its own frames.
    if ($fullRange) {
        Get-ChildItem $frames -Filter 'frame_*.png' | Remove-Item -Confirm:$false
    }

    $log = Join-Path $outRoot 'unity_render.log'
    $unityArgs = @(
        '-batchmode',
        '-projectPath', "`"$root`"",
        '-executeMethod', 'Disagreement.EditorTools.OfflineRenderer.RenderFromCommandLine',
        '-logFile', "`"$log`"",
        '-dgProfile', $RenderProfile,
        '-dgOut', "`"$frames`"",
        '-dgStart', $StartFrame,
        '-dgEnd', $EndFrame,
        '-dgStep', $FrameStep
    )
    Write-Host "Rendering $RenderProfile frames $StartFrame..$EndFrame (step $FrameStep) with $unity"
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $process = Start-Process -FilePath $unity -ArgumentList $unityArgs -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        if (Test-Path $log) { Get-Content $log -Tail 40 }
        throw "Unity exited with code $($process.ExitCode). Full log: $log"
    }
    Write-Host ("Rendered in {0:n0} s -> {1}" -f $timer.Elapsed.TotalSeconds, $frames)
}

if ($NoEncode) { return }

# ---------------------------------------------------------------- encode
$ffmpeg = Find-Ffmpeg
$firstFile = [int]($StartFrame / $FrameStep)
$count = [int](($EndFrame - $StartFrame) / $FrameStep) + 1
$pattern = Join-Path $frames 'frame_%05d.png'

if ($Stills) {
    $columns = 4
    $rows = [int][math]::Ceiling($count / $columns)
    $sheet = Join-Path $outRoot "contact_$RenderProfile.png"
    & $ffmpeg -y -loglevel error -start_number $firstFile -i $pattern -frames:v 1 `
        -vf "scale=480:-2,tile=${columns}x${rows}:padding=4" $sheet
    if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed building the contact sheet." }
    Write-Host "Contact sheet -> $sheet"
    return
}

if (-not $Audio) {
    $found = Get-ChildItem (Join-Path $root 'Audio') -Filter 'track.*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $Audio = $found.FullName }
}

$crf = if ($RenderProfile -eq 'final') { 14 } else { 23 }
$preset = if ($RenderProfile -eq 'final') { 'slow' } else { 'veryfast' }
$video = Join-Path $outRoot "poc_$RenderProfile.mp4"

$ffArgs = @('-y', '-loglevel', 'error', '-framerate', "$Fps/$FrameStep", '-start_number', $firstFile, '-i', $pattern)
if ($Audio) {
    # Line the excerpt up with the track: local frame 0 is 00:35 of the music.
    $audioStart = ($MusicOffset + $StartFrame / $Fps).ToString([cultureinfo]::InvariantCulture)
    $ffArgs += @('-ss', $audioStart, '-i', $Audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest')
}
$ffArgs += @('-frames:v', $count, '-c:v', 'libx264', '-preset', $preset, '-crf', $crf, '-pix_fmt', 'yuv420p', $video)

& $ffmpeg @ffArgs
if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed encoding the video." }
if ($Audio) { Write-Host "Video (with audio from $Audio) -> $video" } else { Write-Host "Video (silent; no Audio\track.* found) -> $video" }
