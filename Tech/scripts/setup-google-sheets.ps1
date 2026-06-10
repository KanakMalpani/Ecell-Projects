# Opens the Google Sheet + Apps Script setup flow for GNN Logistics form automation.
$sheetUrl = "https://docs.google.com/spreadsheets/create"
$scriptGuide = "https://script.google.com/home/start"

Write-Host "GNN Logistics - Google Sheets setup"
Write-Host "1. Create a sheet (opening browser)..."
Start-Process $sheetUrl

Write-Host "2. Copy the spreadsheet ID from the URL:"
Write-Host "   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
Write-Host "3. Open Apps Script (opening browser)..."
Start-Process $scriptGuide

Write-Host "4. Paste Code.gs from Tech/google-apps-script/Code.gs"
Write-Host "5. Set SPREADSHEET_ID and run setupSheet() once"
Write-Host "6. Deploy -> New deployment -> Web app -> Anyone"
Write-Host "7. Add deployment URL to Vercel as GOOGLE_SCRIPT_URL"
