# Page Analyzer 🔍

## Hexlet test and linter status
[![Hexlet tests](https://github.com/VVP04/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/VVP04/python-project-83/actions)

## CI Status
[![Python CI](https://github.com/VVP04/python-project-83/actions/workflows/main.yml/badge.svg)](https://github.com/VVP04/python-project-83/actions/workflows/main.yml)

## Deployment Status
[![Render](https://img.shields.io/badge/Render-Deployed-brightgreen)](https://python-project-83-zlel.onrender.com)

## Project Description 📝

Page Analyzer is a web application that checks websites for SEO readiness. The project provides comprehensive analysis of web pages including URL validation, SEO metrics checking, and detailed reporting.

## Key Features ✨
- Robust URL validation and normalization
- Comprehensive SEO metrics checking
- HTTP response code verification
- Detailed analysis reports
- Full history of all performed checks
- Clean responsive interface with Bootstrap 5

## Technology Stack 🛠️
- **Backend**: Python, Flask
- **Frontend**: HTML, Bootstrap 5
- **Database**: PostgreSQL
- **Production Server**: Gunicorn
- **CI/CD**: GitHub Actions
- **Hosting**: Render

## Deployment 🚀
The application is deployed at: https://python-project-83-zlel.onrender.com

## ⚙️ Installation and Setup
1. Clone the repository:
```bash
git clone https://github.com/VVP04/python-project-83.git
cd python-project-83
```
2. Create `.env` file:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
SECRET_KEY=your_secret_key_here
```
3. Install dependencies:
```bash
make build
```
4. Start application in production mode:
```bash
make start
```
5. For development with hot reload:
```bash
make dev
```
> Uses `uvicorn flask --debug --app page_analyzer:app run` for development server with auto-reload

> **Note:** Requires PostgreSQL and DATABASE_URL environment variable

## Linting 🧹
```bash
make lint
```

## How to Use 🕹️
1. Enter website URL
2. Get SEO analysis
3. View detailed report
4. Check analysis history