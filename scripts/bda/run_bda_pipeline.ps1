<#
.SYNOPSIS
    ProductPulse — End-to-End Big Data Analytics Pipeline Orchestrator
.DESCRIPTION
    Automates the execution of:
    1. Single-node HDFS initialization & data ingestion
    2. Genuine Hadoop Streaming MapReduce job for aspect aggregation
    3. Output validation against raw corpus
    4. Apache Hive analytics queries over MapReduce output
    5. Export of analytical CSV summaries to data/bda/
#>

[CmdletBinding()]
param(
    [switch]$SkipHadoop = $false,
    [switch]$SkipHive = $false
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $WorkspaceRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "ProductPulse: Big Data Analytics Pipeline (Hadoop + Hive)" -ForegroundColor Cyan
Write-Host "Workspace: $WorkspaceRoot" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Pre-flight Checks
$RawCorpus = Join-Path $WorkspaceRoot "data\raw\sample_reviews_cell_phones_25k.jsonl"
if (-not (Test-Path $RawCorpus)) {
    Write-Error "Source corpus missing at $RawCorpus"
}
Write-Host "[OK] Raw corpus verified: $RawCorpus" -ForegroundColor Green

# Verify Docker
$DockerVersion = docker --version
Write-Host "[OK] Docker available: $DockerVersion" -ForegroundColor Green

# Verify unrelated PostgreSQL container is safe
$ExistingPostgres = docker ps --filter "name=yogyatamitra_postgres" --format "{{.Names}} ({{.Status}})"
if ($ExistingPostgres) {
    Write-Host "[SAFE] Unrelated database preserved: $ExistingPostgres" -ForegroundColor Green
}

# 2. Hadoop MapReduce Execution
if (-not $SkipHadoop) {
    Write-Host "`n--- Step 1: Executing Genuine Hadoop Streaming MapReduce Job ---" -ForegroundColor Yellow
    docker run --rm --name productpulse_hadoop `
        -v "${WorkspaceRoot}:/app" `
        apache/hadoop:3.3.6 `
        bash /app/scripts/bda/run_hadoop_job.sh

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Hadoop MapReduce execution failed with exit code $LASTEXITCODE"
    }
    Write-Host "[OK] Hadoop Streaming job completed successfully." -ForegroundColor Green

    # Validate output
    Write-Host "`n--- Step 2: Validating MapReduce Output ---" -ForegroundColor Yellow
    python scripts/bda/verify_hadoop_output.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Hadoop output validation failed!"
    }
}

# 3. Hive Analytics Execution
if (-not $SkipHive) {
    Write-Host "`n--- Step 3: Executing Apache Hive Analytics Queries ---" -ForegroundColor Yellow
    $HiveImage = docker images productpulse-hive:3.1.3 --format "{{.Repository}}:{{.Tag}}"
    if (-not $HiveImage) {
        Write-Host "Building productpulse-hive:3.1.3 image..." -ForegroundColor Cyan
        docker build -t productpulse-hive:3.1.3 -f scripts/bda/Dockerfile.hive scripts/bda
    }
    
    Write-Host "Starting ProductPulse Hive container..." -ForegroundColor Cyan
    docker run --rm --name productpulse_hive `
        -v "${WorkspaceRoot}:/app" `
        productpulse-hive:3.1.3 `
        bash /app/scripts/bda/run_hive_pipeline.sh

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Hive analytics pipeline failed with exit code $LASTEXITCODE"
    }
    Write-Host "[OK] Hive analytics pipeline completed successfully." -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "ProductPulse BDA Pipeline Execution Completed." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
