param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$submission = Join-Path $RepositoryRoot "output\submission"
$concept = Join-Path $submission "Route2Zero_Concept_Deck_20_Slides.pptx"
$demo = Join-Path $submission "Route2Zero_Prototype_Demonstration.pptx"
$pilot = Join-Path $submission "Route2Zero_Team_Larpers_Pilot_Plan.docx"

foreach ($path in @($concept, $demo, $pilot)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required artifact is missing: $path"
    }
}

$powerPoint = $null
$word = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    foreach ($item in @(
        @{ Source = $concept; Target = (Join-Path $submission "Route2Zero_Concept.pdf") },
        @{ Source = $demo; Target = (Join-Path $submission "Route2Zero_Prototype_Demonstration.pdf") }
    )) {
        $presentation = $powerPoint.Presentations.Open($item.Source, $false, $false, $false)
        try {
            foreach ($slide in $presentation.Slides) {
                foreach ($shape in $slide.Shapes) {
                    if ($shape.HasTextFrame -eq 0 -or $shape.TextFrame.HasText -eq 0) {
                        continue
                    }
                    $shapeText = $shape.TextFrame.TextRange.Text
                    if ($shapeText -like "*https://github.com/qjmre23/Route2Zero*") {
                        $shape.ActionSettings(1).Action = 7
                        $shape.ActionSettings(1).Hyperlink.Address = "https://github.com/qjmre23/Route2Zero"
                    }
                    elseif ($shapeText -like "*https://route2zero.netlify.app/*") {
                        $shape.ActionSettings(1).Action = 7
                        $shape.ActionSettings(1).Hyperlink.Address = "https://route2zero.netlify.app/"
                    }
                }
            }
            $presentation.Save()
            $presentation.SaveAs($item.Target, 32)
        }
        finally {
            $presentation.Close()
        }
    }

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $document = $word.Documents.Open($pilot, $false, $true)
    try {
        $document.ExportAsFixedFormat((Join-Path $submission "Route2Zero_Team_Larpers_Pilot_Plan.pdf"), 17)
    }
    finally {
        $document.Close($false)
    }
}
finally {
    if ($word) { $word.Quit() }
    if ($powerPoint) { $powerPoint.Quit() }
    if ($document) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    if ($word) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
    if ($powerPoint) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Get-ChildItem -LiteralPath $submission -File | Where-Object { $_.Extension -in ".pdf", ".pptx", ".docx" } | Select-Object Name, Length, LastWriteTime
