# Avocato Legal Assistant

## Azure Deployment Information
- App Name: avocato-fvhmgsdxgtcbdxhz
- Resource Group: assitants
- Location: Germany West Central
- App Service Plan: ASP-assitants-9053 (B1: 1)
- Operating System: Linux
- Domain: avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net
- GitHub Project: https://github.com/gunnit/avocato

## Local Development Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the template:
```bash
cp .env.example .env
```

4. Update the `.env` file with your local development settings:
- Set `DEBUG=True`
- Set `DJANGO_SETTINGS_MODULE=legal_assistant.settings.local`
- Add your API keys for Anthropic, OpenAI, and Serper

5. Run migrations:
```bash
python manage.py migrate
```

6. Run the development server:
```bash
python manage.py runserver
```

## Azure Deployment with GitHub Actions

### Required GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets):

```
AZURE_CREDENTIALS          # Azure service principal credentials
AZURE_WEBAPP_PUBLISH_PROFILE  # Azure Web App publish profile
SECRET_KEY                 # Django secret key
DB_NAME                    # PostgreSQL database name
DB_USER                    # Database username
DB_PASSWORD               # Database password
DB_HOST                   # Database host
AZURE_STORAGE_ACCOUNT_NAME # Storage account name
AZURE_STORAGE_ACCOUNT_KEY  # Storage account key
ANTHROPIC_API_KEY         # Anthropic API key
OPENAI_API_KEY            # OpenAI API key
SERPER_API_KEY            # Serper API key
```

### Deployment Process

1. The GitHub Actions workflow is configured to:
   - Trigger on pushes to main branch
   - Deploy to Germany West Central region
   - Use Linux B1 App Service Plan
   - Handle static files and database migrations

2. Deployment Steps:
   ```bash
   # One-time setup in Azure Portal:
   1. Create PostgreSQL database
   2. Create Storage Account for media files
   3. Configure Web App environment variables
   ```

3. After setting up secrets, push to main branch:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

### Environment Variables in Azure

Configure these in Azure Web App > Configuration > Application settings:

```
DJANGO_SETTINGS_MODULE=legal_assistant.settings.production
DEBUG=False
ALLOWED_HOSTS=avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net
DB_NAME=<your-db-name>
DB_USER=<your-db-user>
DB_PASSWORD=<your-db-password>
DB_HOST=<your-db-host>
DB_PORT=5432
AZURE_STORAGE_ACCOUNT_NAME=<your-storage-account>
AZURE_STORAGE_ACCOUNT_KEY=<your-storage-key>
AZURE_STORAGE_CONTAINER_NAME=media
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
SERPER_API_KEY=<your-key>
```

### Project Structure

```
legal_assistant/
├── legal_assistant/
│   ├── settings/
│   │   ├── base.py      # Base settings
│   │   ├── local.py     # Local development settings
│   │   └── production.py # Azure production settings
│   ├── urls.py
│   └── wsgi.py
├── cases/              # Main app
├── legal_rag/          # RAG system app
├── .github/
│   └── workflows/
│       └── azure-deploy.yml  # GitHub Actions workflow
├── manage.py
├── requirements.txt
├── .env.example
└── .gitignore
```

### Monitoring

1. GitHub Actions:
   - Check workflow runs at: https://github.com/gunnit/avocato/actions

2. Azure Portal:
   - App Service logs
   - Application Insights (if enabled)
   - Resource metrics

3. Database:
   - Azure Database for PostgreSQL metrics
   - Query performance insights

4. Storage:
   - Azure Storage Account metrics
   - Blob storage monitoring
