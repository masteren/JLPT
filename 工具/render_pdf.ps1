<#
  把 PDF 的指定页渲染成 PNG（Windows 版，替代 macOS 的 render_pdf.js）。

  用法:
    powershell -File 工具/render_pdf.ps1 -Pdf "题/.../某.pdf" -OutDir "<输出目录>" -Pages "1,2,3" [-Width 1700]

  走 Windows 自带的 WinRT Windows.Data.Pdf，不需要装 poppler / ImageMagick / Node 包。
  输出目录不存在会自动创建。-Width 是渲染宽度（像素），默认 1700，够看清日文小字。
#>
param([string]$Pdf, [string]$OutDir, [string]$Pages, [int]$Width = 1700)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]

function Await($op, $type) {
    $t = $asTaskGeneric.MakeGenericMethod($type).Invoke($null, @($op))
    $t.Wait(-1) | Out-Null
    $t.Result
}
function AwaitAction($act) {
    $t = $asTaskAction.Invoke($null, @($act))
    $t.Wait(-1) | Out-Null
}

$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]

$full = (Resolve-Path -LiteralPath $Pdf).Path
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$outFull = (Resolve-Path -LiteralPath $OutDir).Path

$sf = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($full)) ([Windows.Storage.StorageFile])
$doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($sf)) ([Windows.Data.Pdf.PdfDocument])
Write-Output "pagecount=$($doc.PageCount)"

$list = $Pages.Split(',') | ForEach-Object { [int]$_.Trim() }
foreach ($p in $list) {
    if ($p -lt 1 -or $p -gt $doc.PageCount) { Write-Output "skip $p"; continue }
    $page = $doc.GetPage([uint32]($p - 1))
    $ms = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $opt.DestinationWidth = [uint32]$Width
    AwaitAction ($page.RenderToStreamAsync($ms, $opt))
    $size = [int]$ms.Size
    $ms.Seek(0)
    $dr = New-Object Windows.Storage.Streams.DataReader($ms.GetInputStreamAt(0))
    Await ($dr.LoadAsync([uint32]$size)) ([uint32]) | Out-Null
    $bytes = New-Object byte[] $size
    $dr.ReadBytes($bytes)
    $dest = Join-Path $outFull ("page-{0:d3}.png" -f $p)
    [System.IO.File]::WriteAllBytes($dest, $bytes)
    Write-Output "wrote $dest ($size bytes)"

}
