# Scheduled Tasks Setup Guide

This guide explains how to set up automated scheduled tasks for the RE2 application to keep lease statuses and other data up-to-date.

## Available Tasks

### 1. Update Lease Statuses
Automatically updates lease statuses based on dates:
- `pending` → `active` (when start date arrives)
- `active` → `expiring` (when within 30 days of end date)
- `expiring` → `expired` (when end date passes)

### 2. Check Lease Expirations
Sends notifications for leases expiring in 90, 60, 30, 14, and 7 days.

### 3. Cleanup Old Leases
Archives or reports on very old expired leases (default: 365+ days old).

---

## Manual Execution

You can run tasks manually for testing or one-time operations:

```bash
# Make the script executable (first time only)
chmod +x manage_tasks.py

# Update all lease statuses
python manage_tasks.py update_leases

# Update specific company only
python manage_tasks.py update_leases --company=5

# Check for expiring leases
python manage_tasks.py check_expirations

# Clean up old leases
python manage_tasks.py cleanup_old_leases

# Run all tasks
python manage_tasks.py run_all
```

---

## Automated Scheduling

### Option 1: Cron (Linux/Mac)

1. **Edit your crontab:**
   ```bash
   crontab -e
   ```

2. **Add daily task (runs at 2:00 AM):**
   ```cron
   # RE2 Lease Status Updates - Daily at 2:00 AM
   0 2 * * * cd /path/to/re2 && /path/to/re2/reenv312/bin/python manage_tasks.py run_all >> /var/log/re2_tasks.log 2>&1
   ```

3. **Alternative: More frequent status updates (every 6 hours):**
   ```cron
   # RE2 Lease Status Updates - Every 6 hours
   0 */6 * * * cd /path/to/re2 && /path/to/re2/reenv312/bin/python manage_tasks.py update_leases >> /var/log/re2_tasks.log 2>&1

   # RE2 Expiration Notifications - Daily at 8:00 AM
   0 8 * * * cd /path/to/re2 && /path/to/re2/reenv312/bin/python manage_tasks.py check_expirations >> /var/log/re2_notifications.log 2>&1
   ```

4. **Verify cron job:**
   ```bash
   crontab -l
   ```

### Option 2: APScheduler (In-Application Scheduler)

1. **Install APScheduler:**
   ```bash
   pip install apscheduler
   ```

2. **Update `requirements.txt`:**
   ```
   APScheduler==3.10.4
   ```

3. **Add to `website/__init__.py`:**
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler
   from website.tasks.lease_tasks import update_lease_statuses_all_companies

   def create_app():
       # ... existing code ...

       # Initialize scheduler
       scheduler = BackgroundScheduler()

       # Schedule daily lease status updates at 2:00 AM
       scheduler.add_job(
           func=update_lease_statuses_all_companies,
           trigger='cron',
           hour=2,
           minute=0,
           id='update_lease_statuses'
       )

       # Start scheduler
       scheduler.start()

       # Shut down scheduler when app closes
       import atexit
       atexit.register(lambda: scheduler.shutdown())

       return app
   ```

### Option 3: systemd Timer (Linux)

1. **Create service file:**
   ```bash
   sudo nano /etc/systemd/system/re2-lease-update.service
   ```

   ```ini
   [Unit]
   Description=RE2 Lease Status Update Task

   [Service]
   Type=oneshot
   User=your-username
   WorkingDirectory=/path/to/re2
   Environment="PATH=/path/to/re2/reenv312/bin"
   ExecStart=/path/to/re2/reenv312/bin/python manage_tasks.py run_all

   [Install]
   WantedBy=multi-user.target
   ```

2. **Create timer file:**
   ```bash
   sudo nano /etc/systemd/system/re2-lease-update.timer
   ```

   ```ini
   [Unit]
   Description=Run RE2 lease updates daily

   [Timer]
   OnCalendar=daily
   OnCalendar=02:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. **Enable and start timer:**
   ```bash
   sudo systemctl enable re2-lease-update.timer
   sudo systemctl start re2-lease-update.timer
   sudo systemctl status re2-lease-update.timer
   ```

### Option 4: Windows Task Scheduler

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: "RE2 Lease Status Update"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
   - Program: `C:\path\to\re2\reenv312\Scripts\python.exe`
   - Arguments: `manage_tasks.py run_all`
   - Start in: `C:\path\to\re2`
6. Finish and test

---

## Task Schedules (Recommended)

### Production Environment
- **Lease Status Updates**: Daily at 2:00 AM
- **Expiration Notifications**: Daily at 8:00 AM
- **Old Lease Cleanup**: Weekly on Sundays at 3:00 AM

### Development Environment
- **Lease Status Updates**: Every 6 hours (for testing)
- **Expiration Notifications**: Daily at 9:00 AM
- **Old Lease Cleanup**: Disabled (run manually when needed)

---

## Monitoring and Logs

### Log Files
Tasks output to stdout/stderr. Redirect to log files:

```bash
python manage_tasks.py run_all >> /var/log/re2_tasks.log 2>&1
```

### Log Rotation
Set up logrotate for task logs:

```bash
sudo nano /etc/logrotate.d/re2-tasks
```

```
/var/log/re2_tasks.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 your-username your-username
}
```

### Monitoring Task Execution

Create a simple monitoring script:

```bash
#!/bin/bash
# check_re2_tasks.sh

LOGFILE="/var/log/re2_tasks.log"
HOURS=25  # Check last 25 hours (daily task should have run)

if [ ! -f "$LOGFILE" ]; then
    echo "ERROR: Log file not found!"
    exit 1
fi

LAST_RUN=$(find "$LOGFILE" -mmin -$(($HOURS * 60)) -print)

if [ -z "$LAST_RUN" ]; then
    echo "WARNING: RE2 tasks haven't run in $HOURS hours!"
    # Send alert email or notification here
    exit 1
else
    echo "OK: RE2 tasks running normally"
    exit 0
fi
```

---

## Troubleshooting

### Task Not Running
1. Check cron is running: `systemctl status cron`
2. Check cron logs: `grep CRON /var/log/syslog`
3. Verify paths in crontab
4. Check Python virtual environment is activated

### Permission Issues
```bash
# Make sure log directory is writable
sudo mkdir -p /var/log
sudo touch /var/log/re2_tasks.log
sudo chown your-username:your-username /var/log/re2_tasks.log
```

### Database Lock Issues
If tasks run while app is in use:
- Use SQLite WAL mode (Write-Ahead Logging)
- Consider PostgreSQL for production
- Add retry logic to tasks

### Python Path Issues
Always use absolute paths in cron:
```cron
0 2 * * * /full/path/to/python /full/path/to/manage_tasks.py run_all
```

---

## Testing

### Test Task Execution
```bash
# Run with verbose output
python manage_tasks.py update_leases

# Check results
python -c "from website import create_app; from website.models import Lease; app = create_app(); app.app_context().push(); print('Total leases:', Lease.query.count())"
```

### Dry Run Mode (Future Enhancement)
Consider adding a `--dry-run` flag to preview changes without committing.

---

## Security Considerations

1. **Restrict log file access:**
   ```bash
   chmod 640 /var/log/re2_tasks.log
   ```

2. **Use service accounts** for production cron jobs (not root)

3. **Limit task execution time** to prevent resource exhaustion

4. **Add database backup** before cleanup tasks

---

## Next Steps

After setting up scheduled tasks:

1. ✅ Monitor logs for first 7 days
2. ✅ Verify lease statuses update correctly
3. ✅ Test notification delivery (when implemented)
4. ✅ Set up alerts for task failures
5. ✅ Document any company-specific schedule requirements
