# Quick Reference - API Migration Evaluation Framework

## 🚀 Execute Everything (One Command)

```powershell
.\run_all.sh
```

**What it does:**
1. Sets up both projects
2. Runs all tests (Project A + Project B)
3. Generates comparison report
4. Shows summary

**Time:** ~15-30 seconds

---

## 📊 View Results

### Comparison Report
```powershell
Get-Content compare_report.md
```

### JSON Metrics
```powershell
# Pre-change results
Get-Content results\results_pre.json | ConvertFrom-Json

# Post-change results
Get-Content results\results_post.json | ConvertFrom-Json

# Aggregated metrics
Get-Content results\aggregated_metrics.json | ConvertFrom-Json
```

### Logs
```powershell
Get-Content Project_A_PreChange\logs\log_pre.txt
Get-Content Project_B_PostChange\logs\log_post.txt
```

---

## 🔧 Individual Project Testing

### Project A (Legacy v1)
```powershell
cd Project_A_PreChange
.\setup.sh           # First time only
.\run_tests.sh       # Run tests
cd ..
```

### Project B (New v2)
```powershell
cd Project_B_PostChange
.\setup.sh           # First time only
.\run_tests.sh       # Run tests
cd ..
```

---

## 📝 Test Cases

| ID | Name | What It Tests |
|----|------|---------------|
| TC001 | Normal case | Basic v2 integration with confirmed availability |
| TC002 | Boundary case | Zero quantity (out of stock) |
| TC003 | Async case | Pending status requiring polling |
| TC004 | Invalid input | Missing regionId (validation + fallback) |
| TC005 | Error case | Service timeout/500 (retry + fallback) |
| TC006 | Boundary case | Stock at reserve threshold |

---

## 🎯 Key Metrics

### What to Look For
- **Pass Rate:** Should be ≥90% for production readiness
- **Latency Delta:** Should be <20% increase
- **Fallback Rate:** Should be <10% in tests
- **Error Rate:** Should be 0% for non-error test cases

### Success Indicators
- ✅ All normal cases pass (TC001, TC006)
- ✅ Async handling works (TC003)
- ✅ Validation catches errors (TC004)
- ✅ Fallback activates on failures (TC005)
- ✅ Latency increase <20%

---

## 🐛 Troubleshooting

### Mock Servers Won't Start
```powershell
# Check if ports are in use
netstat -ano | findstr "5001"
netstat -ano | findstr "5002"

# Kill process if needed
Stop-Process -Id <PID> -Force
```

### Virtual Environment Issues
```powershell
# Delete and recreate
Remove-Item -Recurse -Force Project_A_PreChange\venv
cd Project_A_PreChange
.\setup.sh
```

### Test Failures
```powershell
# Run with verbose output
cd Project_A_PreChange
& .\venv\Scripts\Activate.ps1
python tests\test_pre_change.py -v
```

### Import Errors
```powershell
# Reinstall dependencies
cd Project_A_PreChange
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt --force-reinstall
```

---

## 📁 File Locations

### Source Code
- `Project_A_PreChange/src/cart_service_v1.py` - Legacy service
- `Project_B_PostChange/src/cart_service_v2.py` - New service
- `Project_B_PostChange/src/adapter.py` - Compatibility layer

### Mock Servers
- `Project_A_PreChange/mocks/mock_api_v1.py` - v1 API (port 5001)
- `Project_B_PostChange/mocks/mock_api_v2.py` - v2 API (port 5002)

### Tests
- `Project_A_PreChange/tests/test_pre_change.py` - v1 test suite
- `Project_B_PostChange/tests/test_post_change.py` - v2 test suite

### Configuration
- `test_data.json` - Test case definitions (6 scenarios)
- `requirements.txt` - Python dependencies (Flask, requests)

### Results (Generated)
- `results/results_pre.json` - Project A metrics
- `results/results_post.json` - Project B metrics
- `results/aggregated_metrics.json` - Comparison
- `compare_report.md` - Human-readable report

---

## 🔍 Manual Testing

### Test v1 API Directly
```powershell
# Start server
cd Project_A_PreChange
& .\venv\Scripts\Activate.ps1
python mocks\mock_api_v1.py

# In another terminal
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/v1/checkStock" `
  -ContentType "application/json" `
  -Body '{"sku":"ABC123"}'
```

### Test v2 API Directly
```powershell
# Start server
cd Project_B_PostChange
& .\venv\Scripts\Activate.ps1
python mocks\mock_api_v2.py

# In another terminal
Invoke-RestMethod -Method Post -Uri "http://localhost:5002/api/v2/stock/availability" `
  -ContentType "application/json" `
  -Body '{"sku":"ABC123","regionId":"ap-sg-1","warehouseGroup":"WG-2"}'
```

---

## 🎨 Customization

### Add a Test Case
1. Edit `test_data.json`
2. Add new test case with all required fields
3. Update mock servers to handle new SKU
4. Re-run tests

### Adjust Timeouts
Edit service constructors:
```python
# In cart_service_v1.py or cart_service_v2.py
self.timeout = 10  # Change from 5 to 10 seconds
```

### Change Circuit Breaker Thresholds
Edit adapter.py:
```python
self.circuit_breaker = CircuitBreaker(
    failure_threshold=5,    # Change from 3
    timeout_seconds=120     # Change from 60
)
```

### Modify Report Format
Edit the Python report generation code in `run_all.sh` (search for "Generate markdown report")

---

## 📚 Documentation

- **README.md** - Overview and quick start
- **IMPLEMENTATION_GUIDE.md** - Technical deep dive
- **PROJECT_SUMMARY.md** - Complete deliverables checklist
- **compare_report.md** - Generated comparison (after run_all.sh)

---

## 💡 Tips

### Fast Iteration
```powershell
# Run only one project
cd Project_B_PostChange
.\run_tests.sh
```

### Clean Slate
```powershell
# Remove all generated files
Remove-Item -Recurse -Force Project_A_PreChange\venv, Project_A_PreChange\logs, Project_A_PreChange\results
Remove-Item -Recurse -Force Project_B_PostChange\venv, Project_B_PostChange\logs, Project_B_PostChange\results
Remove-Item -Recurse -Force results
```

### Parallel Execution (Advanced)
```powershell
# Run both projects in parallel (careful with port conflicts)
$jobA = Start-Job { cd Project_A_PreChange; .\run_tests.sh }
$jobB = Start-Job { cd Project_B_PostChange; .\run_tests.sh }
Wait-Job $jobA, $jobB
Receive-Job $jobA, $jobB
```

---

## 🏆 Success Checklist

After running `.\run_all.sh`, verify:

- [ ] `results/results_pre.json` exists
- [ ] `results/results_post.json` exists
- [ ] `results/aggregated_metrics.json` exists
- [ ] `compare_report.md` generated
- [ ] No error messages in console
- [ ] Pass rate ≥90% in both projects
- [ ] Latency delta <20%

---

## 🆘 Need Help?

### Check Logs First
```powershell
Get-Content Project_A_PreChange\logs\log_pre.txt -Tail 50
Get-Content Project_B_PostChange\logs\log_post.txt -Tail 50
```

### Validate JSON
```powershell
# Check if JSON is valid
Get-Content results\results_pre.json | ConvertFrom-Json
```

### Test Python Environment
```powershell
cd Project_A_PreChange
& .\venv\Scripts\Activate.ps1
python --version          # Should be 3.8+
pip list                  # Should show Flask, requests
```

---

*Quick reference for API Migration Evaluation Framework*
