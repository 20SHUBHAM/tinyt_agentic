# Deployment Guide

## 🚀 Replit Deployment (Recommended)

### Step 1: Import to Replit

1. **Create New Repl**:
   - Go to [Replit](https://replit.com)
   - Click "Create Repl"
   - Choose "Import from GitHub"
   - Paste your repository URL
   - Click "Import from GitHub"

2. **Configure Repl**:
   - Replit will automatically detect the Python project
   - The `.replit` file will configure the build and run commands
   - Dependencies will be installed automatically

### Step 2: Environment Setup

1. **Create Environment File**:
   - In the Replit editor, create a `.env` file
   - Copy contents from `.env.example`
   - Add your configuration (OpenAI API key is optional)

2. **Install Dependencies**:
   - Replit will automatically run `pip install -r requirements.txt`
   - If not, you can run it manually in the Shell tab

### Step 3: Run the Application

1. **Start the Server**:
   - Click the green "Run" button
   - Or use the Shell: `python main.py`

2. **Access Your App**:
   - Replit will provide a URL (usually `https://your-repl-name.your-username.repl.co`)
   - The app will be available at this URL

### Step 4: Configure for Production

1. **Set Environment Variables**:
   ```bash
   # In the .env file
   DEBUG=False
   SECRET_KEY=your_production_secret_key
   ```

2. **Enable Always On** (Replit Hacker Plan):
   - Go to your Repl settings
   - Enable "Always On" to keep your app running 24/7

## 🐳 Docker Deployment

### Local Docker

1. **Build Image**:
   ```bash
   docker build -t agentic-focus-group .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 -e DEBUG=False agentic-focus-group
   ```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your_secret_key
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## ☁️ Cloud Deployment

### Railway

1. **Connect Repository**:
   - Go to [Railway](https://railway.app)
   - Create new project from GitHub
   - Select your repository

2. **Configure**:
   - Railway will auto-detect the Dockerfile
   - Set environment variables in the dashboard
   - Deploy automatically

### Render

1. **Create Web Service**:
   - Go to [Render](https://render.com)
   - Connect your GitHub repository
   - Choose "Web Service"

2. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Set environment variables

### Heroku

1. **Create App**:
   ```bash
   heroku create your-app-name
   ```

2. **Add Procfile**:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Deploy**:
   ```bash
   git push heroku main
   ```

## 🖥️ VPS/Server Deployment

### Using Nginx + Gunicorn

1. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **Setup Application**:
   ```bash
   git clone your-repo
   cd agentic-focus-group
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

3. **Create Systemd Service**:
   ```ini
   # /etc/systemd/system/focus-group.service
   [Unit]
   Description=Agentic Focus Group System
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/agentic-focus-group
   Environment="PATH=/path/to/agentic-focus-group/venv/bin"
   ExecStart=/path/to/agentic-focus-group/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind unix:focus-group.sock
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx**:
   ```nginx
   # /etc/nginx/sites-available/focus-group
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/path/to/agentic-focus-group/focus-group.sock;
       }

       location /static/ {
           alias /path/to/agentic-focus-group/static/;
       }
   }
   ```

5. **Enable and Start**:
   ```bash
   sudo systemctl enable focus-group
   sudo systemctl start focus-group
   sudo ln -s /etc/nginx/sites-available/focus-group /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

## 🔒 Production Checklist

### Security
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Regular security updates

### Performance
- [ ] Use production WSGI server (Gunicorn/uWSGI)
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up caching if needed
- [ ] Monitor resource usage

### Monitoring
- [ ] Set up logging
- [ ] Configure health checks
- [ ] Monitor application metrics
- [ ] Set up alerts

### Backup
- [ ] Backup session data regularly
- [ ] Version control deployment scripts
- [ ] Document recovery procedures

## 🔧 Environment Variables

```bash
# Required
SECRET_KEY=your_secret_key_here

# Optional
OPENAI_API_KEY=your_openai_key
DEBUG=False
LOG_LEVEL=INFO
SESSION_TIMEOUT=3600
DATABASE_URL=sqlite:///./focus_group.db
```

## 📊 Scaling Considerations

### Horizontal Scaling
- Use load balancer (Nginx, HAProxy)
- Shared session storage (Redis, database)
- Container orchestration (Kubernetes, Docker Swarm)

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Use caching strategies

### Database Scaling
- Move from SQLite to PostgreSQL/MySQL
- Implement connection pooling
- Consider read replicas

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Permission Denied**:
   ```bash
   # Fix file permissions
   chmod +x run.sh
   chown -R www-data:www-data /path/to/app
   ```

3. **Module Not Found**:
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Static Files Not Loading**:
   - Check Nginx configuration
   - Verify file paths
   - Check file permissions

### Logs and Debugging

1. **Application Logs**:
   ```bash
   # Check systemd logs
   journalctl -u focus-group -f
   
   # Check Nginx logs
   tail -f /var/log/nginx/error.log
   ```

2. **Debug Mode**:
   - Set `DEBUG=True` in development
   - Check browser developer console
   - Use application health check endpoint

## 📞 Support

For deployment issues:
1. Check the logs first
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Test with the health check endpoint (`/health`)
5. Create an issue with detailed error information

---

**Happy Deploying! 🚀**