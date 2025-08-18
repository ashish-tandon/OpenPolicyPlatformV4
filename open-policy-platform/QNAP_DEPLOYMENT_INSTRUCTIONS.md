# 🚀 Open Policy Platform V4 - QNAP Deployment Instructions

## 📋 Prerequisites
1. QNAP NAS with Container Station installed
2. SSH access enabled on QNAP
3. SSH key added to QNAP (see key above)

## 🔑 SSH Key Setup
Add this SSH key to your QNAP:
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCz8gIQSUI0sosZ4HSg4Nwfoz1TAK5ECKQ93bsVPUe+m7IGGseLCqMWmlUhxnUEaC1J37RuoWIRiDhRaEkY3lAyblz1uk+k402vfbwFf+Ge7FH48nS57S4iumf3k8U0MtjiiUcYMVGeGmpSyF0MyzBHeyQIGCzFKvQ0KVzhDjyLK9Qq+UUAGMwjyvsZa4G1ZPZLANNFJI37tgztst815N1BuSzX9zhH9v/EvZfEJfXwyBvnFzcEfA9GXi/V2l+gIHR3ONngW2xqdBQwJj+/DK9gGT5CWtXQabCT6uILBhlxDudJZPjTdB2S9NnYfc81Jo/FPKP2eJbaFnkXmqtEV7nnP0T9dd1ER0aMZCsEhrPail8IiiQmibpWDcRmRYn2LM1GklLbel0X1n6HwY5Li1u56KsJ1pDY6fpJdGmb9c6AZDCRrP0fcUfxhLgXuYcuFhfgjO5Amb/sjNJ/q/wzm630DnXvUIYWJCk1gZ9O1z5zB23jOxFAYVEkfmT0Q3gHCivbc1IY7z0/abUiCGPhKjl0vcBwxNFwYqi+E3Cj7O4bAdkcRbMxJGJJkg1hBt3SCve4OBDIG0AlolbjHoaXUTut5DHvgo1VrrmDIc8Kiimvu96HAbsDxv0Wxt9hIluPD/zZwJaIQ6vNim8N9lleqeG6PHDB0lHok1+fujhzaMRPeQ== ashish.tandon@openpolicy.me
```

**Steps:**
1. Go to QNAP Control Panel > Network & File Services > SSH
2. Enable SSH service
3. Add the public key above to authorized keys

## 📁 Files to Copy to QNAP
Copy these files to your QNAP NAS:
- `docker-compose.qnap.yml`
- `.env.qnap`
- `qnap-config.json`
- `scripts/import-database-qnap.sh`
- `database-exports/full_database_*.sql`

## 🐳 Deployment Steps

### 1. Connect to QNAP
```bash
ssh admin@192.168.2.152
```

### 2. Create Platform Directory
```bash
mkdir -p /share/Container/OpenPolicyPlatform
cd /share/Container/OpenPolicyPlatform
```

### 3. Copy Files
Copy all deployment files to this directory

### 4. Start Platform
```bash
docker-compose -f docker-compose.qnap.yml up -d
```

### 5. Import Database
```bash
chmod +x scripts/import-database-qnap.sh
./scripts/import-database-qnap.sh database-exports/full_database_*.sql
```

## 🌐 Access URLs
- **Web Interface**: http://192.168.2.152:3000
- **API**: http://192.168.2.152:8000
- **Grafana**: http://192.168.2.152:3001
- **Prometheus**: http://192.168.2.152:9090

## 🔍 Verification
```bash
# Check service status
docker-compose -f docker-compose.qnap.yml ps

# Check logs
docker-compose -f docker-compose.qnap.yml logs -f
```

## 🆘 Troubleshooting
- Check Container Station is running
- Verify SSH key is properly added
- Check firewall settings
- Monitor system resources
