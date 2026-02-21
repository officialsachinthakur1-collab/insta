# Run this script to package your Chrome profiles for GitHub Actions
Write-Host "Zipping Chrome Profiles for GitHub Actions..." -ForegroundColor Cyan

$zipFile = "chrome_profiles_for_github.zip"
if (Test-Path $zipFile) { Remove-Item $zipFile }

# Compress the profiles
Compress-Archive -Path "chrome_profile", "chrome_profile_ig" -DestinationPath $zipFile -Force

Write-Host "Success! Created: $zipFile" -ForegroundColor Green
Write-Host "Next Step: Convert this ZIP to Base64 to upload as a GitHub Secret." -ForegroundColor Yellow
Write-Host "Run this command to get the Base64 string in a text file:"
Write-Host "[Convert]::ToBase64String([IO.File]::ReadAllBytes('chrome_profiles_for_github.zip')) | Out-File profile_base64.txt" -ForegroundColor Magenta
