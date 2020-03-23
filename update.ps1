$funcName = "coin_price_to"
if( Test-Path $funcName".zip" ){
    Remove-Item $funcName".zip"
}
Compress-Archive lambda_function.py, info.json -DestinationPath $funcName".zip"
aws lambda update-function-code --function-name $funcName --zip-file fileb://$funcName.zip
