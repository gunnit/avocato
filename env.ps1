# Load the .env file
$envFile = ".env"

# Read each line in the .env file and set it as an environment variable
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        $name = $matches[1]
        $value = $matches[2]
        [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
    }
}

# Output a message to indicate that the environment variables are set
Write-Output "Environment variables set successfully."
